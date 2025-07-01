"""
JSL: A JSON Serializable Language
"""

# Core components
from .core import Env, Closure, JSL_TYPE, JSL_JSON

# High-level functions for running JSL programs
from .runner import run_program

# The evaluator is not part of the public API, but is used by other modules.
from .evaluator import eval_expr, eval_template

# The prelude is not part of the public API, but is used by other modules.
from .prelude import prelude, make_prelude, eval_closure_or_builtin

# Serialization functions
from .serialization import dumps, loads, to_json, from_json, jsl_to_json, json_to_jsl, JSLEncoder, JSLDecoder

# The modules loader is not part of the public API.
# from .modules import get_modules, load_module
