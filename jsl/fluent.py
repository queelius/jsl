"""
JSL Fluent Python API

Provides a Pythonic way to build JSL expressions using method chaining
and operator overloading. Expressions are constructed as data structures
that can be passed to JSLRunner for execution.
"""

from typing import Any, List, Dict, Union, Optional
import json


class FluentExpression:
    """Base class for fluent JSL expression builders."""
    
    def __init__(self, expression: Any):
        self._expression = expression
    
    def to_jsl(self) -> Any:
        """Convert to JSL expression (list, dict, or primitive)."""
        return self._expression
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({json.dumps(self._expression)})"
    
    # Arithmetic operators
    def __add__(self, other):
        return FluentExpression(["+", self._expression, _unwrap(other)])
    
    def __radd__(self, other):
        return FluentExpression(["+", _unwrap(other), self._expression])
    
    def __sub__(self, other):
        return FluentExpression(["-", self._expression, _unwrap(other)])
    
    def __rsub__(self, other):
        return FluentExpression(["-", _unwrap(other), self._expression])
    
    def __mul__(self, other):
        return FluentExpression(["*", self._expression, _unwrap(other)])
    
    def __rmul__(self, other):
        return FluentExpression(["*", _unwrap(other), self._expression])
    
    def __truediv__(self, other):
        return FluentExpression(["/", self._expression, _unwrap(other)])
    
    def __rtruediv__(self, other):
        return FluentExpression(["/", _unwrap(other), self._expression])
    
    def __mod__(self, other):
        return FluentExpression(["mod", self._expression, _unwrap(other)])
    
    def __rmod__(self, other):
        return FluentExpression(["mod", _unwrap(other), self._expression])
    
    # Comparison operators
    def __eq__(self, other):
        return FluentExpression(["=", self._expression, _unwrap(other)])
    
    def __ne__(self, other):
        return FluentExpression(["not", ["=", self._expression, _unwrap(other)]])
    
    def __lt__(self, other):
        return FluentExpression(["<", self._expression, _unwrap(other)])
    
    def __le__(self, other):
        return FluentExpression(["<=", self._expression, _unwrap(other)])
    
    def __gt__(self, other):
        return FluentExpression([">", self._expression, _unwrap(other)])
    
    def __ge__(self, other):
        return FluentExpression([">=", self._expression, _unwrap(other)])
    
    # Logical operators
    def __and__(self, other):
        return FluentExpression(["and", self._expression, _unwrap(other)])
    
    def __or__(self, other):
        return FluentExpression(["or", self._expression, _unwrap(other)])
    
    def __invert__(self):
        return FluentExpression(["not", self._expression])
    
    # Collection methods
    def map(self, func):
        """Apply function to each element."""
        return FluentExpression(["map", _unwrap(func), self._expression])
    
    def filter(self, predicate):
        """Filter elements based on predicate."""
        return FluentExpression(["filter", _unwrap(predicate), self._expression])
    
    def reduce(self, func, initial=None):
        """Reduce collection with function."""
        if initial is None:
            return FluentExpression(["reduce", _unwrap(func), self._expression])
        else:
            return FluentExpression(["reduce", _unwrap(func), _unwrap(initial), self._expression])
    
    def get(self, key, default=None):
        """Get value from object/array."""
        if default is None:
            return FluentExpression(["get", self._expression, _unwrap(key)])
        else:
            return FluentExpression(["get", self._expression, _unwrap(key), _unwrap(default)])
    
    def has(self, key):
        """Check if object/array has key."""
        return FluentExpression(["has", self._expression, _unwrap(key)])
    
    def keys(self):
        """Get keys of object."""
        return FluentExpression(["keys", self._expression])
    
    def values(self):
        """Get values of object."""
        return FluentExpression(["values", self._expression])
    
    def length(self):
        """Get length of collection."""
        return FluentExpression(["length", self._expression])
    
    def first(self):
        """Get first element."""
        return FluentExpression(["first", self._expression])
    
    def rest(self):
        """Get all but first element."""
        return FluentExpression(["rest", self._expression])
    
    def concat(self, *others):
        """Concatenate with other collections."""
        args = [self._expression] + [_unwrap(other) for other in others]
        return FluentExpression(["concat"] + args)
    
    # String methods
    def str_concat(self, *others):
        """Concatenate strings."""
        args = [self._expression] + [_unwrap(other) for other in others]
        return FluentExpression(["str-concat"] + args)
    
    def str_split(self, delimiter):
        """Split string by delimiter."""
        return FluentExpression(["str-split", self._expression, _unwrap(delimiter)])
    
    def str_contains(self, substring):
        """Check if string contains substring."""
        return FluentExpression(["str-contains", self._expression, _unwrap(substring)])
    
    def str_upper(self):
        """Convert to uppercase."""
        return FluentExpression(["str-upper", self._expression])
    
    def str_lower(self):
        """Convert to lowercase."""
        return FluentExpression(["str-lower", self._expression])


class ExpressionBuilder:
    """Expression builder for function calls and operations."""
    
    def __getattr__(self, name: str):
        """Dynamic method creation for JSL functions."""
        def builder(*args, **kwargs):
            # Convert function name (Python convention) to JSL convention
            jsl_name = name.replace('_', '-')
            jsl_args = [_unwrap(arg) for arg in args]
            
            # Handle keyword arguments as object
            if kwargs:
                jsl_args.append({f"@{k}": _unwrap(v) for k, v in kwargs.items()})
            
            return FluentExpression([jsl_name] + jsl_args)
        
        return builder
    
    # Core JSL functions with explicit implementations
    def add(self, *args):
        """Addition: ['+', ...args]"""
        return FluentExpression(["+"] + [_unwrap(arg) for arg in args])
    
    def subtract(self, *args):
        """Subtraction: ['-', ...args]"""
        return FluentExpression(["-"] + [_unwrap(arg) for arg in args])
    
    def multiply(self, *args):
        """Multiplication: ['*', ...args]"""
        return FluentExpression(["*"] + [_unwrap(arg) for arg in args])
    
    def divide(self, *args):
        """Division: ['/', ...args]"""
        return FluentExpression(["/"] + [_unwrap(arg) for arg in args])
    
    def equals(self, *args):
        """Equality: ['=', ...args]"""
        return FluentExpression(["="] + [_unwrap(arg) for arg in args])
    
    def less_than(self, a, b):
        """Less than: ['<', a, b]"""
        return FluentExpression(["<", _unwrap(a), _unwrap(b)])
    
    def greater_than(self, a, b):
        """Greater than: ['>', a, b]"""
        return FluentExpression([">", _unwrap(a), _unwrap(b)])
    
    def if_(self, condition, then_expr, else_expr=None):
        """Conditional: ['if', condition, then, else]"""
        if else_expr is None:
            return FluentExpression(["if", _unwrap(condition), _unwrap(then_expr)])
        else:
            return FluentExpression(["if", _unwrap(condition), _unwrap(then_expr), _unwrap(else_expr)])
    
    def let(self, bindings, body):
        """Let binding: ['let', bindings, body]"""
        if isinstance(bindings, dict):
            # Convert dict to JSL binding format
            jsl_bindings = [[k, _unwrap(v)] for k, v in bindings.items()]
        else:
            jsl_bindings = _unwrap(bindings)
        return FluentExpression(["let", jsl_bindings, _unwrap(body)])
    
    def do(self, *expressions):
        """Sequential execution: ['do', ...expressions]"""
        return FluentExpression(["do"] + [_unwrap(expr) for expr in expressions])
    
    def lambda_(self, params, body):
        """Lambda function: ['lambda', params, body]"""
        if isinstance(params, str):
            params = [params]
        return FluentExpression(["lambda", params, _unwrap(body)])
    
    def def_(self, name, value):
        """Definition: ['def', name, value]"""
        return FluentExpression(["def", name, _unwrap(value)])
    
    def quote(self, expr):
        """Quote: ['@', expr]"""
        return FluentExpression(["@", expr])
    
    def list(self, *items):
        """Create list: ['@', [items...]]"""
        return FluentExpression(["@", [_unwrap(item) for item in items]])
    
    def object(self, **kwargs):
        """Create object: {key: value, ...}"""
        return FluentExpression({f"@{k}": _unwrap(v) for k, v in kwargs.items()})
    
    def string(self, value: str):
        """Create string literal: '@value'"""
        return FluentExpression(f"@{value}")
    
    def map(self, func, collection):
        """Map function over collection."""
        return FluentExpression(["map", _unwrap(func), _unwrap(collection)])
    
    def filter(self, predicate, collection):
        """Filter collection with predicate."""
        return FluentExpression(["filter", _unwrap(predicate), _unwrap(collection)])
    
    def reduce(self, func, initial, collection):
        """Reduce collection with function."""
        return FluentExpression(["reduce", _unwrap(func), _unwrap(initial), _unwrap(collection)])
    
    def get(self, obj, key, default=None):
        """Get value from object."""
        if default is None:
            return FluentExpression(["get", _unwrap(obj), _unwrap(key)])
        else:
            return FluentExpression(["get", _unwrap(obj), _unwrap(key), _unwrap(default)])
    
    def host(self, command, *args):
        """Host command: ['host', command, ...args]"""
        return FluentExpression(["host", f"@{command}"] + [_unwrap(arg) for arg in args])


class VariableBuilder:
    """Variable builder for creating variable references."""
    
    def __getattr__(self, name: str):
        """Create variable reference."""
        return FluentExpression(name)
    
    def __getitem__(self, name: str):
        """Alternative syntax: V['variable-name']"""
        return FluentExpression(name)


def _unwrap(value: Any) -> Any:
    """Unwrap FluentExpression objects to their JSL representation."""
    if isinstance(value, FluentExpression):
        return value.to_jsl()
    else:
        # Don't make assumptions about string handling - let users be explicit
        # with literal() function or @ prefix when needed
        return value


# Global instances for easy import
E = ExpressionBuilder()
V = VariableBuilder()


# Convenience functions
def literal(value: Any) -> FluentExpression:
    """
    Create a literal value expression (quoted).
    
    This prevents evaluation of the value and treats it as literal data.
    
    Examples:
        literal("hello") -> "@hello" (string literal)
        literal([1, 2, 3]) -> ["@", [1, 2, 3]] (list literal)
        literal(42) -> 42 (numbers are already literal)
    """
    if isinstance(value, str):
        return FluentExpression(f"@{value}")
    elif isinstance(value, (list, dict)):
        return FluentExpression(["@", value])
    else:
        # Numbers, booleans, null are already literals
        return FluentExpression(value)


def var(name: str) -> FluentExpression:
    """Create a variable reference."""
    return FluentExpression(name)


def expr(jsl_expression: Any) -> FluentExpression:
    """Wrap existing JSL expression in fluent interface."""
    return FluentExpression(jsl_expression)


# Pipeline utilities
class Pipeline:
    """Helper for building complex pipelines."""
    
    def __init__(self, initial_value):
        self.value = FluentExpression(_unwrap(initial_value))
    
    def pipe(self, func):
        """Apply function to current value."""
        if callable(func):
            self.value = func(self.value)
        else:
            # Assume it's a FluentExpression representing a function
            self.value = FluentExpression([_unwrap(func), self.value.to_jsl()])
        return self
    
    def result(self):
        """Get the final pipeline result."""
        return self.value


def pipeline(initial_value):
    """Create a new pipeline starting with initial_value."""
    return Pipeline(initial_value)


# Export commonly used functions
__all__ = [
    'E', 'V', 'FluentExpression', 'ExpressionBuilder', 'VariableBuilder',
    'literal', 'var', 'expr', 'pipeline', 'Pipeline'
]