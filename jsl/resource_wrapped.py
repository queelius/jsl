"""
Resource-aware wrappers for built-in functions.

These wrappers add resource checking to operations that can consume
significant memory or create large data structures.
"""

from typing import Any, Callable
from .core import Evaluator


def create_resource_aware_function(original_func: Callable, check_type: str = "result") -> Callable:
    """
    Create a resource-aware wrapper for a function.
    
    Args:
        original_func: The original function to wrap
        check_type: Type of check - "result" for output, "input" for input
    """
    def wrapper(*args, **kwargs):
        # Get the evaluator from the call stack if available
        import sys
        evaluator = None
        frame = sys._getframe()
        while frame:
            if 'self' in frame.f_locals:
                obj = frame.f_locals['self']
                if isinstance(obj, Evaluator):
                    evaluator = obj
                    break
            frame = frame.f_back
        
        # Call the original function
        result = original_func(*args, **kwargs)
        
        # Check resources if we have an evaluator with resource tracking
        if evaluator and evaluator.resources:
            if check_type == "result":
                if isinstance(result, list):
                    evaluator.resources.check_collection_size(len(result))
                    # Also track memory for large lists
                    evaluator.resources.allocate_memory(
                        len(result) * 8,  # Rough estimate: 8 bytes per element
                        f"list of size {len(result)}"
                    )
                elif isinstance(result, str):
                    evaluator.resources.check_string_length(len(result))
                    evaluator.resources.allocate_memory(
                        len(result),  # 1 byte per character estimate
                        f"string of length {len(result)}"
                    )
                elif isinstance(result, dict):
                    evaluator.resources.check_collection_size(len(result))
                    evaluator.resources.allocate_memory(
                        len(result) * 16,  # Rough estimate for dict overhead
                        f"dict of size {len(result)}"
                    )
        
        return result
    
    # Preserve function metadata
    wrapper.__name__ = original_func.__name__
    wrapper.__doc__ = original_func.__doc__
    return wrapper


def wrap_prelude_functions(env):
    """
    Wrap prelude functions with resource checking.
    
    This modifies the environment to replace certain functions
    with resource-aware versions.
    """
    # List operations that can create large structures
    list_ops = ['concat', 'range', 'map', 'filter', 'zip']
    
    for op in list_ops:
        if op in env.bindings:
            original = env.bindings[op]
            if callable(original):
                env.bindings[op] = create_resource_aware_function(original)
    
    # String operations
    string_ops = ['str-concat', 'str-repeat']
    
    for op in string_ops:
        if op in env.bindings:
            original = env.bindings[op]
            if callable(original):
                env.bindings[op] = create_resource_aware_function(original)
    
    return env