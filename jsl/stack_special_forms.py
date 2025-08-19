"""
Special forms support for the stack evaluator.

Special forms like 'if', 'let', 'lambda', 'def', 'do', and 'quote' have
special evaluation rules that can't be compiled to simple postfix notation.
This module provides support for handling them in the stack evaluator.
"""

from typing import Any, List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from .core import Closure, Env


class Opcode(Enum):
    """Special opcodes for control flow and special forms."""
    # Control flow
    JUMP = "jump"               # Unconditional jump
    JUMP_IF_FALSE = "jump_if_false"  # Conditional jump
    JUMP_IF_TRUE = "jump_if_true"    # Conditional jump
    
    # Environment manipulation
    PUSH_ENV = "push_env"       # Create new environment frame
    POP_ENV = "pop_env"         # Restore previous environment
    DEFINE = "define"           # Define variable in current env
    SET = "set"                 # Set variable in env chain
    
    # Lambda and closure
    MAKE_CLOSURE = "make_closure"  # Create closure
    CALL_CLOSURE = "call_closure"  # Call closure
    RETURN = "return"           # Return from closure
    
    # Special markers
    QUOTE = "quote"             # Quote next expression
    SPECIAL_FORM = "special_form"  # Mark special form


@dataclass
class CompiledSpecialForm:
    """
    Compiled representation of a special form.
    
    Special forms are compiled to a sequence of opcodes and operands
    that can be executed by the enhanced stack evaluator.
    """
    opcodes: List[Any]
    metadata: Dict[str, Any]


def compile_special_form(expr: List[Any]) -> Optional[CompiledSpecialForm]:
    """
    Compile a special form to stack machine opcodes.
    
    Args:
        expr: S-expression that might be a special form
        
    Returns:
        CompiledSpecialForm if expr is a special form, None otherwise
    """
    if not isinstance(expr, list) or len(expr) == 0:
        return None
    
    op = expr[0]
    
    if op == "if":
        return compile_if(expr)
    elif op == "let":
        return compile_let(expr)
    elif op == "lambda":
        return compile_lambda(expr)
    elif op == "def":
        return compile_def(expr)
    elif op == "do":
        return compile_do(expr)
    elif op == "quote":
        return compile_quote(expr)
    else:
        return None


def compile_if(expr: List[Any]) -> CompiledSpecialForm:
    """
    Compile 'if' special form.
    
    [if, condition, then_expr, else_expr] compiles to:
    1. Evaluate condition
    2. JUMP_IF_FALSE to else branch
    3. Evaluate then_expr
    4. JUMP to end
    5. Evaluate else_expr
    6. End
    """
    if len(expr) != 4:
        raise ValueError(f"'if' requires exactly 3 arguments, got {len(expr)-1}")
    
    _, condition, then_expr, else_expr = expr
    
    # We need to compile sub-expressions recursively
    # For now, return a marker that the evaluator will handle
    return CompiledSpecialForm(
        opcodes=[Opcode.SPECIAL_FORM, "if", condition, then_expr, else_expr],
        metadata={"form": "if"}
    )


def compile_let(expr: List[Any]) -> CompiledSpecialForm:
    """
    Compile 'let' special form.
    
    [let, [var, value], body] compiles to:
    1. Evaluate value
    2. PUSH_ENV
    3. DEFINE var with value
    4. Evaluate body
    5. POP_ENV
    """
    if len(expr) != 3:
        raise ValueError(f"'let' requires exactly 2 arguments, got {len(expr)-1}")
    
    _, binding, body = expr
    
    if not isinstance(binding, list) or len(binding) != 2:
        raise ValueError("'let' binding must be a list of [var, value]")
    
    var, value = binding
    
    return CompiledSpecialForm(
        opcodes=[Opcode.SPECIAL_FORM, "let", var, value, body],
        metadata={"form": "let", "var": var}
    )


def compile_lambda(expr: List[Any]) -> CompiledSpecialForm:
    """
    Compile 'lambda' special form.
    
    [lambda, [param1, ...], body] compiles to:
    1. MAKE_CLOSURE with params and body
    """
    if len(expr) != 3:
        raise ValueError(f"'lambda' requires exactly 2 arguments, got {len(expr)-1}")
    
    _, params, body = expr
    
    if not isinstance(params, list):
        raise ValueError("'lambda' parameters must be a list")
    
    return CompiledSpecialForm(
        opcodes=[Opcode.SPECIAL_FORM, "lambda", params, body],
        metadata={"form": "lambda", "params": params}
    )


def compile_def(expr: List[Any]) -> CompiledSpecialForm:
    """
    Compile 'def' special form.
    
    [def, var, value] compiles to:
    1. Evaluate value
    2. DEFINE var with value
    """
    if len(expr) != 3:
        raise ValueError(f"'def' requires exactly 2 arguments, got {len(expr)-1}")
    
    _, var, value = expr
    
    if not isinstance(var, str):
        raise ValueError("'def' variable name must be a string")
    
    return CompiledSpecialForm(
        opcodes=[Opcode.SPECIAL_FORM, "def", var, value],
        metadata={"form": "def", "var": var}
    )


def compile_do(expr: List[Any]) -> CompiledSpecialForm:
    """
    Compile 'do' special form.
    
    [do, expr1, expr2, ...] evaluates all expressions in sequence
    and returns the last value.
    """
    if len(expr) < 2:
        raise ValueError("'do' requires at least one expression")
    
    expressions = expr[1:]
    
    return CompiledSpecialForm(
        opcodes=[Opcode.SPECIAL_FORM, "do"] + expressions,
        metadata={"form": "do", "count": len(expressions)}
    )


def compile_quote(expr: List[Any]) -> CompiledSpecialForm:
    """
    Compile 'quote' special form.
    
    [quote, expr] returns expr without evaluation.
    """
    if len(expr) != 2:
        raise ValueError(f"'quote' requires exactly 1 argument, got {len(expr)-1}")
    
    _, quoted = expr
    
    return CompiledSpecialForm(
        opcodes=[Opcode.SPECIAL_FORM, "quote", quoted],
        metadata={"form": "quote"}
    )


class SpecialFormEvaluator:
    """
    Evaluator for special forms within the stack machine.
    
    This is used by the StackEvaluator when it encounters special forms.
    """
    
    def __init__(self, stack_evaluator):
        """
        Initialize with reference to parent stack evaluator.
        
        Args:
            stack_evaluator: The StackEvaluator instance
        """
        self.evaluator = stack_evaluator
    
    def eval_special_form(self, form: str, args: List[Any], env: Env) -> Any:
        """
        Evaluate a special form.
        
        Args:
            form: The special form name
            args: Arguments to the special form
            env: Current environment
            
        Returns:
            Result of evaluating the special form
        """
        if form == "if":
            return self.eval_if(args, env)
        elif form == "let":
            return self.eval_let(args, env)
        elif form == "lambda":
            return self.eval_lambda(args, env)
        elif form == "def":
            return self.eval_def(args, env)
        elif form == "do":
            return self.eval_do(args, env)
        elif form == "quote" or form == "@":
            return self.eval_quote(args, env)
        elif form == "try":
            return self.eval_try(args, env)
        elif form == "host":
            return self.eval_host(args, env)
        elif form == "where":
            return self.eval_where(args, env)
        elif form == "transform":
            return self.eval_transform(args, env)
        else:
            raise ValueError(f"Unknown special form: {form}")
    
    def eval_if(self, args: List[Any], env: Env) -> Any:
        """Evaluate 'if' special form."""
        if len(args) != 3:
            raise ValueError(f"'if' requires exactly 3 arguments, got {len(args)}")
        
        condition, then_expr, else_expr = args
        
        # Evaluate condition using the parent evaluator
        # We need to compile and evaluate in the current environment
        from .compiler import compile_to_postfix
        cond_jpn = compile_to_postfix(condition)
        
        # Pass environment as parameter to eval
        cond_result = self.evaluator.eval(cond_jpn, env=env)
        
        # Choose and evaluate the appropriate branch
        if cond_result:
            branch_jpn = compile_to_postfix(then_expr)
        else:
            branch_jpn = compile_to_postfix(else_expr)
        
        # Evaluate chosen branch with environment
        return self.evaluator.eval(branch_jpn, env=env)
    
    def eval_let(self, args: List[Any], env: Env) -> Any:
        """
        Evaluate 'let' special form: ["let", [[name, value], ...], body]
        
        Multiple bindings are supported and evaluated sequentially in the
        original environment, then the body is evaluated in the extended environment.
        """
        if len(args) != 2:
            raise ValueError(f"'let' requires exactly 2 arguments: bindings and body, got {len(args)}")
        
        bindings, body = args
        
        if not isinstance(bindings, list):
            raise ValueError("'let' bindings must be a list")
        
        # Create new environment with bindings
        from .compiler import compile_to_postfix
        
        # Build bindings dict first
        new_bindings = {}
        for binding in bindings:
            if not isinstance(binding, list) or len(binding) != 2:
                raise ValueError("Each 'let' binding must be [name, value]")
            
            name, value_expr = binding
            if not isinstance(name, str):
                raise ValueError("'let' binding name must be a string")
            
            # Evaluate value in current environment (not the new one)
            value_jpn = compile_to_postfix(value_expr)
            value_result = self.evaluator.eval(value_jpn, env=env)
            new_bindings[name] = value_result
        
        # Create extended environment and evaluate body
        new_env = env.extend(new_bindings)
        body_jpn = compile_to_postfix(body)
        return self.evaluator.eval(body_jpn, env=new_env)
    
    def eval_lambda(self, args: List[Any], env: Env) -> Any:
        """Evaluate 'lambda' special form."""
        if len(args) != 2:
            raise ValueError(f"'lambda' requires exactly 2 arguments, got {len(args)}")
        
        params, body = args
        
        # Create a proper Closure object that captures the full environment
        return Closure(params, body, env)
    
    def eval_def(self, args: List[Any], env: Env) -> Any:
        """Evaluate 'def' special form."""
        if len(args) != 2:
            raise ValueError(f"'def' requires exactly 2 arguments, got {len(args)}")
        
        var, value = args
        
        # Check if the value is already a Closure (from a previous evaluation)
        # This happens when a closure is created and then passed to def
        if isinstance(value, Closure):
            # It's already evaluated - don't evaluate again
            value_result = value
        else:
            # Evaluate value normally
            from .compiler import compile_to_postfix
            value_jpn = compile_to_postfix(value)
            value_result = self.evaluator.eval(value_jpn, env=env)
        
        # Define in environment
        env.define(var, value_result)
        # Also update the evaluator's base environment
        self.evaluator.env.define(var, value_result)
        return value_result
    
    def eval_do(self, args: List[Any], env: Env) -> Any:
        """Evaluate 'do' special form."""
        if len(args) == 0:
            return None
        
        result = None
        from .compiler import compile_to_postfix
        
        for expr in args:
            expr_jpn = compile_to_postfix(expr)
            result = self.evaluator.eval(expr_jpn, env=env)
        
        return result
    
    def eval_quote(self, args: List[Any], env: Env) -> Any:
        """Evaluate 'quote' special form."""
        # Simply return the quoted expression without evaluation
        return args[0]
    
    def eval_try(self, args: List[Any], env: Env) -> Any:
        """Evaluate 'try' special form: ["try", body, handler]"""
        if len(args) != 2:
            raise ValueError(f"'try' requires exactly 2 arguments, got {len(args)}")
        
        body, handler = args
        
        try:
            # Try to evaluate the body
            from .compiler import compile_to_postfix
            body_jpn = compile_to_postfix(body)
            return self.evaluator.eval(body_jpn, env=env)
        except Exception as e:
            # Create error object
            error_obj = {
                "type": type(e).__name__,
                "message": str(e)
            }
            
            # Evaluate the handler to get a function
            handler_jpn = compile_to_postfix(handler)
            handler_func = self.evaluator.eval(handler_jpn, env=env)
            
            # Check if handler is a closure
            if not isinstance(handler_func, Closure):
                raise ValueError("'try' handler must be a function")
            
            # Apply handler function to the error
            params = handler_func.params
            body = handler_func.body
            
            # Check arity
            if len(params) != 1:
                raise ValueError(f"'try' handler must take exactly 1 argument, got {len(params)}")
            
            # Create new environment with error bound
            new_env = handler_func.env.extend({params[0]: error_obj})
            
            # Evaluate handler body
            handler_body_jpn = compile_to_postfix(body)
            return self.evaluator.eval(handler_body_jpn, env=new_env)
    
    def eval_where(self, args: List[Any], env: Env) -> Any:
        """
        Evaluate 'where' special form: filter collection by condition.
        
        Args:
            args: [collection, condition] 
            env: Current environment
            
        Returns:
            Filtered collection
        """
        if len(args) != 2:
            raise ValueError("where requires exactly 2 arguments: collection and condition")
        
        # Import here to avoid circular dependency
        from .compiler import compile_to_postfix
        
        # Evaluate the collection
        collection_jpn = compile_to_postfix(args[0])
        collection = self.evaluator.eval(collection_jpn, env=env)
        
        # The condition expression
        condition_expr = args[1]
        
        # Handle both list and dict collections
        if isinstance(collection, dict):
            items = list(collection.values())
        elif isinstance(collection, list):
            items = collection
        else:
            raise TypeError(f"where requires a list or dict, got {type(collection).__name__}")
        
        # Filter items
        result = []
        for item in items:
            # Extend environment with item's fields
            if isinstance(item, dict):
                # Add all fields from the dict item to the environment
                # Also bind the item itself to '$' for accessing nested fields
                extended_env = env.extend({**item, '$': item})
            else:
                # For non-dict items, bind '$' to the item
                extended_env = env.extend({'$': item})
            
            # Compile and evaluate condition in extended environment
            condition_jpn = compile_to_postfix(condition_expr)
            try:
                if self.evaluator.eval(condition_jpn, env=extended_env):
                    result.append(item)
            except:
                # If condition evaluation fails, skip the item
                pass
        
        return result
    
    def eval_transform(self, args: List[Any], env: Env) -> Any:
        """
        Evaluate 'transform' special form: apply transformations to data.
        
        Args:
            args: [data, operation1, operation2, ...] 
            env: Current environment
            
        Returns:
            Transformed data
        """
        if len(args) < 2:
            raise ValueError("transform requires at least data and one operation")
        
        # Import here to avoid circular dependency
        from .compiler import compile_to_postfix
        
        # Evaluate the data
        data_jpn = compile_to_postfix(args[0])
        data = self.evaluator.eval(data_jpn, env=env)
        
        # Get the operations
        operations = args[1:]
        
        # Handle both single objects and collections
        is_collection = isinstance(data, list)
        items = data if is_collection else [data]
        
        # Apply each operation in sequence
        for operation_expr in operations:
            new_items = []
            for item in items:
                # Extend environment with item's fields
                if isinstance(item, dict):
                    # Also bind the item itself to '$' for accessing nested fields
                    extended_env = env.extend({**item, '$': item})
                else:
                    extended_env = env.extend({'$': item})
                
                # Compile and evaluate the operation
                operation_jpn = compile_to_postfix(operation_expr)
                operation = self.evaluator.eval(operation_jpn, env=extended_env)
                
                # Apply the operation
                if not isinstance(operation, list) or len(operation) < 2:
                    raise ValueError("Transform operation must be a list with at least 2 elements")
                
                op_type = operation[0]
                result = item.copy() if isinstance(item, dict) else {}
                
                if op_type == "assign":
                    if len(operation) != 3:
                        raise ValueError("'assign' requires field and value")
                    field = operation[1]
                    value = operation[2]
                    result[field] = value
                    
                elif op_type == "pick":
                    fields = operation[1:]
                    result = {k: v for k, v in item.items() if k in fields} if isinstance(item, dict) else {}
                    
                elif op_type == "omit":
                    fields = operation[1:]
                    if isinstance(item, dict):
                        result = item.copy()
                        for field in fields:
                            result.pop(field, None)
                    
                elif op_type == "rename":
                    if len(operation) != 3:
                        raise ValueError("'rename' requires old_field and new_field")
                    old_field, new_field = operation[1], operation[2]
                    if isinstance(item, dict) and old_field in item:
                        result = item.copy()
                        result[new_field] = result.pop(old_field)
                    
                elif op_type == "default":
                    if len(operation) != 3:
                        raise ValueError("'default' requires field and value")
                    field = operation[1]
                    value = operation[2]
                    if isinstance(item, dict):
                        result = item.copy()
                        if field not in result:
                            result[field] = value
                    
                elif op_type == "apply":
                    if len(operation) != 3:
                        raise ValueError("'apply' requires field and function")
                    field = operation[1]
                    func_expr = operation[2]
                    if isinstance(item, dict) and field in item:
                        result = item.copy()
                        # Evaluate the function if it's an expression
                        if isinstance(func_expr, list):
                            func_jpn = compile_to_postfix(func_expr)
                            func = self.evaluator.eval(func_jpn, env=extended_env)
                        else:
                            func = func_expr
                        
                        # Apply the function
                        if isinstance(func, Closure):
                            # Apply the closure
                            params = func.params
                            body = func.body
                            
                            if len(params) != 1:
                                raise ValueError(f"Transform apply function must take 1 argument, got {len(params)}")
                            
                            # Create new environment with parameter bound
                            new_env = func.env.extend({params[0]: item[field]})
                            
                            # Evaluate function body
                            body_jpn = compile_to_postfix(body)
                            result[field] = self.evaluator.eval(body_jpn, env=new_env)
                        elif callable(func):
                            result[field] = func(item[field])
                        else:
                            raise TypeError(f"Cannot apply non-function: {type(func).__name__}")
                else:
                    raise ValueError(f"Unknown transform operation: {op_type}")
                
                new_items.append(result)
            
            items = new_items
        
        return items if is_collection else items[0]
    
    def eval_host(self, args: List[Any], env: Env) -> Any:
        """Evaluate 'host' special form: ["host", command, arg1, ...]"""
        if len(args) < 1:
            raise ValueError("'host' requires at least a command")
        
        from .compiler import compile_to_postfix
        
        # Evaluate the command
        command_jpn = compile_to_postfix(args[0])
        command = self.evaluator.eval(command_jpn, env=env)
        
        if not isinstance(command, str):
            raise ValueError("Host command must be a string")
        
        # Evaluate all arguments
        eval_args = []
        for arg in args[1:]:
            arg_jpn = compile_to_postfix(arg)
            eval_args.append(self.evaluator.eval(arg_jpn, env=env))
        
        # Get host dispatcher from the evaluator
        if hasattr(self.evaluator, 'host_dispatcher') and self.evaluator.host_dispatcher:
            # Dispatch the host command
            return self.evaluator.host_dispatcher.dispatch(command, eval_args)
        else:
            raise ValueError("No host dispatcher available")


def detect_special_form(expr: Any) -> bool:
    """
    Check if an expression is a special form.
    
    Args:
        expr: Expression to check
        
    Returns:
        True if expr is a special form, False otherwise
    """
    if not isinstance(expr, list) or len(expr) == 0:
        return False
    
    op = expr[0]
    # Only detect special form if operator is a string
    return isinstance(op, str) and op in {"if", "let", "lambda", "def", "do", "quote", "@", "try", "host", "where", "transform"}


def hybrid_compile(expr: Any) -> List[Any]:
    """
    Hybrid compilation that preserves special forms.
    
    This compiles regular expressions to JPN but leaves special forms
    as structured data with a marker for the evaluator to handle.
    
    Args:
        expr: Expression to compile
        
    Returns:
        JPN instructions with special form markers
    """
    if detect_special_form(expr):
        # Mark as special form for evaluator
        return [Opcode.SPECIAL_FORM, expr]
    else:
        # Regular compilation to JPN
        from .compiler import compile_to_postfix
        return compile_to_postfix(expr)


# Example usage and testing
if __name__ == "__main__":
    # Test special form detection
    test_cases = [
        ["if", ["=", "x", 0], "@zero", "@nonzero"],
        ["let", ["x", 10], ["*", "x", 2]],
        ["lambda", ["x"], ["*", "x", "x"]],
        ["def", "square", ["lambda", ["x"], ["*", "x", "x"]]],
        ["do", ["print", "@Hello"], ["print", "@World"], 42],
        ["quote", ["*", 2, 3]],
        ["+", 1, 2, 3],  # Not a special form
    ]
    
    print("Special Form Detection:")
    print("-" * 40)
    for expr in test_cases:
        is_special = detect_special_form(expr)
        print(f"{str(expr)[:50]:<50} {'✓ Special' if is_special else '✗ Regular'}")
    
    print("\nCompilation Examples:")
    print("-" * 40)
    for expr in test_cases[:6]:
        try:
            compiled = compile_special_form(expr)
            if compiled:
                print(f"{expr[0]:10} → {compiled.metadata}")
        except ValueError as e:
            print(f"{expr[0]:10} → Error: {e}")