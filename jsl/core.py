"""
JSL (JSON Serializable Language) - Core Module

This module provides the fundamental data structures and evaluation engine
for JSL, a network-native functional programming language.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
import json
from .resources import ResourceBudget, ResourceLimits, GasCost, HostGasPolicy
import hashlib


# Type aliases for clarity
JSLValue = Union[str, int, float, bool, None, List, Dict]
JSLExpression = JSLValue
Environment = Dict[str, Any]


class JSLError(Exception):
    """Base exception for all JSL runtime errors."""
    pass


class SymbolNotFoundError(JSLError):
    """Raised when a symbol cannot be found in the current environment."""
    pass


class JSLTypeError(JSLError):
    """Raised when there's a type mismatch in JSL operations."""
    pass


@dataclass
class Closure:
    """
    Represents a JSL function (closure).
    
    A closure captures three things:
    1. The parameter names it expects
    2. The body expression to evaluate when called
    3. The environment where it was defined (lexical scoping)
    """
    params: List[str]
    body: JSLExpression
    env: 'Env'
    
    def __call__(self, evaluator: 'Evaluator', args: List[JSLValue]) -> JSLValue:
        """Apply this closure to the given arguments."""
        if len(args) != len(self.params):
            raise JSLTypeError(f"Function expects {len(self.params)} arguments, got {len(args)}")
        
        # Create new environment extending the closure's captured environment
        call_env = self.env.extend(dict(zip(self.params, args)))
        return evaluator.eval(self.body, call_env)
    
    def deepcopy(self, env: Optional['Env'] = None) -> 'Closure':
        """
        Create a deep copy of this closure.
        
        Args:
            env: Optional environment to use for the copy. If not provided,
                 deep copies the closure's environment.
        """
        # Deep copy the body
        def copy_expr(expr):
            if isinstance(expr, list):
                return [copy_expr(item) for item in expr]
            elif isinstance(expr, dict):
                return {k: copy_expr(v) for k, v in expr.items()}
            else:
                return expr
        
        new_body = copy_expr(self.body)
        new_params = self.params[:]  # Copy params list
        
        # Use provided env or deep copy the closure's env
        if env is not None:
            new_env = env
        else:
            new_env = self.env.deepcopy() if self.env else None
        
        return Closure(new_params, new_body, new_env)


class Env:
    """
    Represents a JSL environment - a scope containing variable bindings.
    
    Environments form a chain: each environment has an optional parent.
    When looking up a variable, we search the current environment first,
    then its parent, and so on until we find it or reach the root.
    """
    
    def __init__(self, bindings: Optional[Dict[str, Any]] = None, parent: Optional['Env'] = None):
        self.bindings = bindings or {}
        self.parent = parent
        # Prelude metadata (set by make_prelude)
        self._prelude_id = None
        self._prelude_version = None
        self._is_prelude = False
    
    def get(self, name: str) -> Any:
        """Look up a variable in this environment or its parents."""
        if name in self.bindings:
            return self.bindings[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise SymbolNotFoundError(f"Symbol '{name}' not found")
    
    def __contains__(self, name: str) -> bool:
        """Check if a variable exists in this environment or its parents."""
        if name in self.bindings:
            return True
        elif self.parent:
            return name in self.parent
        else:
            return False
    
    def __eq__(self, other: Any) -> bool:
        """Check if two environments are equal."""
        if not isinstance(other, Env):
            return False
        
        # Check prelude compatibility
        if self._is_prelude and other._is_prelude:
            # Both are preludes - compare by ID
            return self._prelude_id == other._prelude_id
        elif self._is_prelude or other._is_prelude:
            # One is prelude, other isn't - not equal
            return False
        
        # Get all bindings from both environments (including parents)
        self_bindings = self.to_dict()
        other_bindings = other.to_dict()
        
        # Check if they have the same keys
        if set(self_bindings.keys()) != set(other_bindings.keys()):
            return False
        
        # Check if all values are equal
        for key in self_bindings:
            self_val = self_bindings[key]
            other_val = other_bindings[key]
            
            # Special handling for Closures - compare structure not identity
            if isinstance(self_val, Closure) and isinstance(other_val, Closure):
                if not self._closures_equal(self_val, other_val):
                    return False
            elif callable(self_val) and callable(other_val):
                # For callable functions (like prelude), just check they're both callable
                # Can't really compare lambdas/functions for equality in Python
                continue
            elif self_val != other_val:
                return False
        
        return True
    
    def _closures_equal(self, c1: 'Closure', c2: 'Closure') -> bool:
        """Check if two closures are structurally equal."""
        # Compare params and body
        if c1.params != c2.params or c1.body != c2.body:
            return False
        
        # For environments, we need to be careful about cycles
        # Just check that they have the same bindings available
        c1_bindings = c1.env.to_dict() if c1.env else {}
        c2_bindings = c2.env.to_dict() if c2.env else {}
        
        # Compare keys
        if set(c1_bindings.keys()) != set(c2_bindings.keys()):
            return False
        
        # For now, don't recurse into closure environments to avoid infinite loops
        # Just verify they have the same structure
        return True
    
    def define(self, name: str, value: Any) -> None:
        """Define a variable in this environment."""
        # Prevent modification of immutable preludes
        if self._is_prelude:
            raise JSLError("Cannot modify prelude environment. Use extend() to create a new environment.")
        self.bindings[name] = value
    
    def extend(self, new_bindings: Dict[str, Any]) -> 'Env':
        """Create a new environment that extends this one with additional bindings."""
        return Env(new_bindings, parent=self)
    
    def deepcopy(self) -> 'Env':
        """Create a deep copy of this environment, including all parents."""
        # First, gather all bindings from this env and parents
        all_bindings = self.to_dict()
        
        # Create a mapping of old closures to new closures to handle cycles
        closure_map = {}
        
        # Create new environment with copied bindings
        new_env = Env()
        
        # Copy prelude metadata if present
        new_env._prelude_id = self._prelude_id
        new_env._prelude_version = self._prelude_version
        new_env._is_prelude = self._is_prelude
        
        # First pass: copy non-closure values
        for name, value in all_bindings.items():
            if not isinstance(value, Closure):
                # For non-closures, just copy the value
                if isinstance(value, (list, dict)):
                    import copy
                    new_env.bindings[name] = copy.deepcopy(value)
                else:
                    new_env.bindings[name] = value
        
        # Second pass: copy closures with updated env references
        for name, value in all_bindings.items():
            if isinstance(value, Closure):
                # Deep copy the closure with the new environment
                new_closure = value.deepcopy(env=new_env)
                new_env.bindings[name] = new_closure
                closure_map[id(value)] = new_closure
        
        return new_env
    
    def _deepcopy_expr(self, expr: Any) -> Any:
        """Deep copy a JSL expression."""
        if isinstance(expr, list):
            return [self._deepcopy_expr(item) for item in expr]
        elif isinstance(expr, dict):
            return {k: self._deepcopy_expr(v) for k, v in expr.items()}
        else:
            return expr
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert environment bindings to a dictionary (for serialization)."""
        result = {}
        if self.parent:
            result.update(self.parent.to_dict())
        result.update(self.bindings)
        return result
    
    def content_hash(self) -> str:
        """Generate a content-addressable hash with cycle detection."""
        # Thread-local cycle detection for rock-solid safety
        import threading
        if not hasattr(Env, '_cycle_detection'):
            Env._cycle_detection = threading.local()
        
        if not hasattr(Env._cycle_detection, 'computing'):
            Env._cycle_detection.computing = set()
        
        env_id = id(self)
        if env_id in Env._cycle_detection.computing:
            # Cycle detected - return deterministic placeholder
            return f"cycle_{env_id:016x}"
        
        # Add to cycle detection set
        Env._cycle_detection.computing.add(env_id) 
        
        try:
            canonical = {
                "bindings": self._serialize_bindings(),
                "parent_hash": self.parent.content_hash() if self.parent else None
            }
            # Convert to string - handle special cases
            try:
                content = json.dumps(canonical, sort_keys=True)
            except (TypeError, ValueError):
                # If we can't serialize (due to complex objects), use a fallback
                # This can happen when bindings contain data structures with Closures
                content = str(sorted(canonical.get("bindings", {}).keys())) + str(canonical.get("parent_hash"))
            return hashlib.sha256(content.encode()).hexdigest()[:16]
            
        finally:
            # Always clean up, even on exceptions
            Env._cycle_detection.computing.discard(env_id)
            
            # Clean up thread-local storage when empty
            if not Env._cycle_detection.computing:
                delattr(Env._cycle_detection, 'computing')
    
    def _serialize_bindings(self) -> Dict[str, Any]:
        """Serialize bindings - cycles handled by content_hash."""
        result = {}
        for k, v in self.bindings.items():
            if isinstance(v, Closure):
                # Let content_hash handle all cycle detection
                result[k] = {
                    "type": "closure",
                    "params": v.params,
                    "body": v.body,
                    "env_hash": v.env.content_hash()  # ← Cycles handled here
                }
            elif not callable(v):
                # For content_hash purposes, just use a placeholder for complex objects
                # The actual serialization will be handled by JSLEncoder
                if self._contains_closures(v):
                    result[k] = {"type": "complex", "id": id(v)}
                else:
                    result[k] = v
            else:
                result[k] = {"type": "builtin", "name": k}
        return result
    
    def _contains_closures(self, value: Any) -> bool:
        """Check if a value contains any Closures."""
        if isinstance(value, Closure):
            return True
        elif isinstance(value, list):
            return any(self._contains_closures(item) for item in value)
        elif isinstance(value, dict):
            return any(self._contains_closures(v) for v in value.values())
        else:
            return False


class HostDispatcher:
    """
    Handles JHIP (JSL Host Interaction Protocol) requests.
    
    This is where all side effects are controlled. The host environment
    registers handlers for specific commands and decides what operations
    are permitted.
    """
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
    
    def register(self, command: str, handler: Callable) -> None:
        """Register a handler for a specific host command."""
        self.handlers[command] = handler
    
    def dispatch(self, command: str, args: List[Any]) -> Any:
        """Dispatch a host command with arguments."""
        if command not in self.handlers:
            raise JSLError(f"Unknown host command: {command}")
        
        try:
            return self.handlers[command](*args)
        except Exception as e:
            raise JSLError(f"Host command '{command}' failed: {e}")


class Evaluator:
    """
    The core JSL evaluator - recursive evaluation engine.
    
    This is a clean, elegant reference implementation that uses traditional 
    recursive tree-walking to evaluate S-expressions. It serves as the
    specification for JSL's semantics.
    
    Characteristics:
    - Simple and easy to understand
    - Direct mapping from S-expressions to evaluation
    - Perfect for learning and testing JSL semantics
    - Limited by Python's recursion depth for deep expressions
    
    For production use with resumption and better performance, use the 
    stack-based evaluator which compiles to JPN (JSL Postfix Notation).
    """
    
    def __init__(self, host_dispatcher: Optional[HostDispatcher] = None, 
                 resource_limits: Optional[ResourceLimits] = None,
                 host_gas_policy: Optional['HostGasPolicy'] = None):
        self.host = host_dispatcher or HostDispatcher()
        self.resources = ResourceBudget(resource_limits, host_gas_policy) if resource_limits else None
    
    def eval(self, expr: JSLExpression, env: Env) -> JSLValue:
        """
        Evaluate a JSL expression in the given environment.
        
        This is a pure recursive evaluator without resumption support.
        For resumable evaluation, use the stack-based evaluator.
        """
        # Resource checking
        if self.resources:
            # Check time periodically
            self.resources.check_time()
            
            # Consume gas based on expression type
            if isinstance(expr, (int, float, bool)) or expr is None:
                self.resources.consume_gas(GasCost.LITERAL)
            elif isinstance(expr, str):
                if expr.startswith("@"):
                    self.resources.consume_gas(GasCost.LITERAL)
                else:
                    self.resources.consume_gas(GasCost.VARIABLE)
            elif isinstance(expr, dict):
                self.resources.consume_gas(GasCost.DICT_CREATE + 
                                          len(expr) * GasCost.DICT_PER_ITEM)
        
        # Literals: numbers, booleans, null, objects
        if isinstance(expr, (int, float, bool)) or expr is None:
            return expr
        
        # Objects: evaluate both keys and values, keys must be strings
        if isinstance(expr, dict):
            return self._eval_dict(expr, env)
        
        # Strings: variables or string literals
        if isinstance(expr, str):
            return self._eval_string(expr, env)
        
        # Arrays: function calls or special forms
        if isinstance(expr, list):
            return self._eval_list(expr, env)
        
        raise JSLTypeError(f"Cannot evaluate expression of type {type(expr)}")
    
    def _eval_string(self, s: str, env: Env) -> JSLValue:
        """Evaluate a string: either a variable lookup or a string literal."""
        if s.startswith('@'):
            # String literal: "@hello" -> "hello"
            return s[1:]
        else:
            # Variable lookup: "x" -> value of x
            return env.get(s)
    
    def _eval_dict(self, obj_expr: Dict[str, Any], env: Env) -> JSLValue:
        """Evaluate a dictionary: keys must be strings, values are evaluated."""
        result = {}
        for key_expr, value_expr in obj_expr.items():
            # Evaluate key - must result in a string
            key_result = self.eval(key_expr, env)
            if not isinstance(key_result, str):
                raise JSLTypeError(f"Object key must evaluate to string, got {type(key_result)}: {key_result}")
            
            # Evaluate value
            value_result = self.eval(value_expr, env)
            result[key_result] = value_result
        return result
        
    def _eval_list(self, lst: List, env: Env) -> JSLValue:
        """Evaluate a list: either a special form or a function call."""
        if not lst:
            return lst  # Empty list evaluates to itself
        
        # Check collection size limit
        if self.resources:
            self.resources.check_collection_size(len(lst))
        
        operator = lst[0]
        
        # Special forms have unique evaluation rules
        if operator == "def":
            return self._eval_def(lst, env)
        elif operator == "lambda":
            return self._eval_lambda(lst, env)
        elif operator == "if":
            return self._eval_if(lst, env)
        elif operator == "let":
            return self._eval_let(lst, env)
        elif operator == "do":
            return self._eval_do(lst, env)
        elif operator == "quote" or operator == "@":
            return self._eval_quote(lst, env)
        elif operator == "try":
            return self._eval_try(lst, env)
        elif operator == "where":
            return self._eval_where(lst, env)
        elif operator == "transform":
            return self._eval_transform(lst, env)
        elif operator == "host":
            return self._eval_host(lst, env)
        else:
            # Regular function call: evaluate operator and arguments
            return self._eval_function_call(lst, env)
    
    def _eval_def(self, lst: List, env: Env) -> JSLValue:
        """Handle 'def' special form: ["def", name, value_expr]"""
        if len(lst) != 3:
            raise JSLError("'def' requires exactly 2 arguments: name and value")
        
        _, name, value_expr = lst
        if not isinstance(name, str):
            raise JSLTypeError("'def' name must be a string")
        
        value = self.eval(value_expr, env)
        env.define(name, value)
        return value
    
    def _eval_lambda(self, lst: List, env: Env) -> Closure:
        """Handle 'lambda' special form: ["lambda", [params], body]"""
        if len(lst) != 3:
            raise JSLError("'lambda' requires exactly 2 arguments: params and body")
        
        _, params, body = lst
        if not isinstance(params, list) or not all(isinstance(p, str) for p in params):
            raise JSLTypeError("'lambda' parameters must be a list of strings")
        
        return Closure(params, body, env)
    
    def _eval_if(self, lst: List, env: Env) -> JSLValue:
        """Handle 'if' special form: ["if", condition, then_expr, else_expr]"""
        if len(lst) != 4:
            raise JSLError("'if' requires exactly 3 arguments: condition, then, else")
        
        _, condition, then_expr, else_expr = lst
        condition_value = self.eval(condition, env)
        
        if self._is_truthy(condition_value):
            return self.eval(then_expr, env)
        else:
            return self.eval(else_expr, env)
    
    def _eval_let(self, lst: List, env: Env) -> JSLValue:
        """Handle 'let' special form: ["let", [[name, value], ...], body]"""
        if len(lst) != 3:
            raise JSLError("'let' requires exactly 2 arguments: bindings and body")
        
        _, bindings, body = lst
        if not isinstance(bindings, list):
            raise JSLTypeError("'let' bindings must be a list")
        
        # Create new environment with the bindings
        new_bindings = {}
        for binding in bindings:
            if not isinstance(binding, list) or len(binding) != 2:
                raise JSLError("Each 'let' binding must be [name, value]")
            
            name, value_expr = binding
            if not isinstance(name, str):
                raise JSLTypeError("'let' binding name must be a string")
            
            # Evaluate in the original environment (not the new one)
            value = self.eval(value_expr, env)
            new_bindings[name] = value
        
        new_env = env.extend(new_bindings)
        return self.eval(body, new_env)
    
    def _eval_do(self, lst: List, env: Env) -> JSLValue:
        """Handle 'do' special form: ["do", expr1, expr2, ...]"""
        if len(lst) < 2:
            raise JSLError("'do' requires at least one expression")
        
        result = None
        for expr in lst[1:]:
            result = self.eval(expr, env)
        return result
    
    def _eval_quote(self, lst: List, env: Env) -> JSLValue:
        """Handle 'quote' or '@' special form: ["@", expr]"""
        if len(lst) != 2:
            raise JSLError("'quote' requires exactly 1 argument")
        
        result = lst[1]  # Return the argument without evaluating it
        
        # Check resources for quoted data
        if self.resources:
            self.resources.check_result(result)
        
        return result
    
    def _eval_try(self, lst: List, env: Env) -> JSLValue:
        """Handle 'try' special form: ["try", body, handler]"""
        if len(lst) != 3:
            raise JSLError("'try' requires exactly 2 arguments: body and handler")
        
        _, body, handler = lst
        
        try:
            return self.eval(body, env)
        except Exception as e:
            # Create error object
            error_obj = {
                "type": type(e).__name__,
                "message": str(e)
            }
            
            # Apply handler function to the error
            handler_func = self.eval(handler, env)
            if not isinstance(handler_func, Closure):
                raise JSLTypeError("'try' handler must be a function")
            
            return handler_func(self, [error_obj])
    
    def _eval_where(self, lst: List, env: Env) -> JSLValue:
        """
        Evaluate where form: ["where", collection, condition]
        
        Filters collection by evaluating condition for each item.
        The condition is evaluated with item's fields bound in the environment.
        """
        if len(lst) != 3:
            raise ValueError("where requires exactly 2 arguments: collection and condition")
        
        # Evaluate the collection
        collection = self.eval(lst[1], env)
        condition_expr = lst[2]
        
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
            # Extend environment with item's fields (if it's a dict)
            if isinstance(item, dict):
                # Extend the environment with all fields from the item
                # Also bind the item itself to '$' for accessing nested fields
                extended_env = env.extend({**item, '$': item})
            else:
                # For non-dict items, bind '$' to the item
                extended_env = env.extend({'$': item})
            
            # Evaluate condition in extended environment using standard eval
            try:
                if self.eval(condition_expr, extended_env):
                    result.append(item)
            except:
                # If condition evaluation fails, skip the item
                pass
        
        return result
    
    def _eval_transform(self, lst: List, env: Env) -> JSLValue:
        """
        Evaluate transform form: ["transform", data, operation1, operation2, ...]
        
        Applies a sequence of transformation operations to data.
        Each operation is evaluated with the item's fields in scope.
        """
        if len(lst) < 3:
            raise ValueError("transform requires at least data and one operation")
        
        # Evaluate the data
        data = self.eval(lst[1], env)
        
        # Get the operations
        operations = lst[2:]
        
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
                
                # Evaluate the operation to get the actual operation list
                operation = self.eval(operation_expr, extended_env)
                
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
                    # Field can be a string literal or evaluated from env
                    if not isinstance(field, str):
                        field = str(field) if field is not None else "null"
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
                        # Evaluate the function in the extended environment
                        func = self.eval(func_expr, extended_env)
                        # Apply the function
                        if isinstance(func, Closure):
                            result[field] = func(self, [item[field]])
                        elif callable(func):
                            result[field] = func(item[field])
                        else:
                            raise TypeError(f"Cannot apply non-function: {type(func).__name__}")
                else:
                    raise ValueError(f"Unknown transform operation: {op_type}")
                
                new_items.append(result)
            
            items = new_items
        
        return items if is_collection else items[0]
    
    def _eval_host(self, lst: List, env: Env) -> JSLValue:
        """Handle 'host' special form: ["host", command, arg1, ...]"""
        if len(lst) < 2:
            raise JSLError("'host' requires at least a command")
        
        # Evaluate all arguments
        command = self.eval(lst[1], env)
        args = [self.eval(arg, env) for arg in lst[2:]]
        
        if not isinstance(command, str):
            raise JSLTypeError("Host command must be a string")
        
        # Consume gas for host operation based on namespace
        # The command should have @ prefix for namespace-aware costing
        if self.resources:
            # Add @ prefix if not present for gas policy lookup
            gas_command = command if command.startswith('@') else f"@{command}"
            self.resources.consume_host_gas(gas_command)
        
        return self.host.dispatch(command, args)
    
    def _eval_function_call(self, lst: List, env: Env) -> JSLValue:
        """Handle regular function calls: [func, arg1, arg2, ...]"""
        if self.resources:
            self.resources.check_time()  # Check time limit periodically
            self.resources.consume_gas(GasCost.FUNCTION_CALL)
            self.resources.enter_call()  # Track stack depth
        
        try:
            func = self.eval(lst[0], env)
            args = [self.eval(arg, env) for arg in lst[1:]]
            
            if isinstance(func, Closure):
                result = func(self, args)
            elif callable(func):
                # Built-in function
                result = func(*args)
            else:
                raise JSLTypeError(f"Cannot call non-function value: {func}")
            
            # Check resources for the result
            if self.resources:
                self.resources.check_result(result)
            
            return result
        finally:
            if self.resources:
                self.resources.exit_call()  # Restore stack depth

    def _is_truthy(self, value: JSLValue) -> bool:
        """Determine if a value is truthy in JSL."""
        if value is None or value is False:
            return False
        elif isinstance(value, (list, dict, str)) and len(value) == 0:
            return False
        elif isinstance(value, (int, float)) and value == 0:
            return False
        else:
            return True
