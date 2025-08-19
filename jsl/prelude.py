"""
JSL Prelude - Built-in Functions

This module provides the standard library of functions available in every
JSL environment. These functions implement the computational foundation
of the language.
"""

import math
import json
import re
import hashlib
from typing import Any, List, Dict, Union, Callable
from .core import Env, JSLValue

# Prelude version - increment when prelude changes
PRELUDE_VERSION = "1.0.0"


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
        "max": lambda *args: max(args) if args else float('-inf'),
        "min": lambda *args: min(args) if args else float('inf'),
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
        "contains": _contains,
        "matches": _string_matches,
        
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
        "str-contains": _string_contains,
        "str-matches": _string_matches,
        "str-replace": _string_replace,
        "str-find-all": _string_find_all,
        
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
        
        # Path navigation (JSON path operations)
        "get-path": _get_path,
        "set-path": _set_path,
        "has-path": _has_path,
        "get-safe": _get_safe,
        "get-default": _get_default,
        
        # Query and transformation operations
        # "where" is now a special form in core.py and stack_special_forms.py
        # "transform" is now a special form in core.py and stack_special_forms.py
        # Transform operators - these return operation descriptors for transform
        "assign": lambda field, value: ["assign", field, value],
        "pick": lambda *fields: ["pick"] + list(fields),
        "omit": lambda *fields: ["omit"] + list(fields),
        "rename": lambda old_field, new_field: ["rename", old_field, new_field],
        "default": lambda field, value: ["default", field, value],
        "apply": lambda field, func: ["apply", field, func],
        # Collection operations
        "pluck": _pluck,
        "index-by": _index_by,
        
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
    
    # Create the prelude environment
    env = Env(prelude_bindings)
    
    # Generate prelude ID based on version and function names
    # This helps detect prelude compatibility issues
    func_names = sorted([k for k in prelude_bindings.keys() if not k.startswith('_')])
    prelude_content = f"v{PRELUDE_VERSION}:{','.join(func_names)}"
    prelude_id = hashlib.sha256(prelude_content.encode()).hexdigest()[:16]
    
    # Attach metadata to the environment
    env._prelude_id = prelude_id
    env._prelude_version = PRELUDE_VERSION
    env._is_prelude = True
    
    return env


def check_prelude_compatibility(env1: Env, env2: Env) -> tuple[bool, str]:
    """
    Check if two environments have compatible preludes.
    
    Returns:
        Tuple of (compatible, message)
    """
    if not hasattr(env1, '_prelude_id') or not hasattr(env2, '_prelude_id'):
        return (True, "No prelude metadata to compare")
    
    if env1._prelude_id == env2._prelude_id:
        return (True, f"Preludes match (v{env1._prelude_version})")
    else:
        return (False, f"Prelude mismatch: v{env1._prelude_version} vs v{env2._prelude_version}")


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


def _string_contains(string, substring):
    """Check if string contains substring."""
    return substring in string


def _string_matches(string, pattern, flags=0):
    """Check if string matches regex pattern.
    
    Args:
        string: The string to match against
        pattern: The regex pattern
        flags: Optional regex flags (0 for none, can use sum of re.IGNORECASE=2, re.MULTILINE=8, etc.)
    
    Returns:
        True if the pattern matches, False otherwise
    """
    try:
        return bool(re.search(pattern, string, flags))
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")


def _string_replace(string, pattern, replacement, count=0):
    """Replace regex pattern matches in string.
    
    Args:
        string: The string to process
        pattern: The regex pattern to find
        replacement: The replacement string (can include backreferences like \\1)
        count: Maximum number of replacements (0 for all)
    
    Returns:
        The string with replacements made
    """
    try:
        return re.sub(pattern, replacement, string, count=count)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")


def _string_find_all(string, pattern, flags=0):
    """Find all regex pattern matches in string.
    
    Args:
        string: The string to search
        pattern: The regex pattern
        flags: Optional regex flags
    
    Returns:
        List of all non-overlapping matches
    """
    try:
        matches = re.findall(pattern, string, flags)
        # Convert tuples to lists since JSL doesn't have tuples
        return [list(match) if isinstance(match, tuple) else match for match in matches]
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")


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


# Helper for applying functions (including closure dicts)
def _apply_function(func, args):
    """Apply a function (callable or closure dict) to arguments."""
    from .core import Closure, Evaluator
    
    if isinstance(func, Closure):
        # Recursive evaluator closure
        evaluator = Evaluator()
        return func(evaluator, args)
    elif isinstance(func, dict) and func.get('type') == 'closure':
        # Stack evaluator closure (dict representation)
        from .stack_evaluator import StackEvaluator
        from .compiler import compile_to_postfix
        
        params = func['params']
        body = func['body']
        closure_env = func.get('env', {})
        
        # Check arity
        if len(args) != len(params):
            raise ValueError(f"Arity mismatch: expected {len(params)} args, got {len(args)}")
        
        # Create new environment
        new_env = closure_env.copy()
        for param, arg in zip(params, args):
            new_env[param] = arg
        
        # Compile and evaluate body
        evaluator = StackEvaluator(env=new_env)
        body_jpn = compile_to_postfix(body)
        return evaluator.eval(body_jpn)
    elif callable(func):
        # Regular Python callable
        return func(*args)
    else:
        raise TypeError(f"Cannot apply non-function: {type(func).__name__}")

# Higher-order functions
def _map(func, lst):
    """Apply function to each element in list."""
    return [_apply_function(func, [item]) for item in lst]


def _filter(func, lst):
    """Filter list by predicate function."""
    return [item for item in lst if _apply_function(func, [item])]


def _reduce(func, lst, initial=None):
    """Reduce list to single value using function."""
    if not lst:
        return initial
    
    if initial is None:
        result = lst[0]
        items = lst[1:]
    else:
        result = initial
        items = lst
    
    for item in items:
        result = _apply_function(func, [result, item])
    return result


def _for_each(func, lst):
    """Apply function to each element for side effects."""
    for item in lst:
        _apply_function(func, [item])
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


# Path navigation functions
def _parse_path(path):
    """Parse a path string into components.
    
    Supports:
    - Dot notation: "user.address.city"
    - Array indices: "items.0.name" or "items[0].name"
    - Wildcards: "users.*.email"
    """
    if not isinstance(path, str):
        return [path]  # Single key access
    
    # Handle bracket notation for arrays
    path = re.sub(r'\[(\d+)\]', r'.\1', path)
    
    # Split by dots
    components = path.split('.')
    
    # Convert numeric strings to integers for array access
    result = []
    for comp in components:
        if comp.isdigit():
            result.append(int(comp))
        else:
            result.append(comp)
    
    return result


def _get_path(obj, path):
    """Get value from object using deep path.
    
    Args:
        obj: The object to navigate
        path: Path string like "user.address.city" or "items.0.name"
    
    Returns:
        The value at the path
    
    Raises:
        KeyError or IndexError if path doesn't exist
    """
    components = _parse_path(path)
    current = obj
    
    for comp in components:
        if comp == '*':
            # Wildcard - return all values
            if isinstance(current, dict):
                return list(current.values())
            elif isinstance(current, list):
                return current
            else:
                raise TypeError(f"Cannot apply wildcard to {type(current).__name__}")
        elif isinstance(current, dict):
            if comp not in current:
                raise KeyError(f"Key '{comp}' not found in path")
            current = current[comp]
        elif isinstance(current, list):
            if not isinstance(comp, int):
                raise TypeError(f"List index must be integer, got '{comp}'")
            if comp < 0 or comp >= len(current):
                raise IndexError(f"Index {comp} out of range")
            current = current[comp]
        else:
            raise TypeError(f"Cannot navigate into {type(current).__name__}")
    
    return current


def _set_path(obj, path, value):
    """Set value in object at deep path (returns new object).
    
    Args:
        obj: The object to modify
        path: Path string like "user.address.city"
        value: The value to set
    
    Returns:
        New object with value set at path
    """
    components = _parse_path(path)
    
    if not components:
        return value
    
    # Deep copy the object to avoid mutation
    import copy
    result = copy.deepcopy(obj) if obj is not None else {}
    
    # Navigate to parent and set the value
    current = result
    for comp in components[:-1]:
        if isinstance(current, dict):
            if comp not in current:
                # Auto-create intermediate objects
                current[comp] = {}
            current = current[comp]
        elif isinstance(current, list):
            if not isinstance(comp, int):
                raise TypeError(f"List index must be integer, got '{comp}'")
            if comp < 0 or comp >= len(current):
                raise IndexError(f"Index {comp} out of range")
            current = current[comp]
        else:
            raise TypeError(f"Cannot navigate into {type(current).__name__}")
    
    # Set the final value
    last_comp = components[-1]
    if isinstance(current, dict):
        current[last_comp] = value
    elif isinstance(current, list):
        if not isinstance(last_comp, int):
            raise TypeError(f"List index must be integer, got '{last_comp}'")
        if last_comp < 0 or last_comp >= len(current):
            raise IndexError(f"Index {last_comp} out of range")
        current[last_comp] = value
    else:
        raise TypeError(f"Cannot set value in {type(current).__name__}")
    
    return result


def _has_path(obj, path):
    """Check if path exists in object.
    
    Args:
        obj: The object to check
        path: Path string like "user.address.city"
    
    Returns:
        True if path exists, False otherwise
    """
    try:
        _get_path(obj, path)
        return True
    except (KeyError, IndexError, TypeError):
        return False


def _get_safe(obj, path, default=None):
    """Get value from object using path, returning default if path doesn't exist.
    
    Args:
        obj: The object to navigate
        path: Path string like "user.address.city"
        default: Value to return if path doesn't exist
    
    Returns:
        The value at the path or default
    """
    try:
        return _get_path(obj, path)
    except (KeyError, IndexError, TypeError):
        return default


def _get_default(obj, path, default):
    """Alias for get-safe with explicit default parameter."""
    return _get_safe(obj, path, default)


# Query and transformation operations
# Note: 'where' is a special form in core.py and stack_special_forms.py
# It uses the standard JSL evaluator with extended environment
def _pluck(collection, field):
    """Extract single field from each item in collection.
    
    Args:
        collection: List of objects
        field: Field to extract
    
    Returns:
        List of field values
    """
    if not isinstance(collection, list):
        raise TypeError(f"pluck requires a list, got {type(collection).__name__}")
    
    result = []
    for item in collection:
        if isinstance(item, dict) and field in item:
            result.append(item[field])
        elif "." in field:
            try:
                result.append(_get_path(item, field))
            except (KeyError, IndexError, TypeError):
                result.append(None)
        else:
            result.append(None)
    
    return result


def _index_by(collection, field):
    """Convert list to keyed object using field values as keys.
    
    Args:
        collection: List of objects
        field: Field to use as key
    
    Returns:
        Dict with field values as keys
    """
    if not isinstance(collection, list):
        raise TypeError(f"index-by requires a list, got {type(collection).__name__}")
    
    result = {}
    for item in collection:
        if isinstance(item, dict) and field in item:
            key = item[field]
            if isinstance(key, (str, int, float, bool)):
                result[str(key)] = item
    
    return result


# Utility functions
def _range(*args):
    """Create a range of numbers."""
    return list(range(*args))


def _sort(lst, key_func=None, reverse=False):
    """Sort a list."""
    if key_func:
        return sorted(lst, key=lambda x: _apply_function(key_func, [x]), reverse=reverse)
    else:
        return sorted(lst, reverse=reverse)


def _group_by(key_func, lst):
    """Group list elements by key function."""
    groups = {}
    
    for item in lst:
        key = _apply_function(key_func, [item])
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
