"""
JSL (JSON Serializable Language) - A Network-Native Functional Language

JSL is a Lisp-like functional programming language designed from the ground up for 
network transmission and distributed computing. Unlike traditional languages that 
treat serialization as an afterthought, JSL makes wire-format compatibility a 
first-class design principle.

MOTIVATION AND DESIGN PHILOSOPHY
===============================

Modern distributed systems require seamless code mobility - the ability to send 
executable code across network boundaries, store it in databases, and reconstruct 
it in different runtime environments. Traditional approaches face fundamental 
challenges:

1. **Serialization Complexity**: Most languages require complex serialization 
   frameworks (pickle, protobuf, etc.) that are brittle, version-dependent, and 
   often insecure.

2. **Runtime Dependencies**: Serialized code often depends on specific runtime 
   versions, libraries, or execution contexts that may not be available on the 
   receiving end.

3. **Security Vulnerabilities**: Deserializing code often requires executing 
   arbitrary instructions, creating attack vectors.

4. **Platform Lock-in**: Serialization formats are often language-specific, 
   preventing cross-platform code sharing.

JSL solves these problems by making JSON the native representation of both data 
AND code. This creates several powerful properties:

THEORETICAL FOUNDATIONS
======================

**Homoiconicity**: Like classic Lisps, JSL code and data share the same 
representation. However, unlike S-expressions, JSL uses JSON - a universally 
supported, standardized format with existing tooling and security properties.

**Closure Serializability**: The most challenging aspect of code mobility is 
handling closures (functions that capture their lexical environment). JSL 
solves this by:
- Separating built-in primitives (non-serializable) from user code (serializable)
- Reconstructing closure environments by merging serialized user bindings with 
  a fresh prelude on the receiving end
- Using environment chaining to ensure closures always have access to built-ins

**Wire-Format Transparency**: Every JSL value can be serialized to JSON and 
reconstructed identically in any compliant runtime. This enables:
- Database storage of executable code
- HTTP transmission of functions
- Cross-language interoperability
- Audit trails of code execution

PRACTICAL APPLICATIONS
======================

1. **Distributed Computing**: Send computations to data rather than moving data 
   to computations
2. **Edge Computing**: Deploy code dynamically to edge nodes
3. **Database Functions**: Store and execute business logic directly in databases
4. **Microservices**: Share functional components across service boundaries
5. **Code as Configuration**: Express complex configurations as executable code
6. **Live Programming**: Update running systems by transmitting new code

IMPLEMENTATION ARCHITECTURE
===========================

The JSL runtime consists of three layers:

1. **Prelude Layer**: Non-serializable built-in functions (+, map, get, etc.) 
   that form the computational foundation
2. **User Layer**: Serializable functions and data defined by user programs
3. **Wire Layer**: JSON representation that can be transmitted and reconstructed

This separation ensures that transmitted code is always safe (contains no 
executable primitives) while remaining fully functional when reconstructed 
with a compatible prelude.

SECURITY MODEL
==============

JSL's security model is based on capability restriction:
- Transmitted code cannot contain arbitrary executable primitives
- All capabilities come from the receiving environment's prelude
- The prelude can be customized to provide only safe operations
- Code execution is deterministic and sandboxable

This makes JSL suitable for scenarios where traditional code mobility would 
be too dangerous, such as user-submitted code or cross-tenant execution.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Callable
import json, math, sys
import argparse, sys
import operator
import math
from functools import reduce
import hashlib

# ----------------------------------------------------------------------
# Runtime Data Structures
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Closure:
    """
    A closure represents a function with its captured lexical environment.
    
    In JSL, closures are first-class values that can be passed as arguments,
    returned from functions, and most importantly, serialized to JSON and
    reconstructed in different runtime environments.
    
    The environment (env) contains only user-defined bindings. Built-in
    functions are provided by the prelude and are automatically made
    available when the closure is reconstructed.
    
    This design enables true code mobility - closures can be:
    - Stored in databases
    - Transmitted over networks  
    - Cached in distributed systems
    - Executed in different processes/machines
    
    Theoretical Note: This implements the mathematical concept of a closure
    while maintaining the engineering requirement of serializability.
    """
    params: List[str]  # Parameter names
    body: Any          # Function body (JSL expression)
    env: "Env"         # Captured lexical environment (user bindings only)

class Env(dict):
    """
    Lexical environment with parent chaining for scope resolution.
    
    Environments now use content-based IDs for deterministic serialization
    and cleaner environment reference management.
    """
    
    def __init__(self, bindings: Dict[str, Any] | None = None, parent: "Env|None" = None):
        super().__init__(bindings or {})
        self.parent = parent
        self._id = None  # Computed lazily
    
    def lookup(self, name: str) -> Any:
        if name in self:
            return self[name]
        if self.parent:
            return self.parent.lookup(name)
        raise NameError(f"Unbound symbol: {name}")
    
    def extend(self, bindings: Dict[str, Any]) -> "Env":
        return Env(bindings, parent=self)
    
    def get_id(self) -> str:
        """Get content-based deterministic ID for this environment."""
        if self._id is None:
            # Create ID based on content, not memory address
            content = {
                "bindings": sorted(self.items()),
                "parent_id": self.parent.get_id() if self.parent else None
            }
            content_str = str(content)
            self._id = hashlib.md5(content_str.encode()).hexdigest()[:12]
        return self._id

# Global reference to the prelude for closure environment fixing
prelude = None

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
                # Assuming prelude environments are not parents of further user environments in this context.
                # `Closure.env` is documented to contain "user bindings only".
                highest_user_env_in_chain = env_chain_iterator
                env_chain_iterator = env_chain_iterator.parent
            
            if not is_already_linked_to_current_prelude:
                # The captured_env's chain does not (or no longer) lead to the current prelude.
                # `highest_user_env_in_chain` is the topmost environment in the captured_env's
                # original chain (it could be captured_env itself if it had no parent initially,
                # or its highest ancestor that wasn't the current prelude).
                # Its .parent is currently None or an old/different prelude.
                # We need to link this topmost user environment to the current `prelude`.
                if highest_user_env_in_chain is not None and highest_user_env_in_chain is not prelude:
                    # This modification makes the original captured_env structure now
                    # point to the current prelude, preserving its internal chain.
                    highest_user_env_in_chain.parent = prelude
                # If highest_user_env_in_chain is None, captured_env was None (which is invalid for a Closure).
                # If highest_user_env_in_chain is prelude, is_already_linked_to_current_prelude would be true.
        
        # Now, captured_env (which is fn.env) is part of a chain
        # that should correctly resolve to the current `prelude` if prelude is not None.
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
    prelude = Env({
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
        "/": lambda *args: args[0] / math.prod(args[1:]) if len(args) > 1 and all(x != 0 for x in args[1:]) else (1/args[0] if len(args) == 1 and args[0] != 0 else float('inf')),
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
    })
    
    return prelude

# ----------------------------------------------------------------------
# Evaluator
# ----------------------------------------------------------------------

def eval_expr(expr: Any, env: Env) -> Any:
    """
    Evaluate an expression in the given environment.
    
    JSL expressions are evaluated according to the following semantics:
    - Literals (numbers, strings, booleans, null) evaluate to themselves
    - Symbols are resolved through environment lookup
    - Lists represent either special forms or function application
    
    Special forms have specific evaluation rules and are not subject to
    normal function application semantics.
    """
    if isinstance(expr, str):
        if expr.startswith("@"):
            return expr[1:]  # String literal escape
        return env.lookup(expr)  # Symbol lookup
    
    if isinstance(expr, (int, float, bool)) or expr is None:
        return expr

    if not expr:
        raise ValueError("Empty list cannot be evaluated")

    head, *tail = expr

    if head == "dict":
        """
        Create a dictionary from key-value pairs.
        
        Args:
            ["dict", key1, value1, key2, value2, ...]
            
        Returns:
            A dictionary with the provided key-value pairs.
        """
        if len(tail) % 2 != 0:
            raise ValueError("dict expects an even number of arguments")
        return {eval_expr(tail[i], env): eval_expr(tail[i+1], env) for i in range(0, len(tail), 2)}

    # ---------- special forms ----------
    if head == "quote":            # ["quote", expr]
        if len(tail) != 1:
            raise ValueError("quote expects exactly one argument")
        return tail[0]

    if head == "def":              # ["def", name, expr]
        if len(tail) != 2:
            raise ValueError("def expects exactly two arguments")
        name, value_expr = tail
        if not isinstance(name, str):
            raise ValueError("def name must be a string")
        env[name] = None           # placeholder for self‑recursion
        value = eval_expr(value_expr, env)
        env[name] = value
        return value

    if head == "lambda":           # ["lambda", [params], body]
        if len(tail) != 2:
            raise ValueError("lambda expects exactly two arguments")
        params, body = tail
        if not isinstance(params, list) or not all(isinstance(p, str) for p in params):
            raise ValueError("lambda params must be a list of strings")
        return Closure(params, body, env)

    if head == "if":               # ["if", test, conseq, alt]
        if len(tail) != 3:
            raise ValueError("if expects exactly three arguments")
        test, conseq, alt = tail
        branch = conseq if eval_expr(test, env) else alt
        return eval_expr(branch, env)

    if head == "do":               # ["do", e1, e2, ...]
        result = None
        for sub in tail:
            result = eval_expr(sub, env)
        return result

    if head == "host":             # ["host", command_id, ...args]
        """
        Host command special form - reifies side effects as data.
        
        THEORETICAL FOUNDATION
        ======================
        
        The host form implements several key principles from programming
        language theory and distributed systems:
        
        1. **Effect Reification**: Instead of executing side effects directly,
           they are converted to data structures that describe the intended
           effect. This enables:
           - Effect inspection and auditing
           - Effect batching and optimization  
           - Effect denial and sandboxing
           - Effect logging and replay
        
        2. **Capability Security**: The host environment acts as a capability
           broker, deciding which operations to allow based on:
           - Security policies
           - Resource constraints
           - Trust relationships
           - Operational context
        
        3. **Algebraic Effects**: Host commands represent algebraic effects
           that can be:
           - Composed and combined
           - Handled by different interpreters
           - Transformed and optimized
           - Made subject to static analysis
        
        PRACTICAL APPLICATIONS
        ======================
        
        Host commands enable powerful distributed computing patterns:
        
        - **Secure Code Execution**: Untrusted code can request capabilities
          without being able to execute them directly
        - **Transparent Distribution**: The same JSL code can run locally
          or remotely with different host command handlers
        - **Effect Batching**: Multiple host commands can be collected and
          executed efficiently in batches
        - **Audit Trails**: All attempted side effects are visible as data
        - **Gradual Trust**: Different hosts can provide different subsets
          of capabilities based on trust level
        
        SECURITY MODEL
        ==============
        
        The host command model provides several security guarantees:
        
        1. **No Privilege Escalation**: Transmitted code cannot gain more
           capabilities than the host explicitly provides
        2. **Effect Visibility**: All side effects are explicit and inspectable
        3. **Capability Delegation**: Hosts can provide restricted versions
           of capabilities (e.g., file I/O limited to specific directories)
        4. **Fail-Safe Defaults**: Unknown commands are safely ignored or
           rejected rather than causing errors
        
        Args:
            command_id: String identifying the requested host capability
            *args: Arguments for the host command (pre-evaluated to pure values)
            
        Returns:
            ["host", command_id, *evaluated_args] - A data structure describing
            the requested effect, to be interpreted by the host environment
            
        Examples:
            ["host", "file/read", "/path/to/file"]
            ["host", "http/get", "https://api.example.com/data"]
            ["host", "db/query", "SELECT * FROM users WHERE id = ?", 123]
            ["host", "log/info", "Processing completed successfully"]
        """
        if not tail:
            raise ValueError("host command requires at least a command_id")
        
        command_id = tail[0]
        args = tail[1:] if len(tail) > 1 else []
        
        # Validate command_id is a string
        if not isinstance(command_id, str):
            raise TypeError(f"host command_id must be a string, got {type(command_id).__name__}")
        
        # Evaluate all arguments to pure values
        # This ensures no unevaluated code can escape to the host
        try:
            evaluated_args = [eval_expr(arg, env) for arg in args]
        except Exception as e:
            raise RuntimeError(f"Error evaluating host command arguments: {e}")
        
        # Validate that all arguments are JSON-serializable
        # This prevents non-serializable objects from reaching the host
        try:
            json.dumps([command_id] + evaluated_args)
        except (TypeError, ValueError) as e:
            raise ValueError(f"host command arguments must be JSON-serializable: {e}")
        
        # Return the effect description as data
        return ["host", command_id] + evaluated_args

    # ---------- function application ----------
    # Resolve operator
    if isinstance(head, str):
        fn_val = env.lookup(head)
    else:
        fn_val = eval_expr(head, env)

    args = [eval_expr(a, env) for a in tail]

    if isinstance(fn_val, Closure):
        if len(args) != len(fn_val.params):
            raise TypeError(f"Arity mismatch: expected {len(fn_val.params)}, got {len(args)}")
        call_env = fn_val.env.extend(dict(zip(fn_val.params, args)))
        return eval_expr(fn_val.body, call_env)

    if callable(fn_val):
        return fn_val(*args)

    raise TypeError(f"Cannot call non‑callable value: {fn_val!r}")

def find_free_variables(expr: Any, bound: set[str] = None) -> set[str]:
    """Find free variables (symbols) referenced in an expression."""
    if bound is None:
        bound = set()
    
    if isinstance(expr, str):
        if expr.startswith("@"):
            return set()  # String literal
        return {expr} if expr not in bound else set()
    
    if not isinstance(expr, list) or not expr:
        return set()
    
    head, *tail = expr
    
    # Special forms that bind variables
    if head == "lambda":
        if len(tail) >= 2:
            params, body = tail[0], tail[1]
            param_names = params if isinstance(params, list) else []
            new_bound = bound | set(param_names)
            return find_free_variables(body, new_bound)
    
    if head == "def":
        if len(tail) >= 2:
            name, value_expr = tail[0], tail[1]
            # The name being defined is bound in the value expression (for recursion)
            new_bound = bound | {name}
            return find_free_variables(value_expr, new_bound)
    
    if head == "do":
        # Handle sequential definitions in do blocks
        free_vars = set()
        current_bound = bound.copy()
        for subexpr in tail:
            if isinstance(subexpr, list) and len(subexpr) >= 3 and subexpr[0] == "def":
                # This is a def - add the defined name to bound set for subsequent expressions
                def_name = subexpr[1]
                free_vars |= find_free_variables(subexpr, current_bound)
                current_bound.add(def_name)
            else:
                free_vars |= find_free_variables(subexpr, current_bound)
        return free_vars
    
    # For all other forms, recursively find free variables
    free_vars = set()
    for subexpr in expr:
        free_vars |= find_free_variables(subexpr, bound)
    
    return free_vars

def to_json_env_user_only(env: Env, _seen: set[int], referenced_vars: set[str] = None, closure_name: str = None) -> Dict[str, Any]:
    """Serialize environment, only including referenced user-defined variables."""
    oid = id(env)
    if oid in _seen:
        return {"$ref": oid}
    
    _seen.add(oid)
    
    try:
        # Get the prelude to know what to exclude
        prelude_keys = set(make_prelude().keys())
        
        result = {}
        
        # Only serialize user-defined bindings that are actually referenced
        for k, v in env.items():
            if k not in prelude_keys:  # Skip built-ins
                if referenced_vars is None or k in referenced_vars:
                    # Special case: if this is a self-reference to the closure being serialized,
                    # we could use a special marker instead of full serialization
                    if closure_name and k == closure_name and isinstance(v, Closure):
                        result[k] = {"$self": True}
                    else:
                        result[k] = to_json(v, _seen)
        
        # Recursively handle parent environments
        if env.parent:
            parent_data = to_json_env_user_only(env.parent, _seen, referenced_vars)
            if parent_data and parent_data != {"$ref": id(env.parent)}:
                result["$parent"] = parent_data
        
        return result
    finally:
        _seen.remove(oid)

def to_json(val: Any, _seen: set[int] | None = None) -> Dict[str, Any] | list[Any] | str | int | float | bool | None:
    """Serialize JSL values to JSON, handling circular references."""
    if val is None or isinstance(val, (bool, int, float, str)):
        return val

    if _seen is None:
        _seen = set()
    
    oid = id(val)
    if oid in _seen:
        return {"$ref": oid}
    _seen.add(oid)

    try:
        if isinstance(val, list):
            return [to_json(v, _seen) for v in val]
        
        if isinstance(val, Closure):
            # Find which variables are actually referenced in the closure body
            referenced_vars = find_free_variables(val.body)
            
            return {
                "$ref": oid,
                "type": "closure",
                "params": to_json(val.params, _seen),
                "body": to_json(val.body, _seen),
                "env": to_json_env_user_only(val.env, _seen, referenced_vars),
            }
        
        if isinstance(val, Env):
            return to_json_env_user_only(val, _seen)
        
        if isinstance(val, dict):
            return {k: to_json(v, _seen) for k, v in val.items()}

        raise TypeError(f"Cannot JSON‑encode {val!r}")
    finally:
        _seen.remove(oid)

def from_json(data: Dict[str, Any], prelude: Env) -> Any:
    """Reconstruct JSL values from flat JSON representation."""
    if data is None or isinstance(data, (bool, int, float, str)):
        return data
    
    if isinstance(data, list):
        return [from_json(item, prelude) for item in data]
    
    if isinstance(data, dict):
        if data.get("type") == "closure":
            # Reconstruct closure with environment registry
            env_registry = data.get("_environments", {})
            env = reconstruct_env(data["env"], env_registry, prelude)
            params = data["params"]
            body = from_json_env_value(data["body"], env_registry, prelude)
            return Closure(params, body, env)
        else:
            return {k: from_json(v, prelude) for k, v in data.items() if k != "_environments"}
    
    return data

def from_json_env_value(val: Any, env_registry: Dict[str, Dict], prelude: Env) -> Any:
    """Reconstruct a value that might contain closures with environment references."""
    if val is None or isinstance(val, (bool, int, float, str)):
        return val
    
    if isinstance(val, list):
        return [from_json_env_value(v, env_registry, prelude) for v in val]
    
    if isinstance(val, dict):
        if val.get("type") == "closure":
            env = reconstruct_env(val["env"], env_registry, prelude)
            params = val["params"]
            body = from_json_env_value(val["body"], env_registry, prelude)
            return Closure(params, body, env)
        else:
            return {k: from_json_env_value(v, env_registry, prelude) for k, v in val.items()}
    
    return val

def reconstruct_env(env_id: str, registry: Dict[str, Dict], prelude: Env, _cache: Dict[str, Env] | None = None) -> Env:
    """Reconstruct environment from flat registry using hash-based parent references."""
    if _cache is None:
        _cache = {}
    
    if env_id in _cache:
        return _cache[env_id]
    
    if env_id not in registry:
        raise ValueError(f"Environment ID {env_id} not found in registry")
    
    env_data = registry[env_id]
    
    # Reconstruct parent first (if it exists)
    parent = prelude
    if env_data["parent"]:
        parent = reconstruct_env(env_data["parent"], registry, prelude, _cache)
    
    # Reconstruct bindings
    bindings = {
        k: from_json_env_value(v, registry, prelude) 
        for k, v in env_data["bindings"].items()
    }
    
    # Create environment and cache it
    env = Env(bindings, parent=parent)
    # Override the computed ID to match the serialized one
    env._id = env_id
    _cache[env_id] = env
    
    return env

# ----------------------------------------------------------------------
# Module Loader
# ----------------------------------------------------------------------

def load_module(module_path: str, prelude_env: Env) -> Dict[str, Any]:
    """
    Loads a JSL module, evaluates it, and returns its exports.

    A module is a JSL program file (JSON). All top-level definitions (def)
    within the module are considered its exports. The module is evaluated
    in a new environment that is a child of the provided prelude_env.
    """
    module_env = Env(parent=prelude_env)
    
    try:
        with open(module_path) as f:
            module_data = json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Module file not found: {module_path}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON in module file: {module_path}")

    forms_to_eval: List[Any]
    if isinstance(module_data, list): # Allow a raw list of forms
        forms_to_eval = module_data
    elif isinstance(module_data, dict) and "forms" in module_data:
        forms_to_eval = module_data.get("forms", [])
    else:
        raise ValueError(
            f"Module {module_path} content is not a valid JSL structure. "
            "Expected a list of forms or a dict with a 'forms' key."
        )

    # Evaluate all forms in the module's own environment
    for form in forms_to_eval:
        eval_expr(form, module_env)

    # Exports are all bindings defined directly in the module_env itself.
    # Env inherits dict, so .items() gives only direct bindings.
    exports = {}
    for name, value in module_env.items():
        exports[name] = value
        
    return exports

# ----------------------------------------------------------------------
# Program runner
# ----------------------------------------------------------------------

def run_program(prog: Any, initial_env: Env) -> Any:
    """
    Runs a JSL program (parsed JSON data) in the given initial environment.

    The program can be a dictionary (e.g., {"forms": [], "entrypoint": ...})
    or a list of JSL expressions.

    If 'prog' is a dictionary:
      - Forms in "forms" are evaluated sequentially.
      - If "entrypoint" is specified, its evaluation is the result.
      - If no "entrypoint", the result of the last form in "forms" is returned.
      - If no "forms" and no "entrypoint", result is None.
    If 'prog' is a list of expressions:
      - Expressions are evaluated sequentially.
      - The result of the last expression is returned.
      - If the list is empty, result is None.
    """
    env = initial_env
    result = None

    if isinstance(prog, list):
        if not prog: # Empty list of forms
            return None
        for form in prog:
            result = eval_expr(form, env)
        return result
    elif isinstance(prog, dict):
        forms = prog.get("forms", [])
        entry_expr = prog.get("entrypoint")

        for form in forms:
            result = eval_expr(form, env) # Evaluate forms for side-effects/definitions

        if entry_expr is not None:
            return eval_expr(entry_expr, env)
        elif forms: # No entry_expr, but forms existed, result is from last form
            return result
        else: # No entry_expr and no forms
            return None
    else:
        raise ValueError(
            "Program must be a JSL dictionary structure or a list of forms. "
            f"Got: {type(prog)}"
        )

def run_with_imports(main_program_path: str, cli_allowed_imports: List[str], cli_bindings: Dict[str, str]) -> Any:
    """
    Run a JSL program with imported modules.
    
    Args:
        main_program_path: Path to main JSL program file.
        cli_allowed_imports: List of JSL files explicitly allowed to be imported (from --import).
                               Used as a check if provided.
        cli_bindings: Map of alias to module path (from --bind alias=path).
    """
    global prelude
    if prelude is None:
        prelude = make_prelude()
    
    # Environment for the main program starts based on the prelude.
    # We will extend this with module bindings.
    env_for_main_program = Env(parent=prelude)

    if cli_bindings:
        module_definitions_for_env = {}
        for alias, module_path in cli_bindings.items():
            # Optional: Enforce that bound modules must be in --import list
            if cli_allowed_imports and module_path not in cli_allowed_imports:
                print(f"Warning: Module '{module_path}' (bound to alias '{alias}') "
                      f"was not in the --import list. Skipping.", file=sys.stderr)
                continue
            
            try:
                # print(f"Loading module '{alias}' from '{module_path}'...", file=sys.stderr)
                # Each module is loaded using the global prelude as the base for its own environment.
                exports_dict = load_module(module_path, prelude)
                module_definitions_for_env[alias] = exports_dict # Bind the dict of exports to the alias
                # print(f"Module '{alias}' loaded. Exports: {list(exports_dict.keys())}", file=sys.stderr)
            except Exception as e:
                # Fail fast if a module can't be loaded
                raise RuntimeError(f"Failed to load module '{alias}' from '{module_path}': {e}") from e
        
        if module_definitions_for_env:
            env_for_main_program = env_for_main_program.extend(module_definitions_for_env)

    try:
        with open(main_program_path) as f:
            program_data = json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Main program file not found: {main_program_path}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON in main program file: {main_program_path}")
    
    return run_program(program_data, env_for_main_program)

def main():
    parser = argparse.ArgumentParser(description="JSL - JSON Script Language")
    parser.add_argument("program", nargs='?', default=None, help="JSL program file to run (reads from stdin if not provided and input is piped)")
    parser.add_argument("--import", dest="imports", action="append", default=[],
                       help="Declare a JSL file as importable: --import path/to/module.json")
    parser.add_argument("--bind", dest="bindings", action="append", default=[],
                       help="Bind module to an alias: --bind alias=path/to/module.json")
    
    args = parser.parse_args()
    
    binding_map = {}
    if args.bindings:
        for binding_arg_str in args.bindings:
            if "=" not in binding_arg_str:
                print(f"Error: Invalid --bind format '{binding_arg_str}'. Expected 'alias=path'.", file=sys.stderr)
                sys.exit(1)
            name, path = binding_arg_str.split("=", 1)
            binding_map[name] = path
    
    program_data = None
    program_source_name = "stdin"

    if args.program:
        program_source_name = args.program
        try:
            with open(args.program) as f:
                program_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Program file not found: {args.program}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in program file {args.program}: {e}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty(): # Check if input is piped
        try:
            program_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help(sys.stderr)
        print("\nError: No program file specified and no input from stdin.", file=sys.stderr)
        sys.exit(1)

    if program_data is None: # Should not happen if logic above is correct, but as a safeguard
        print("Error: Could not load program data.", file=sys.stderr)
        sys.exit(1)

    try:
        global prelude
        if prelude is None:
            prelude = make_prelude()

        if args.imports or args.bindings:
            # run_with_imports expects a path to the main program,
            # which is problematic if it came from stdin.
            # For now, let's adjust run_with_imports to accept program_data directly
            # or simplify this path if stdin is used with imports.
            # A simple solution: if program is from stdin, imports might be less common
            # or require a different handling strategy.
            # For now, let's assume if program is from stdin, it's a self-contained execution
            # or we need to enhance run_with_imports.
            if args.program: # main_program_path is valid
                result = run_with_imports(args.program, args.imports, binding_map)
            else: # main program is from stdin, pass program_data
                  # We need to adjust run_with_imports or have a separate path
                  # For simplicity, let's assume if program is from stdin, it's a direct run for now
                  # or that run_with_imports is adapted.
                  # The previous run_with_imports was:
                  # run_with_imports(main_program_path: str, ...)
                  #
                  # Let's assume for now that if using stdin, we don't use the file-based import system
                  # in the same way, or that modules are pre-loaded differently.
                  # This part needs careful consideration based on desired UX for piped imports.
                  #
                  # Simplest approach: if program_data is from stdin, run it directly
                  # with an environment potentially configured by --bind (if modules are globally accessible)
                  # This implies modules loaded by --bind are available even if main prog is from stdin.

                env_for_main_program = Env(parent=prelude)
                if binding_map:
                    module_definitions_for_env = {}
                    for alias, module_path in binding_map.items():
                        if args.imports and module_path not in args.imports:
                            print(f"Warning: Module '{module_path}' (bound to alias '{alias}') "
                                  f"was not in the --import list. Skipping.", file=sys.stderr)
                            continue
                        try:
                            exports_dict = load_module(module_path, prelude)
                            module_definitions_for_env[alias] = exports_dict
                        except Exception as e:
                            raise RuntimeError(f"Failed to load module '{alias}' from '{module_path}': {e}") from e
                    if module_definitions_for_env:
                        env_for_main_program = env_for_main_program.extend(module_definitions_for_env)
                
                result = run_program(program_data, env_for_main_program)

        else:
            # Simple case - just run the program directly with a fresh prelude-based environment
            direct_run_env = Env(parent=prelude)
            result = run_program(program_data, direct_run_env)
        
        print(json.dumps(to_json(result), indent=2))
            
    except Exception as e:
        print(f"Error running program from {program_source_name}: {e}", file=sys.stderr)
        # import traceback
        # traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()