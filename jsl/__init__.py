"""
JSL - JSON Serializable Language

A network-native functional programming language where code and data are both JSON.
"""

# Version information
__version__ = "0.2.0"
__author__ = "Alex Towell"
__license__ = "MIT"

# Core components
from .core import (
    Env, 
    Closure, 
    Evaluator, 
    HostDispatcher,
    JSLError, 
    SymbolNotFoundError, 
    JSLTypeError,
    JSLValue,
    JSLExpression
)

# Prelude
from .prelude import make_prelude

# High-level API
from .runner import JSLRunner, run_program, eval_expression
from .serialization import serialize, deserialize, to_json, from_json

# Make sure all expected exports are available
__all__ = [
    # Version info
    "__version__", "__author__", "__license__",
    
    # Core data structures and types
    "Env", "Closure", "Evaluator", "HostDispatcher",
    "JSLError", "SymbolNotFoundError", "JSLTypeError",
    "JSLValue", "JSLExpression",
    
    # Prelude  
    "make_prelude",
    
    # High-level API
    "JSLRunner", "run_program", "eval_expression",
    
    # Serialization
    "serialize", "deserialize", "to_json", "from_json",
]
