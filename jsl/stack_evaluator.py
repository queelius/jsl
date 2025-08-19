"""
Stack-based evaluator for postfix expressions.

This evaluator processes postfix notation using a simple value stack.
It's much simpler than recursive evaluation and enables:
1. Easy resumption (just save/restore the stack)
2. Clear resource tracking (each operation is atomic)
3. No call stack depth issues
4. Potential for optimization
"""

from typing import List, Any, Optional, Dict, Callable
from dataclasses import dataclass
from .resources import ResourceBudget, ResourceExhausted, GasCost
from .stack_special_forms import SpecialFormEvaluator, Opcode, detect_special_form
from .core import Env, Closure
from .serialization import to_json, from_json


@dataclass
class StackState:
    """State of the stack evaluator, can be serialized for resumption."""
    stack: List[Any]
    pc: int  # Program counter (position in postfix instructions)
    instructions: List[Any]
    resource_checkpoint: Optional[Dict[str, Any]] = None  # Resource state for resumption
    env: Optional[Env] = None  # The environment (user-defined bindings extend prelude)
    
    def to_dict(self) -> Dict:
        """Convert to serializable dictionary."""
        return {
            'stack': to_json(self.stack),
            'pc': self.pc,
            'instructions': self.instructions,
            'resource_checkpoint': self.resource_checkpoint,
            'env': to_json(self.env) if self.env else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict, prelude_env: Optional[Env] = None) -> 'StackState':
        """Restore from dictionary."""
        return cls(
            stack=from_json(data['stack'], prelude_env),
            pc=data['pc'],
            instructions=data['instructions'],
            resource_checkpoint=data.get('resource_checkpoint'),
            env=from_json(data['env'], prelude_env) if data.get('env') else prelude_env
        )


class StackEvaluator:
    """Evaluator for postfix expressions using a value stack."""
    
    def __init__(self, env: Optional[Env] = None, resource_budget: Optional[ResourceBudget] = None, host_dispatcher=None):
        """
        Initialize evaluator with optional environment and resource budget.
        
        Args:
            env: Environment for variable lookups (Env object)
            resource_budget: Optional resource budget for tracking gas/memory
            host_dispatcher: Optional host dispatcher for side effects
        """
        self.env = env or Env()
        self.resource_budget = resource_budget
        self.host_dispatcher = host_dispatcher
        self.builtins = self._setup_builtins()
        self.special_forms = SpecialFormEvaluator(self)
    
    def _consume_gas(self, cost: int, operation: str = ""):
        """Consume gas if resource budget is available."""
        if self.resource_budget:
            self.resource_budget.consume_gas(cost, operation)
    
    def _check_resources(self):
        """Check time and other resources if budget is available."""
        if self.resource_budget:
            self.resource_budget.check_time()
    
    def _track_memory_for_stack(self, stack_size: int):
        """Track memory usage for stack size."""
        if self.resource_budget:
            # Estimate 8 bytes per stack element
            stack_memory = stack_size * 8
            # Only track if we haven't tracked this much before
            current_memory = getattr(self, '_last_tracked_memory', 0)
            if stack_memory > current_memory:
                self.resource_budget.allocate_memory(
                    stack_memory - current_memory, 
                    f"stack size {stack_size}"
                )
                self._last_tracked_memory = stack_memory
    
    def _product(self, args: list) -> Any:
        """Compute product of arguments, with identity 1 for empty list."""
        result = 1
        for x in args:
            result *= x
        return result
    
    def _subtract(self, args: list) -> Any:
        """
        Compute subtraction with proper n-ary semantics.
        0 args: 0 (identity)
        1 arg: negation
        2 args: a - b
        n args: a - b - c - ... (left-associative)
        """
        if not args:
            return 0
        elif len(args) == 1:
            return -args[0]
        else:
            # Left-associative: (((a - b) - c) - d)
            result = args[0]
            for x in args[1:]:
                result -= x
            return result
    
    def _create_dict(self, args: list) -> dict:
        """
        Create a dictionary from stack values.
        The args list contains the number of key-value pairs.
        Stack should have been: key1, val1, key2, val2, ... (in that order)
        But with our arity system, args[0] is the number of pairs,
        and the actual pairs have already been consumed.
        """
        # For __dict__, the arity tells us the number of key-value pairs
        # But our arity system has already collected ALL values
        # So args contains all the keys and values
        
        result = {}
        # Process pairs - every 2 items form a key-value pair
        for i in range(0, len(args), 2):
            if i + 1 >= len(args):
                raise ValueError(f"__dict__ requires even number of arguments for key-value pairs")
            
            key = args[i]
            value = args[i + 1]
            
            # Key must be a string
            if not isinstance(key, str):
                raise TypeError(f"Dictionary key must be string, got {type(key).__name__}: {key}")
            
            result[key] = value
        
        return result
    
    def _setup_builtins(self) -> Dict[str, Callable]:
        """Setup built-in operators."""
        return {
            # Arithmetic (with proper identity elements)
            '+': lambda args: sum(args) if args else 0,  # Identity: 0
            '-': lambda args: self._subtract(args),
            '*': lambda args: self._product(args),  # Identity: 1
            '/': lambda args: args[0] / args[1],
            '%': lambda args: args[0] % args[1],
            
            # Comparison
            '=': lambda args: args[0] == args[1],
            '!=': lambda args: args[0] != args[1],
            '<': lambda args: args[0] < args[1],
            '>': lambda args: args[0] > args[1],
            '<=': lambda args: args[0] <= args[1],
            '>=': lambda args: args[0] >= args[1],
            
            # Logical (with proper identity elements)
            'not': lambda args: not args[0],
            'and': lambda args: all(args) if args else True,   # Identity: True (all of empty set)
            'or': lambda args: any(args) if args else False,   # Identity: False (any of empty set)
            
            # Min/max with proper identity elements
            'max': lambda args: max(args) if args else float('-inf'),  # Identity: -infinity
            'min': lambda args: min(args) if args else float('inf'),   # Identity: +infinity
            
            # List operations
            'list': lambda args: list(args),
            '__empty_list__': lambda args: [],  # Special marker for empty list
            '__dict__': self._create_dict,  # Dictionary creation from stack
            'cons': lambda args: [args[0]] + (args[1] if isinstance(args[1], list) else [args[1]]),
            'first': lambda args: args[0][0] if args[0] else None,
            'rest': lambda args: args[0][1:] if args[0] else [],
            'length': lambda args: len(args[0]),
            'append': lambda args: args[0] + [args[1]] if isinstance(args[0], list) else [args[0], args[1]],
        }
    
    def eval(self, instructions: List[Any], state: Optional[StackState] = None, env: Optional[Env] = None) -> Any:
        """
        Evaluate postfix instructions.
        
        Args:
            instructions: List of postfix instructions
            state: Optional saved state for resumption
            env: Optional environment override (Env object)
            
        Returns:
            Result of evaluation
            
        Raises:
            ValueError: On invalid instructions or stack underflow
            ResourceExhausted: When resource limits are exceeded
        """
        if state:
            # Resume from saved state
            stack = state.stack.copy()
            pc = state.pc
            instructions = state.instructions
            # Restore resource state if available
            if state.resource_checkpoint and self.resource_budget:
                self.resource_budget.restore(state.resource_checkpoint)
            # Restore environment if available
            if state.env:
                self.env = state.env
        else:
            # Start fresh
            stack = []
            pc = 0
            self._last_tracked_memory = 0  # Reset memory tracking
        
        # Use provided env or default
        old_env = None
        if env is not None:
            old_env = self.env
            self.env = env
        
        while pc < len(instructions):
            # Check resources before each operation
            self._check_resources()
            self._track_memory_for_stack(len(stack))
            
            instr = instructions[pc]
            
            # Check for special form marker
            if instr == Opcode.SPECIAL_FORM:
                # Handle special form
                pc += 1
                if pc >= len(instructions):
                    raise ValueError("Special form marker without form")
                
                special_expr = instructions[pc]
                pc += 1
                
                if isinstance(special_expr, list) and len(special_expr) > 0:
                    form = special_expr[0]
                    args = special_expr[1:]
                    
                    # Consume gas for special form
                    self._consume_gas(GasCost.FUNCTION_CALL, f"special form: {form}")
                    
                    # Evaluate special form
                    result = self.special_forms.eval_special_form(form, args, self.env)
                    
                    # Push result to stack
                    stack.append(result)
                else:
                    raise ValueError(f"Invalid special form: {special_expr}")
            
            # Check if this is an arity (number followed by operator)
            elif (isinstance(instr, int) and 
                pc + 1 < len(instructions) and 
                isinstance(instructions[pc + 1], str) and
                (instructions[pc + 1] in self.builtins or 
                 instructions[pc + 1] in self.env or
                 instructions[pc + 1] == '__apply__' or
                 instructions[pc + 1] == '__dict__' or
                 instructions[pc + 1] == '__empty_list__')):
                # This is an arity-operator pair
                arity = instr
                operator = instructions[pc + 1]
                pc += 2  # Skip both arity and operator
                
                # Check if it's a special __apply__ operator
                if operator == '__apply__':
                    # Pop arguments from stack
                    if len(stack) < arity + 1:  # +1 for the function itself
                        raise ValueError(f"Stack underflow: apply needs function + {arity} args, have {len(stack)}")
                    
                    # Pop arguments
                    args = []
                    for _ in range(arity):
                        args.insert(0, stack.pop())
                    
                    # Pop function/closure
                    func = stack.pop()
                    
                    # Apply the function
                    if isinstance(func, Closure):
                        # It's a Closure - apply it
                        self._consume_gas(GasCost.FUNCTION_CALL, "closure application")
                        
                        # Check arity
                        if len(args) != len(func.params):
                            raise ValueError(f"Arity mismatch: closure expects {len(func.params)} args, got {len(args)}")
                        
                        # Create new environment extending the closure's captured environment
                        call_env = func.env.extend(dict(zip(func.params, args)))
                        
                        # Import compiler here to avoid circular dependency
                        from .compiler import compile_to_postfix
                        
                        # Compile and evaluate body in new environment
                        body_jpn = compile_to_postfix(func.body)
                        result = self.eval(body_jpn, env=call_env)
                        
                        # Check result constraints if we have a resource budget
                        if self.resource_budget:
                            self.resource_budget.check_result(result)
                        
                        stack.append(result)
                    else:
                        raise ValueError(f"Cannot apply non-closure: {type(func).__name__}")
                
                elif operator in self.builtins:
                    # Regular builtin operator
                    # Consume gas based on operation type and arity
                    if operator in ['+', '-', '*', '/', '%']:
                        base_cost = GasCost.ARITHMETIC
                    elif operator in ['=', '!=', '<', '>', '<=', '>=']:
                        base_cost = GasCost.COMPARISON
                    elif operator in ['not', 'and', 'or']:
                        base_cost = GasCost.LOGICAL
                    else:
                        # Built-in function call (list operations, etc.)
                        base_cost = GasCost.FUNCTION_CALL
                    
                    if arity == 2:
                        self._consume_gas(base_cost, f"binary {operator}")
                    else:
                        self._consume_gas(base_cost + arity, f"n-ary {operator}")
                    
                    # Pop arguments from stack
                    if len(stack) < arity:
                        raise ValueError(f"Stack underflow: {operator} needs {arity} args, have {len(stack)}")
                    
                    args = []
                    for _ in range(arity):
                        args.insert(0, stack.pop())
                    
                    # Apply operator
                    result = self.builtins[operator](args)
                    
                    # Check result constraints if we have a resource budget
                    if self.resource_budget:
                        self.resource_budget.check_result(result)
                    
                    stack.append(result)
                
                else:
                    # Not a builtin - could be a variable that's a function
                    # Pop arguments from stack
                    if len(stack) < arity:
                        raise ValueError(f"Stack underflow: {operator} needs {arity} args, have {len(stack)}")
                    
                    args = []
                    for _ in range(arity):
                        args.insert(0, stack.pop())
                    
                    # Look up the function
                    if operator in self.env:
                        func = self.env.get(operator)
                        if isinstance(func, Closure):
                            # It's a closure - apply it
                            self._consume_gas(GasCost.FUNCTION_CALL, f"closure call: {operator}")
                            
                            # Check arity
                            if len(args) != len(func.params):
                                raise ValueError(f"Arity mismatch: {operator} expects {len(func.params)} args, got {len(args)}")
                            
                            # Create new environment extending the closure's captured environment
                            call_env = func.env.extend(dict(zip(func.params, args)))
                            
                            # Import compiler here to avoid circular dependency
                            from .compiler import compile_to_postfix
                            
                            # Compile and evaluate body in new environment
                            body_jpn = compile_to_postfix(func.body)
                            result = self.eval(body_jpn, env=call_env)
                            
                            # Check result constraints if we have a resource budget
                            if self.resource_budget:
                                self.resource_budget.check_result(result)
                            
                            stack.append(result)
                        elif callable(func):
                            # Built-in function stored in env
                            self._consume_gas(GasCost.FUNCTION_CALL, f"builtin call: {operator}")
                            result = func(*args)
                            if self.resource_budget:
                                self.resource_budget.check_result(result)
                            stack.append(result)
                        else:
                            raise ValueError(f"'{operator}' is not a function")
                    else:
                        raise ValueError(f"Undefined function: {operator}")
            
            elif isinstance(instr, (int, float, bool, type(None))):
                # Push literal number/bool/null
                self._consume_gas(GasCost.LITERAL, "literal")
                stack.append(instr)
                pc += 1
            
            elif isinstance(instr, str):
                if instr.startswith('@'):
                    # Literal string (@ prefix)
                    self._consume_gas(GasCost.LITERAL, "string literal")
                    result = instr[1:]
                    if self.resource_budget:
                        self.resource_budget.check_string_length(len(result))
                    stack.append(result)
                else:
                    # Variable lookup
                    self._consume_gas(GasCost.VARIABLE, f"variable {instr}")
                    try:
                        value = self.env.get(instr)
                        stack.append(value)
                    except:
                        raise ValueError(f"Undefined variable: {instr}")
                pc += 1
            
            elif isinstance(instr, list):
                # Push list literal
                self._consume_gas(GasCost.LIST_CREATE + len(instr) * GasCost.LIST_PER_ITEM, "list literal")
                if self.resource_budget:
                    self.resource_budget.check_collection_size(len(instr))
                stack.append(instr)
                pc += 1
            
            elif isinstance(instr, dict):
                # Push dict literal
                self._consume_gas(GasCost.DICT_CREATE + len(instr) * GasCost.DICT_PER_ITEM, "dict literal")
                if self.resource_budget:
                    self.resource_budget.check_collection_size(len(instr))
                stack.append(instr)
                pc += 1
            
            else:
                # Other types - push as-is
                self._consume_gas(GasCost.LITERAL, "literal")
                stack.append(instr)
                pc += 1
        
        if len(stack) != 1:
            raise ValueError(f"Invalid expression: stack has {len(stack)} items at end")
        
        # Restore original env if we overrode it
        if old_env is not None:
            self.env = old_env
        
        return stack[0]
    
    def eval_partial(self, instructions: List[Any], max_steps: int, 
                     state: Optional[StackState] = None) -> tuple[Optional[Any], Optional[StackState]]:
        """
        Evaluate with step limit for resumption.
        
        Args:
            instructions: Postfix instructions
            max_steps: Maximum steps to execute
            state: Optional saved state
            
        Returns:
            Tuple of (result, state) - result is None if not complete
            
        Raises:
            ResourceExhausted: When resource limits are exceeded
        """
        if state:
            stack = state.stack.copy()
            pc = state.pc
            instructions = state.instructions
            # Restore resource state if available
            if state.resource_checkpoint and self.resource_budget:
                self.resource_budget.restore(state.resource_checkpoint)
            # Restore user environment if available
            if state.env:
                # Use the restored environment
                self.env = state.env
        else:
            stack = []
            pc = 0
            self._last_tracked_memory = 0  # Reset memory tracking
        
        steps = 0
        
        while pc < len(instructions) and steps < max_steps:
            # Check resources before each operation
            self._check_resources()
            self._track_memory_for_stack(len(stack))
            
            instr = instructions[pc]
            
            # Check if this is an arity (number followed by operator)
            if (isinstance(instr, int) and 
                pc + 1 < len(instructions) and 
                isinstance(instructions[pc + 1], str) and
                (instructions[pc + 1] in self.builtins or
                 instructions[pc + 1] in self.env)):
                # This is an arity-operator pair
                arity = instr
                operator = instructions[pc + 1]
                pc += 2  # Skip both arity and operator
                
                # Consume gas based on operation type and arity
                # Use different gas costs based on operator type
                if operator in ['+', '-', '*', '/', '%']:
                    base_cost = GasCost.ARITHMETIC
                elif operator in ['=', '!=', '<', '>', '<=', '>=']:
                    base_cost = GasCost.COMPARISON
                elif operator in ['not', 'and', 'or']:
                    base_cost = GasCost.LOGICAL
                else:
                    # Built-in function call (list operations, etc.)
                    base_cost = GasCost.FUNCTION_CALL
                
                if arity == 2:
                    self._consume_gas(base_cost, f"binary {operator}")
                else:
                    self._consume_gas(base_cost + arity, f"n-ary {operator}")
                
                # Pop arguments from stack
                if len(stack) < arity:
                    raise ValueError(f"Stack underflow: {operator} needs {arity} args, have {len(stack)}")
                
                args = []
                for _ in range(arity):
                    args.insert(0, stack.pop())
                
                # Apply operator
                if operator in self.builtins:
                    result = self.builtins[operator](args)
                    
                    # Check result constraints if we have a resource budget
                    if self.resource_budget:
                        self.resource_budget.check_result(result)
                    
                    stack.append(result)
                else:
                    # Not a builtin - could be a user-defined function in env
                    if operator in self.env:
                        func = self.env.get(operator)
                        if isinstance(func, Closure):
                            # It's a closure - apply it
                            self._consume_gas(GasCost.FUNCTION_CALL, f"closure call: {operator}")
                            
                            # Check arity
                            if len(args) != len(func.params):
                                raise ValueError(f"Arity mismatch: {operator} expects {len(func.params)} args, got {len(args)}")
                            
                            # Create new environment extending the closure's captured environment
                            call_env = func.env.extend(dict(zip(func.params, args)))
                            
                            # Import compiler here to avoid circular dependency
                            from .compiler import compile_to_postfix
                            
                            # Compile and evaluate body in new environment
                            body_jpn = compile_to_postfix(func.body)
                            result = self.eval(body_jpn, env=call_env)
                            
                            # Check result constraints if we have a resource budget
                            if self.resource_budget:
                                self.resource_budget.check_result(result)
                            
                            stack.append(result)
                        elif callable(func):
                            # Built-in function stored in env
                            self._consume_gas(GasCost.FUNCTION_CALL, f"builtin call: {operator}")
                            result = func(*args)
                            if self.resource_budget:
                                self.resource_budget.check_result(result)
                            stack.append(result)
                        else:
                            raise ValueError(f"'{operator}' is not a function")
                    else:
                        raise ValueError(f"Undefined function: {operator}")
            
            elif isinstance(instr, (int, float, bool, type(None))):
                # Push literal number/bool/null
                self._consume_gas(GasCost.LITERAL, "literal")
                stack.append(instr)
                pc += 1
            
            elif isinstance(instr, str):
                if instr.startswith('@'):
                    # Literal string (@ prefix)
                    self._consume_gas(GasCost.LITERAL, "string literal")
                    result = instr[1:]
                    if self.resource_budget:
                        self.resource_budget.check_string_length(len(result))
                    stack.append(result)
                else:
                    # Variable lookup
                    self._consume_gas(GasCost.VARIABLE, f"variable {instr}")
                    try:
                        value = self.env.get(instr)
                        stack.append(value)
                    except:
                        raise ValueError(f"Undefined variable: {instr}")
                pc += 1
            
            elif isinstance(instr, list):
                # Push list literal
                self._consume_gas(GasCost.LIST_CREATE + len(instr) * GasCost.LIST_PER_ITEM, "list literal")
                if self.resource_budget:
                    self.resource_budget.check_collection_size(len(instr))
                stack.append(instr)
                pc += 1
            
            elif isinstance(instr, dict):
                # Push dict literal
                self._consume_gas(GasCost.DICT_CREATE + len(instr) * GasCost.DICT_PER_ITEM, "dict literal")
                if self.resource_budget:
                    self.resource_budget.check_collection_size(len(instr))
                stack.append(instr)
                pc += 1
            
            else:
                # Other types - push as-is
                self._consume_gas(GasCost.LITERAL, "literal")
                stack.append(instr)
                pc += 1
            
            steps += 1
        
        if pc >= len(instructions) and len(stack) == 1:
            # Complete
            return stack[0], None
        else:
            # Incomplete - save state with resource checkpoint
            resource_checkpoint = None
            if self.resource_budget:
                resource_checkpoint = self.resource_budget.checkpoint()
            
            state = StackState(
                stack=stack, 
                pc=pc, 
                instructions=instructions,
                resource_checkpoint=resource_checkpoint,
                env=self.env
            )
            return None, state


# Test the evaluator
if __name__ == "__main__":
    from jsl.compiler import compile_to_postfix
    
    evaluator = StackEvaluator()
    
    test_cases = [
        (['+', 2, 3], 5),
        (['*', 2, 3], 6),
        (['*', 2, ['+', 1, 2]], 6),
        (['+', ['-', 5, 2], 3], 6),
        (['*', ['+', 2, 3], ['-', 7, 3]], 20),
        (['+', 1, 2, 3, 4], 10),
        (['=', 5, 5], True),
        (['not', ['=', 1, 2]], True),
    ]
    
    print("=== Stack Evaluator Tests ===\n")
    
    for sexpr, expected in test_cases:
        postfix = compile_to_postfix(sexpr)
        result = evaluator.eval(postfix)
        status = "✓" if result == expected else "✗"
        print(f"{status} {sexpr} = {result} (expected {expected})")
        print(f"  Postfix: {postfix}")
    
    print("\n=== Resumption Test ===\n")
    
    # Test resumption with limited steps
    expr = ['*', ['+', 10, 20], ['-', 100, 50]]
    postfix = compile_to_postfix(expr)
    print(f"Expression: {expr}")
    print(f"Postfix: {postfix}")
    print(f"Expected: {(10+20) * (100-50)} = {30 * 50}")
    print()
    
    result = None
    state = None
    attempt = 1
    
    while result is None and attempt <= 10:
        result, state = evaluator.eval_partial(postfix, max_steps=2, state=state)
        if result is None:
            print(f"Attempt {attempt}: Not complete, state = {state.stack}, pc = {state.pc}")
        else:
            print(f"Attempt {attempt}: Complete! Result = {result}")
        attempt += 1