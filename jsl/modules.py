import operator
from functools import reduce
import json

from .core import Env
from .evaluator import eval_expr as evaluate

def get_modules():
    """
    Returns a dictionary of all modules.
    """
    return {
        "math": {
            "+": lambda *args: sum(args),
            "-": lambda *args: args[0] - sum(args[1:]),
            "*": lambda *args: reduce(operator.mul, args),
            "/": lambda *args: args[0] / reduce(operator.mul, args[1:]),
            "%": lambda x, y: x % y,
            "abs": lambda x: abs(x),
            "**": lambda x, y: x ** y,
        },
        "string": {
            "len": lambda x: len(x),
            "+": lambda *args: "".join(str(arg) for arg in args),
        },
        "operator": {
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">": lambda x, y: x > y,
            ">=": lambda x, y: x >= y,
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
        },
        "collection": {
            "len": lambda x: len(x),
            "get": lambda col, key: col[key],
            "set": lambda col, key, val: col.update({key: val}) or col,
            "append": lambda arr, val: arr + [val],
            "slice": lambda arr, start, stop, step: arr[start:stop:step],
        },
        "functional": {
            "map": lambda func, arr: list(map(func, arr)),
            "filter": lambda func, arr: list(filter(func, arr)),
            "reduce": lambda func, arr, init: reduce(func, arr, init),
        },
        "type": {
            "is_int": lambda x: isinstance(x, int),
            "is_float": lambda x: isinstance(x, float),
            "is_string": lambda x: isinstance(x, str),
            "is_bool": lambda x: isinstance(x, bool),
            "is_array": lambda x: isinstance(x, list),
            "is_object": lambda x: isinstance(x, dict),
        }
    }

def load_module(path: str, env: Env) -> Env:
    """
    Loads a JSL module from a file.
    """
    with open(path, "r") as f:
        module_def = json.load(f)
    
    module_env = Env(parent=env)
    if "exports" in module_def:
        for name, expr in module_def["exports"].items():
            module_env[name] = evaluate(expr, module_env)
            
    return module_env
