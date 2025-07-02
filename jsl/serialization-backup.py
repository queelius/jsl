"""
JSL Serialization - JSON serialization for JSL values and closures

This module handles the serialization and deserialization of JSL values,
including closures with their captured environments.
"""

import json
import hashlib
from typing import Any, Dict, List, Union

from .core import Env, Closure, JSLValue


class JSLEncoder(json.JSONEncoder):
    """JSON encoder that handles JSL-specific types like closures."""
    
    def default(self, obj):
        if isinstance(obj, Closure):
            return {
                "__jsl_type__": "closure",
                "params": obj.params,
                "body": obj.body,
                "env": self._serialize_env(obj.env)
            }
        elif isinstance(obj, Env):
            return {
                "__jsl_type__": "env", 
                "bindings": self._serialize_env_bindings(obj),
                "env_hash": obj.content_hash()
            }
        return super().default(obj)
    
    def _serialize_env(self, env: Env) -> Dict:
        """Serialize an environment, capturing only user-defined bindings."""
        # Only serialize user-defined bindings, not prelude functions
        user_bindings = {}
        
        def collect_user_bindings(e: Env):
            if e is None:
                return
            
            # Collect from parent first (depth-first)
            if e.parent:
                collect_user_bindings(e.parent)
            
            # Then collect from current level
            for name, value in e.bindings.items():
                # Skip built-in functions (they're not serializable)
                if not callable(value) or isinstance(value, Closure):
                    user_bindings[name] = value
        
        collect_user_bindings(env)
        return {
            "bindings": user_bindings,
            "env_hash": env.content_hash()
        }
    
    def _serialize_env_bindings(self, env: Env) -> Dict:
        """Get serializable bindings from environment."""
        result = {}
        if env.parent:
            result.update(self._serialize_env_bindings(env.parent))
        
        for k, v in env.bindings.items():
            if not callable(v) or isinstance(v, Closure):
                result[k] = v
        
        return result


class JSLDecoder(json.JSONDecoder):
    """JSON decoder that reconstructs JSL-specific types."""
    
    def __init__(self, prelude_env: Env = None):
        super().__init__(object_hook=self.object_hook)
        self.prelude_env = prelude_env
    
    def object_hook(self, obj):
        if isinstance(obj, dict) and "__jsl_type__" in obj:
            if obj["__jsl_type__"] == "closure":
                return self._deserialize_closure(obj)
            elif obj["__jsl_type__"] == "env":
                return self._deserialize_env(obj)
        return obj
    
    def _deserialize_closure(self, obj: Dict) -> Closure:
        """Deserialize a closure object."""
        params = obj["params"]
        body = obj["body"]
        env_data = obj["env"]
        
        # Reconstruct environment
        env = self._reconstruct_env(env_data)
        
        return Closure(params, body, env)
    
    def _deserialize_env(self, obj: Dict) -> Env:
        """Deserialize an environment object."""
        bindings = obj["bindings"]
        return self._reconstruct_env({"bindings": bindings})
    
    def _reconstruct_env(self, env_data: Dict) -> Env:
        """Reconstruct an environment from serialized data."""
        bindings = env_data["bindings"]
        
        # Start with prelude if available
        if self.prelude_env:
            env = self.prelude_env.extend(bindings)
        else:
            env = Env(bindings)
        
        return env


def serialize(obj: Any, indent: int = None) -> str:
    """
    Serialize a JSL value to JSON string.
    
    Args:
        obj: The JSL value to serialize
        indent: Optional indentation for pretty printing
    
    Returns:
        JSON string representation
    """
    return json.dumps(obj, cls=JSLEncoder, indent=indent)


def deserialize(json_str: str, prelude_env: Env = None) -> Any:
    """
    Deserialize a JSON string to JSL value.
    
    Args:
        json_str: JSON string to deserialize
        prelude_env: Optional prelude environment for closure reconstruction
    
    Returns:
        Reconstructed JSL value
    """
    decoder = JSLDecoder(prelude_env)
    return decoder.decode(json_str)


def to_json(obj: Any) -> Dict:
    """
    Convert JSL value to JSON-compatible dictionary.
    
    Args:
        obj: JSL value to convert
    
    Returns:
        JSON-compatible dictionary
    """
    encoder = JSLEncoder()
    # Use the encoder's default method to handle JSL types
    return json.loads(json.dumps(obj, cls=JSLEncoder))


def from_json(json_data: Union[str, Dict], prelude_env: Env = None) -> Any:
    """
    Reconstruct JSL value from JSON data.
    
    Args:
        json_data: JSON string or dictionary
        prelude_env: Optional prelude environment
        
    Returns:
        Reconstructed JSL value
    """
    if isinstance(json_data, str):
        return deserialize(json_data, prelude_env)
    else:
        # Convert dict back to JSON string and deserialize
        json_str = json.dumps(json_data)
        return deserialize(json_str, prelude_env)


def serialize_program(program: Any, prelude_hash: str = None) -> Dict:
    """
    Serialize a complete JSL program with metadata.
    
    Args:
        program: The JSL program to serialize
        prelude_hash: Optional hash of the prelude version
        
    Returns:
        Dictionary with program and metadata
    """
    return {
        "version": "0.1.0",
        "prelude_hash": prelude_hash,
        "program": to_json(program),
        "timestamp": None  # Could add timestamp if needed
    }


def deserialize_program(program_data: Dict, prelude_env: Env = None) -> Any:
    """
    Deserialize a complete JSL program.
    
    Args:
        program_data: Serialized program data
        prelude_env: Prelude environment for reconstruction
        
    Returns:
        Reconstructed JSL program
    """
    # Could add version checking here
    program = program_data.get("program")
    return from_json(program, prelude_env)
