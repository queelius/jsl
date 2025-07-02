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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track what we're currently serializing to handle cycles
        self._serializing = set()
    
    def default(self, obj):
        # Check for circular references before processing
        obj_id = id(obj)
        if obj_id in self._serializing:
            # Return a reference instead of recursing
            if isinstance(obj, Closure):
                return {"__jsl_ref__": "closure", "id": f"closure_{obj_id:016x}"}
            elif isinstance(obj, Env):
                return {"__jsl_ref__": "env", "id": f"env_{obj_id:016x}"}
            else:
                return {"__jsl_ref__": "object", "id": f"obj_{obj_id:016x}"}
        
        # Add to serialization set
        self._serializing.add(obj_id)
        
        try:
            if isinstance(obj, Closure):
                return {
                    "__jsl_type__": "closure",
                    "params": obj.params,
                    "body": obj.body,
                    "env": self._serialize_env_safe(obj.env)  # Use safe serialization
                }
            elif isinstance(obj, Env):
                return {
                    "__jsl_type__": "env", 
                    "bindings": self._serialize_env_bindings(obj),
                    "env_hash": self._safe_content_hash(obj)  # Use safe hash
                }
            return super().default(obj)
        finally:
            # Always clean up
            self._serializing.discard(obj_id)
    
    def _serialize_env_safe(self, env: Env) -> Dict:
        """Safely serialize an environment without triggering JSON circular ref detection."""
        # Check if we're already serializing this environment
        env_id = id(env)
        if env_id in self._serializing:
            return {"__jsl_ref__": "env", "id": f"env_{env_id:016x}"}
        
        # Use the environment's own content_hash for cycle detection
        env_hash = self._safe_content_hash(env)
        
        # Only serialize user-defined bindings, not prelude functions
        user_bindings = self._collect_user_bindings_safe(env)
        
        return {
            "bindings": user_bindings,
            "env_hash": env_hash
        }
    
    def _safe_content_hash(self, env: Env) -> str:
        """Safely get content hash, handling any recursion issues."""
        try:
            return env.content_hash()
        except (RecursionError, ValueError):
            # Fallback for any remaining recursion issues
            return f"fallback_hash_{id(env):016x}"
    
    def _collect_user_bindings_safe(self, env: Env) -> Dict:
        """Collect user bindings while avoiding circular references."""
        visited = set()
        result = {}
        
        def collect_from_env(e: Env):
            if e is None:
                return
            
            env_id = id(e)
            if env_id in visited:
                return
            
            visited.add(env_id)
            
            # Collect from parent first
            if e.parent:
                collect_from_env(e.parent)
            
            # Then collect from current level
            for name, value in e.bindings.items():
                # Skip built-in functions and avoid self-references
                if not callable(value) or isinstance(value, Closure):
                    # For closures, check if we're creating a cycle
                    if isinstance(value, Closure) and id(value.env) in visited:
                        # Don't include self-referential closures in bindings
                        # They'll be handled by the closure's own serialization
                        continue
                    result[name] = value
        
        collect_from_env(env)
        return result
    
    def _serialize_env_bindings(self, env: Env, visited=None) -> Dict:
        """Get serializable bindings from environment with cycle detection."""
        if visited is None:
            visited = set()
        
        env_id = id(env)
        if env_id in visited:
            return {}  # Return empty dict for circular references
        
        visited.add(env_id)
        result = {}
        
        try:
            if env.parent:
                result.update(self._serialize_env_bindings(env.parent, visited))
            
            for k, v in env.bindings.items():
                if not callable(v) or isinstance(v, Closure):
                    result[k] = v
            
            return result
        finally:
            visited.discard(env_id)


class JSLDecoder(json.JSONDecoder):
    """JSON decoder that reconstructs JSL-specific types."""
    
    def __init__(self, prelude_env: Env = None):
        super().__init__(object_hook=self.object_hook)
        self.prelude_env = prelude_env
        self._refs = {}  # Track references during deserialization
    
    def object_hook(self, obj):
        if isinstance(obj, dict):
            # Handle references first
            if "__jsl_ref__" in obj:
                ref_id = obj["id"]
                if ref_id in self._refs:
                    return self._refs[ref_id]
                else:
                    # Create placeholder that will be resolved later
                    return {"__unresolved_ref__": ref_id}
            
            # Handle actual objects
            if "__jsl_type__" in obj:
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
        
        closure = Closure(params, body, env)
        
        # Store reference for potential circular refs
        closure_id = f"closure_{id(closure):016x}"
        self._refs[closure_id] = closure
        
        return closure
    
    def _deserialize_env(self, obj: Dict) -> Env:
        """Deserialize an environment object."""
        bindings = obj["bindings"]
        env = self._reconstruct_env({"bindings": bindings})
        
        # Store reference
        env_id = f"env_{id(env):016x}"
        self._refs[env_id] = env
        
        return env
    
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
