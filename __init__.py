"""
JSL - JSON Serializable Language

A network-native functional programming language where code and data are both JSON.
"""

# Import all public components from the main module
from .jsl import *

# Version information
__version__ = "0.1.0"
__author__ = "JSL Project"
__license__ = "MIT"

# Make sure all expected exports are available
__all__ = [
    # Core data structures
    'Env', 'Closure', 'prelude',
    
    # Prelude and built-ins  
    'make_prelude', 'get_prelude',
    
    # Evaluation engine
    'eval_expr', 'evaluate', 'eval_template', 'find_free_variables',
    
    # Serialization
    'to_json', 'from_json',
    
    # Module system
    'load_module',
    
    # Program execution
    'run_program', 'main'
]
