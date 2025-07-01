"""
JSL Prelude Environment

Contains the built-in functions and operations that form the computational
foundation of JSL. These functions are available in all JSL environments
but are not serialized with user code.
"""

from __future__ import annotations
import math
from typing import Any
from .core import Env, prelude, Closure

def eval_closure_or_builtin(fn, args):
    """
    Universal function call interface for JSL closures and built-ins.
    
    This function solves the fundamental challenge of making JSL closures
    work seamlessly with built-in higher-order functions like map and filter.
    
    PROBLEM: When a JSL closure is created, it captures its lexical 
    environment. However, that environment might not chain back to the
    prelude, especially for closures created in nested scopes or if the
    global prelude instance changes.
    
    SOLUTION: At call time, ensure the closure's captured environment chain
    ultimately links to the current global prelude. This is done by finding
    the highest-level user environment in the closure's captured chain and
    setting its parent to the current prelude if it's not already linked.
    
    This approach maintains several important properties:
    1. **Lexical Correctness**: Original variable bindings from the full captured chain are preserved.
    2. **Built-in Access**: All closures can access primitive functions via the current prelude.
    3. **Performance**: Environment chain modification is done when necessary.
    4. **Serialization Safety**: Only user bindings are ever serialized with closures.
    
    Args:
        fn: Function to call (JSL Closure or Python callable)
        args: List of arguments to pass to the function
        
    Returns:
        Result of calling fn with args
        
    Raises:
        TypeError: If fn is not callable or has arity mismatch
    """
    global prelude  # Access the global prelude
    
    if isinstance(fn, Closure):
        if len(args) != len(fn.params):
            raise TypeError(f"Arity mismatch: expected {len(fn.params)}, got {len(args)}")
        
        captured_env = fn.env
        
        # Ensure the captured_env's chain links to the current global prelude.
        # This is important if the prelude instance has changed since closure creation,
        # or if the closure was defined in an environment not initially linked to the prelude.
        if prelude is not None:
            # Check if the current global prelude is already an ancestor of captured_env.
            env_chain_iterator = captured_env
            highest_user_env_in_chain = None # Will store the topmost user env in the captured_env's chain.
            is_already_linked_to_current_prelude = False

            while env_chain_iterator is not None:
                if env_chain_iterator is prelude:
                    is_already_linked_to_current_prelude = True
                    break
                highest_user_env_in_chain = env_chain_iterator
                env_chain_iterator = env_chain_iterator.parent
            
            if not is_already_linked_to_current_prelude:
                # The end of the chain was reached without finding the current prelude.
                # `highest_user_env_in_chain` now holds the top-most environment in the original chain
                # (or its highest ancestor that wasn't the current prelude).
                # Its .parent is currently None or an old/different prelude.
                # We need to link this topmost user environment to the current `prelude`.
                if highest_user_env_in_chain is not None and highest_user_env_in_chain is not prelude:
                    highest_user_env_in_chain.parent = prelude
                # If highest_user_env_in_chain is None, captured_env was None (which is invalid for a Closure).
                # If highest_user_env_in_chain is prelude, is_already_linked_to_current_prelude would be true.
        
        # Now, captured_env (which is fn.env) is part of a chain
        # that should correctly resolve to the current `prelude` if prelude is not None.
        from .evaluator import eval_expr
        call_env = captured_env.extend(dict(zip(fn.params, args)))
        return eval_expr(fn.body, call_env)
    elif callable(fn):
        return fn(*args)
    else:
        raise TypeError(f"Cannot call non-callable value: {fn!r}")

def reduce_jsl(fn, lst, init=None):
    """
    JSL-compatible reduce operation supporting both closures and built-ins.
    
    Implements the standard functional programming reduce operation
    (also known as fold) with proper support for JSL closures.
    
    Args:
        fn: Binary function to apply (closure or built-in)
        lst: List to reduce
        init: Initial value (optional)
        
    Returns:
        Single value produced by applying fn to all elements
        
    Mathematical Definition:
        reduce(f, [x1, x2, ..., xn], init) = f(...f(f(init, x1), x2)..., xn)
    """
    if not lst:
        return init
    
    if init is None:
        result = lst[0]
        items = lst[1:]
    else:
        result = init
        items = lst
    
    for item in items:
        result = eval_closure_or_builtin(fn, [result, item])
    
    return result

def make_prelude() -> Env:
    """
    Create the foundational environment containing all built-in functions.
    
    The prelude serves as the computational foundation of JSL. It contains
    all primitive operations needed for computation but is never serialized
    or transmitted over the wire.
    """
    global prelude  # Declare that we'll modify the global prelude
    
    # Create the prelude environment with all built-in functions
    prelude_bindings = {
        # =================================================================
        # DATA CONSTRUCTORS
        # =================================================================
        # These provide the fundamental data types for JSL programs
        
        "list": lambda *args: list(args),
       
        # =================================================================
        # LIST OPERATIONS
        # =================================================================
        # Comprehensive list manipulation functions following functional
        # programming principles (immutability, composability)
        
        "append": lambda lst, item: lst + [item] if isinstance(lst, list) else [item],
        "prepend": lambda item, lst: [item] + lst if isinstance(lst, list) else [item],
        "concat": lambda *lsts: [item for lst in lsts for item in (lst if isinstance(lst, list) else [])],
        "first": lambda lst: lst[0] if lst else None,
        "rest": lambda lst: lst[1:] if len(lst) > 1 else [],
        "nth": lambda lst, i: lst[i] if isinstance(lst, list) and 0 <= i < len(lst) else None,
        "length": len,
        "empty?": lambda x: len(x) == 0 if hasattr(x, '__len__') else True,
        "slice": lambda lst, start, end=None: lst[start:end] if isinstance(lst, (list, str)) else [],
        "reverse": lambda lst: lst[::-1] if isinstance(lst, (list, str)) else lst,
        "contains?": lambda lst, item: item in lst if hasattr(lst, '__contains__') else False,
        "index": lambda lst, item: lst.index(item) if item in lst else -1,
        
        # =================================================================
        # DICTIONARY OPERATIONS  
        # =================================================================
        # Immutable dictionary operations supporting functional programming
        # patterns and data transformation pipelines
        
        "get": lambda d, k, default=None: d.get(k, default) if isinstance(d, dict) else default,
        "set": lambda d, k, v: {**d, k: v} if isinstance(d, dict) else {},
        "keys": lambda d: list(d.keys()) if isinstance(d, dict) else [],
        "values": lambda d: list(d.values()) if isinstance(d, dict) else [],
        "merge": lambda *dicts: {k: v for d in dicts if isinstance(d, dict) for k, v in d.items()},
        "has-key?": lambda d, k: k in d if isinstance(d, dict) else False,
        
        # =================================================================
        # N-ARITY ARITHMETIC
        # =================================================================
        # Mathematical operations supporting variable numbers of arguments
        # for more natural expression and reduced intermediate allocations
        
        "+": lambda *args: sum(args) if args else 0,
        "-": lambda *args: args[0] - sum(args[1:]) if len(args) > 1 else (-args[0] if args else 0),
        "*": lambda *args: math.prod(args) if args else 1,
        "/": lambda *args: (
            # Case: 1 argument
            (
                (lambda val: 1 / val if val != 0 else (_ for _ in ()).throw(ZeroDivisionError("division by zero")))(args[0])
            ) if len(args) == 1 else (
                # Case: >1 argument
                (lambda num, *denoms_tuple: (
                    (lambda prod_denoms: num / prod_denoms if prod_denoms != 0 else (_ for _ in ()).throw(ZeroDivisionError("division by zero")))(math.prod(denoms_tuple))
                ))(args[0], *args[1:])
            ) if len(args) > 1 else (
                # Case: 0 arguments
                (_ for _ in ()).throw(TypeError("/ requires at least one argument"))
            )
        ),
        "mod": lambda a, b: a % b if b != 0 else 0,
        "pow": lambda a, b: pow(a, b),
        
        # =================================================================
        # N-ARITY COMPARISONS
        # =================================================================
        # Chained comparisons supporting mathematical notation like a < b < c
        
        "=": lambda *args: all(x == args[0] for x in args[1:]) if len(args) > 1 else True,
        "<": lambda *args: all(args[i] < args[i+1] for i in range(len(args)-1)) if len(args) > 1 else True,
        ">": lambda *args: all(args[i] > args[i+1] for i in range(len(args)-1)) if len(args) > 1 else True,
        "<=": lambda *args: all(args[i] <= args[i+1] for i in range(len(args)-1)) if len(args) > 1 else True,
        ">=": lambda *args: all(args[i] >= args[i+1] for i in range(len(args)-1)) if len(args) > 1 else True,
        
        # =================================================================
        # N-ARITY LOGIC
        # =================================================================
        # Logical operations with short-circuiting behavior
        
        "and": lambda *args: all(args),
        "or": lambda *args: any(args),
        "not": lambda x: not x,
        
        # =================================================================
        # TYPE PREDICATES
        # =================================================================
        # Essential for wire format validation and dynamic type checking
        
        "null?": lambda x: x is None,
        "bool?": lambda x: isinstance(x, bool),
        "number?": lambda x: isinstance(x, (int, float)),
        "string?": lambda x: isinstance(x, str),
        "list?": lambda x: isinstance(x, list),
        "dict?": lambda x: isinstance(x, dict),
        "callable?": callable,
        
        # =================================================================
        # STRING OPERATIONS
        # =================================================================
        # String manipulation functions for text processing and formatting
        
        "str-concat": lambda *args: ''.join(str(arg) for arg in args),
        "str-split": lambda s, sep=' ': s.split(sep) if isinstance(s, str) else [],
        "str-join": lambda lst, sep='': sep.join(str(x) for x in lst),
        "str-length": lambda s: len(s) if isinstance(s, str) else 0,
        "str-upper": lambda s: s.upper() if isinstance(s, str) else s,
        "str-lower": lambda s: s.lower() if isinstance(s, str) else s,
        
        # =================================================================
        # HIGHER-ORDER FUNCTIONS
        # =================================================================
        # The cornerstone of functional programming, enabling composition
        # and abstraction. These work seamlessly with JSL closures through
        # the eval_closure_or_builtin integration layer.
        
        "map": lambda fn, lst: [eval_closure_or_builtin(fn, [item]) for item in lst] if isinstance(lst, list) else [],
        "filter": lambda fn, lst: [item for item in lst if eval_closure_or_builtin(fn, [item])] if isinstance(lst, list) else [],
        "reduce": reduce_jsl,
        "apply": lambda fn, args: eval_closure_or_builtin(fn, args) if isinstance(args, list) else None,
        
        # =================================================================
        # MATHEMATICAL FUNCTIONS
        # =================================================================
        # Extended mathematical operations for scientific computing
        
        "min": lambda *args: min(args) if args else None,
        "max": lambda *args: max(args) if args else None,
        "abs": abs,
        "round": round,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "log": math.log,
        "exp": math.exp,
        
        # =================================================================
        # TYPE CONVERSION
        # =================================================================
        # Safe type conversion functions with reasonable defaults
        
        "to-string": str,
        "to-number": lambda x: float(x) if str(x).replace('.','').replace('-','').isdigit() else 0,
        "type-of": lambda x: type(x).__name__,
        
        # =================================================================
        # I/O OPERATIONS
        # =================================================================
        # Basic I/O functions (can be customized or restricted in sandboxed
        # environments)
        
        "print": print,
        "error": lambda msg: (_ for _ in ()).throw(RuntimeError(str(msg))),
    }
    # Create the new Env instance using the refactored class
    new_prelude_env = Env(prelude_bindings, parent=None) # Explicitly parent=None for prelude
    prelude = new_prelude_env
    return new_prelude_env
