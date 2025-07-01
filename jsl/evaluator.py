"""
JSL Evaluation Engine

Handles the evaluation of JSL expressions, including special forms and
function application.
"""

from __future__ import annotations
import json
from typing import Any, List
from .core import Env, Closure
from .jsl_host_dispatcher import process_host_request

def eval_template(part: Any, env: Env) -> Any:
    """
    This is a template for JSON. We do not do general evaluations,
    but only lookups in the environment. Otherwise, everything
    is treated as a literal.
    """
    if isinstance(part, str):
        if part.startswith("@"):
            return part[1:]  # String literal escape
        else:
            # Symbol lookup. The result of the lookup might need further template processing.
            value = env.lookup(part)
            if isinstance(value, str):
                if value.startswith("@"):
                    return env.lookup(value[1:])
                return value  # Return the looked-up string as is
            else:
                return eval_template(value, env)  # Evaluate the looked-up value as a template part
    
    elif isinstance(part, (int, float, bool)) or part is None:
        return part  # Primitive values evaluate to themselves

    elif isinstance(part, list):
        # This is a list literal within the template. Process its parts.
        return [eval_template(part, env) for part in part]
    
    elif isinstance(part, dict):
        # This is a dict literal within the template. Process its keys and values.
        return {eval_template(k, env): eval_template(v, env) for k, v in part.items()}
    
    raise ValueError(f"Cannot evaluate JSON template part of type {type(part)}: {part}")

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
    
    if isinstance(expr, (int, float, bool, dict)) or expr is None:
        return expr

    if not isinstance(expr, list) or not expr: # Ensure expr is a non-empty list for further processing
        # If it's not a list, and wasn't handled as a literal/symbol above,
        # it might be an already evaluated dict from a module, or an error.
        # For now, assume if it reached here and isn't a list, it's a value (e.g. a dict from a module).
        # This part might need refinement based on how non-list, non-primitive exprs are expected.
        # However, the `json` special form's argument will be a list or dict.
        if isinstance(expr, dict): # Allow pre-formed dicts (e.g. from module exports) to pass through
            return expr
        raise ValueError(f"Cannot evaluate expression of type {type(expr)}: {expr}")

    head, *tail = expr

    # ---------- special forms ----------
    if head == "json":              # ["json", template]
        if len(tail) != 1:
            raise ValueError("json special form expects exactly one argument (the template)")
        # The argument to "json" is the root of the template.
        return eval_template(tail[0], env)

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
    
    if head == "let":
        """
        let special form: ["let", [bindings], body]
        bindings is a list of pairs [name, value_expr]
        """
        if len(tail) != 2: # Check number of arguments first
            raise ValueError("let expects exactly two arguments: a list of bindings and a body")
        
        bindings_expr, body = tail # Unpack after length check

        if not isinstance(bindings_expr, list): # Then check type of bindings argument
            raise ValueError("let bindings must be a list")

        # Now bindings_expr is confirmed to be a list.
        # Proceed to check the structure of each binding pair.
        if not all(isinstance(b, list) and len(b) == 2 for b in bindings_expr):
            raise ValueError("Each let binding must be a list of [name, value_expr]")
        
        let_env = env.extend({})
        for name, value_expr in bindings_expr: # Use bindings_expr here
            if not isinstance(name, str):
                raise ValueError(f"let binding name must be a string, got {type(name).__name__}")
            value = eval_expr(value_expr, env) # Values are evaluated in the outer environment
            let_env[name] = value

        # Evaluate the body in the new environment
        return eval_expr(body, let_env)

    if head == "host":             # ["host", command_id, ...args]
        if not tail:
            raise ValueError("host command requires at least a command_id")
        
        command_id_expr = tail[0]
        arg_exprs = tail[1:]
        
        # Evaluate command_id expression
        command_id = eval_expr(command_id_expr, env)
        if not isinstance(command_id, str):
            raise TypeError(f"host command_id must evaluate to a string, got {type(command_id).__name__} from {command_id_expr}")
        
        # Evaluate all argument expressions to pure values
        try:
            evaluated_args = [eval_expr(arg, env) for arg in arg_exprs]
        except Exception as e:
            # More specific error message for argument evaluation failure
            raise RuntimeError(f"Error evaluating arguments for host command '{command_id}': {e}")
        
        # Construct the JHIP request message
        request_message = ["host", command_id] + evaluated_args
        
        # Validate that the constructed request_message (specifically args) is JSON-serializable
        # process_host_request might do its own validation, but good to ensure here too.
        try:
            # We only need to check evaluated_args as command_id is already a string
            # and "host" is a
            json.dumps(request_message)
        except (TypeError, ValueError) as e:
            raise ValueError(f"host command arguments must be JSON-serializable: {e}")
        
        # Send the request to the host and return the response
        response = process_host_request(request_message)
        
        # Check if the response indicates a JHIP error
        if isinstance(response, dict) and "$jsl_host_error" in response:
            error_obj = response["$jsl_host_error"]
            error_type = error_obj.get("type", "UnknownHostError")
            error_message = error_obj.get("message", "An unspecified error occurred on the host.")
            error_details = error_obj.get("details", {})
            # Construct the error message to match the test's expectation
            raise RuntimeError(f"Host error ({error_type}): {error_message} - Details: {error_details}")
        
        return response

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
    
    if isinstance(fn_val, (str, int, float, bool, list, dict) or fn_val is None):
        return fn_val
    
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
