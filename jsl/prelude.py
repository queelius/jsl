"""
JSL Prelude - Built-in Functions

This module provides the standard library of functions available in every
JSL environment. These functions implement the computational foundation
of the language.
"""

import math
import json
from typing import Any, List, Dict, Union, Callable
from .core import Env, JSLValue


def make_prelude() -> Env:
    """
    Create the standard JSL prelude environment.
    
    This environment contains all the built-in functions that form
    the computational foundation of JSL.
    """
    prelude_bindings = {
        # Arithmetic operations
        "+": _add,
        "-": _subtract,
        "*": _multiply,
        "/": _divide,
        "%": _modulo,
        "abs": abs,
        "max": max,
        "min": min,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "sqrt": math.sqrt,
        "pow": math.pow,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "gcd": math.gcd,
        "lcm": lambda a, b: abs(a * b) // math.gcd(a, b) if a and b else 0,
        "comb": math.comb,
        "perm": math.perm,
        "mod": _modulo,
        
        # Comparison operations
        "=": _equals,
        "!=": _not_equals,
        "<": _less_than,
        "<=": _less_than_or_equal,
        ">": _greater_than,
        ">=": _greater_than_or_equal,
        
        # Logical operations
        "and": _logical_and,
        "or": _logical_or,
        "not": _logical_not,
        
        # String operations
        "str-concat": _string_concat,
        "str-length": len,
        "str-upper": lambda s: s.upper() if isinstance(s, str) else s,
        "str-lower": lambda s: s.lower() if isinstance(s, str) else s,
        "str-split": _string_split,
        "str-join": _string_join,
        "str-slice": _string_slice,
        
        # List operations
        "list": _make_list,
        "length": len,
        "first": _first,
        "rest": _rest,
        "last": _last,
        "cons": _cons,
        "append": _append,
        "concat": _concat_lists,
        "reverse": _reverse,
        "slice": _slice,
        "contains": _contains,
        "index-of": _index_of,
        
        # Higher-order functions
        "map": _map,
        "filter": _filter,
        "reduce": _reduce,
        "for-each": _for_each,
        "any": _any,
        "all": _all,
        
        # Object operations
        "get": _get,
        "set": _set,
        "has": _has,
        "keys": _keys,
        "values": _values,
        "items": _items,
        "merge": _merge,
        
        # Type checking
        "is-null": lambda x: x is None,
        "is-bool": lambda x: isinstance(x, bool),
        "is-num": lambda x: isinstance(x, (int, float)),
        "is-str": lambda x: isinstance(x, str),
        "is-list": lambda x: isinstance(x, list),
        "is-obj": lambda x: isinstance(x, dict),
        "is-func": callable,
        
        # Utility functions
        "range": _range,
        "sort": _sort,
        "group-by": _group_by,
        "unique": _unique,
        "zip": _zip,
        "enumerate": _enumerate,
        
        # JSON operations
        "json-parse": json.loads,
        "json-stringify": _json_stringify,
        
        # Math constants
        "pi": math.pi,
        "e": math.e,
    }
    
    return Env(prelude_bindings)


# Arithmetic functions
def _add(*args):
    """Add numbers or concatenate strings/lists."""
    if not args:
        return 0
    
    result = args[0]
    for arg in args[1:]:
        if isinstance(result, str) and isinstance(arg, str):
            result = result + arg
        elif isinstance(result, list) and isinstance(arg, list):
            result = result + arg
        elif isinstance(result, (int, float)) and isinstance(arg, (int, float)):
            result = result + arg
        else:
            raise TypeError(f"Cannot add {type(result).__name__} and {type(arg).__name__}")
    
    return result


def _subtract(*args):
    """Subtract numbers."""
    if not args:
        return 0
    if len(args) == 1:
        return -args[0]
    
    result = args[0]
    for arg in args[1:]:
        result = result - arg
    return result


def _multiply(*args):
    """Multiply numbers."""
    if not args:
        return 1
    
    result = args[0]
    for arg in args[1:]:
        result = result * arg
    return result


def _divide(*args):
    """Divide numbers."""
    if len(args) != 2:
        raise ValueError("Division requires exactly 2 arguments")
    
    a, b = args
    if b == 0:
        raise ZeroDivisionError("Division by zero")
    return a / b


def _modulo(a, b):
    """Modulo operation."""
    return a % b


# Comparison functions
def _equals(*args):
    """Check if all arguments are equal."""
    if len(args) < 2:
        return True
    
    first = args[0]
    return all(arg == first for arg in args[1:])


def _not_equals(a, b):
    """Check if two values are not equal."""
    return a != b


def _less_than(a, b):
    """Check if a < b."""
    return a < b


def _less_than_or_equal(a, b):
    """Check if a <= b."""
    return a <= b


def _greater_than(a, b):
    """Check if a > b."""
    return a > b


def _greater_than_or_equal(a, b):
    """Check if a >= b."""
    return a >= b


# Logical functions
def _logical_and(*args):
    """Logical AND of all arguments."""
    return all(args)


def _logical_or(*args):
    """Logical OR of all arguments."""
    return any(args)


def _logical_not(x):
    """Logical NOT."""
    return not x


# String functions
def _string_concat(*args):
    """Concatenate strings."""
    return ''.join(str(arg) for arg in args)


def _string_split(string, delimiter=' '):
    """Split string by delimiter."""
    return string.split(delimiter)


def _string_join(delimiter, strings):
    """Join strings with delimiter."""
    return delimiter.join(strings)


def _string_slice(string, start, end=None):
    """Slice a string."""
    if end is None:
        return string[start:]
    return string[start:end]


# List functions
def _make_list(*args):
    """Create a list from arguments."""
    return list(args)


def _first(lst):
    """Get the first element of a list."""
    if not lst:
        return None
    return lst[0]


def _rest(lst):
    """Get all elements except the first."""
    if not lst:
        return []
    return lst[1:]


def _last(lst):
    """Get the last element of a list."""
    if not lst:
        return None
    return lst[-1]


def _cons(item, lst):
    """Add item to the front of a list."""
    return [item] + lst


def _append(lst, item):
    """Add item to the end of a list."""
    return lst + [item]


def _concat_lists(*lists):
    """Concatenate multiple lists."""
    result = []
    for lst in lists:
        result.extend(lst)
    return result


def _reverse(lst):
    """Reverse a list."""
    return list(reversed(lst))


def _slice(lst, start, end=None):
    """Slice a list."""
    if end is None:
        return lst[start:]
    return lst[start:end]


def _contains(lst, item):
    """Check if list contains item."""
    return item in lst


def _index_of(lst, item):
    """Find index of item in list."""
    try:
        return lst.index(item)
    except ValueError:
        return -1


# Higher-order functions
def _map(func, lst):
    """Apply function to each element in list."""
    from .core import Closure, Evaluator
    
    if isinstance(func, Closure):
        evaluator = Evaluator()
        return [func(evaluator, [item]) for item in lst]
    else:
        return [func(item) for item in lst]


def _filter(func, lst):
    """Filter list by predicate function."""
    from .core import Closure, Evaluator
    
    if isinstance(func, Closure):
        evaluator = Evaluator()
        return [item for item in lst if func(evaluator, [item])]
    else:
        return [item for item in lst if func(item)]


def _reduce(func, lst, initial=None):
    """Reduce list to single value using function."""
    from .core import Closure, Evaluator
    
    if not lst:
        return initial
    
    if isinstance(func, Closure):
        evaluator = Evaluator()
        if initial is None:
            result = lst[0]
            items = lst[1:]
        else:
            result = initial
            items = lst
        
        for item in items:
            result = func(evaluator, [result, item])
        return result
    else:
        if initial is None:
            result = lst[0]
            items = lst[1:]
        else:
            result = initial
            items = lst
        
        for item in items:
            result = func(result, item)
        return result


def _for_each(func, lst):
    """Apply function to each element for side effects."""
    from .core import Closure, Evaluator
    
    if isinstance(func, Closure):
        evaluator = Evaluator()
        for item in lst:
            func(evaluator, [item])
    else:
        for item in lst:
            func(item)
    
    return None


def _any(lst):
    """Check if any element is truthy."""
    return any(lst)


def _all(lst):
    """Check if all elements are truthy."""
    return all(lst)


# Object functions
def _get(obj, key, default=None):
    """Get value from object by key."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    elif isinstance(obj, list) and isinstance(key, int):
        try:
            return obj[key]
        except IndexError:
            return default
    else:
        return default


def _set(obj, key, value):
    """Set value in object (returns new object)."""
    if isinstance(obj, dict):
        result = obj.copy()
        result[key] = value
        return result
    elif isinstance(obj, list) and isinstance(key, int):
        result = obj.copy()
        if 0 <= key < len(result):
            result[key] = value
        return result
    else:
        raise TypeError(f"Cannot set key in {type(obj).__name__}")


def _has(obj, key):
    """Check if object has key."""
    if isinstance(obj, dict):
        return key in obj
    elif isinstance(obj, list) and isinstance(key, int):
        return 0 <= key < len(obj)
    else:
        return False


def _keys(obj):
    """Get keys from object."""
    if isinstance(obj, dict):
        return list(obj.keys())
    elif isinstance(obj, list):
        return list(range(len(obj)))
    else:
        return []


def _values(obj):
    """Get values from object."""
    if isinstance(obj, dict):
        return list(obj.values())
    elif isinstance(obj, list):
        return obj.copy()
    else:
        return []


def _items(obj):
    """Get key-value pairs from object."""
    if isinstance(obj, dict):
        return [[k, v] for k, v in obj.items()]
    elif isinstance(obj, list):
        return [[i, v] for i, v in enumerate(obj)]
    else:
        return []


def _merge(*objs):
    """Merge objects (later objects override earlier ones)."""
    result = {}
    for obj in objs:
        if isinstance(obj, dict):
            result.update(obj)
    return result


# Utility functions
def _range(*args):
    """Create a range of numbers."""
    return list(range(*args))


def _sort(lst, key_func=None, reverse=False):
    """Sort a list."""
    from .core import Closure, Evaluator
    
    if key_func and isinstance(key_func, Closure):
        evaluator = Evaluator()
        return sorted(lst, key=lambda x: key_func(evaluator, [x]), reverse=reverse)
    elif key_func:
        return sorted(lst, key=key_func, reverse=reverse)
    else:
        return sorted(lst, reverse=reverse)


def _group_by(key_func, lst):
    """Group list elements by key function."""
    from .core import Closure, Evaluator
    
    groups = {}
    
    if isinstance(key_func, Closure):
        evaluator = Evaluator()
        for item in lst:
            key = key_func(evaluator, [item])
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
    else:
        for item in lst:
            key = key_func(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
    
    return groups


def _unique(lst):
    """Remove duplicates from list (preserving order)."""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _zip(*lists):
    """Zip multiple lists together."""
    return [list(items) for items in zip(*lists)]


def _enumerate(lst):
    """Enumerate list items with indices."""
    return [[i, item] for i, item in enumerate(lst)]


def _json_stringify(obj, indent=None):
    """Convert object to JSON string."""
    return json.dumps(obj, indent=indent)
