"""
JSL Serialization - JSON serialization for JSL values and closures

This module handles the serialization and deserialization of JSL values,
including closures with their captured environments. Uses content-addressable
storage to handle circular references elegantly.
"""

import json
import hashlib
from typing import Any, Dict, Optional, Set
from .core import Closure, Env


class ContentAddressableSerializer:
    """
    Serializer that uses content hashing to handle circular references elegantly.
    
    The key insight: each object's content hash uniquely identifies it, and we can
    use these hashes as stable references that work across serialization boundaries.
    """
    
    def __init__(self):
        # Maps content hash -> serialized representation
        self.objects = {}
        # Track what we're currently computing to detect cycles
        self.computing = set()
        
    def serialize(self, obj: Any) -> str:
        """
        Serialize a JSL value to JSON string.
        
        Returns a JSON object with:
        - "root": hash of the root object (or the object itself if primitive)
        - "objects": table of hash -> serialized object mappings
        """
        root = self._process_value(obj)
        
        if self.objects:
            result = {
                "__cas_version__": 1,
                "root": root,
                "objects": self.objects
            }
        else:
            # No complex objects, just return the value directly
            result = root
            
        return json.dumps(result, allow_nan=False, sort_keys=True)
    
    def _process_value(self, obj: Any) -> Any:
        """
        Process a value, returning either:
        - A primitive value directly
        - A hash reference for complex objects (Closure, Env)
        - A processed structure (list/dict) with nested values processed
        """
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            # Primitives pass through
            return obj
            
        elif isinstance(obj, Closure):
            # Get content hash and ensure it's in the objects table
            obj_hash = self._get_closure_hash(obj)
            if obj_hash not in self.objects:
                self.objects[obj_hash] = self._serialize_closure(obj)
            return {"__ref__": obj_hash}
            
        elif isinstance(obj, Env):
            # Get content hash and ensure it's in the objects table
            obj_hash = self._get_env_hash(obj)
            if obj_hash not in self.objects:
                self.objects[obj_hash] = self._serialize_env(obj)
            return {"__ref__": obj_hash}
            
        elif isinstance(obj, list):
            # Process each element
            return [self._process_value(item) for item in obj]
            
        elif isinstance(obj, dict):
            # Process each value (keys must be strings in JSON)
            return {k: self._process_value(v) for k, v in obj.items()}
            
        else:
            # Unknown type - try to pass through
            return obj
    
    def _get_closure_hash(self, closure: Closure) -> str:
        """Compute content hash for a closure."""
        # The hash should be based on:
        # 1. Parameters
        # 2. Body (which is JSON-serializable JSL code)
        # 3. Environment hash
        
        content = {
            "type": "closure",
            "params": closure.params,
            "body": closure.body,
            "env_hash": self._get_env_hash(closure.env)
        }
        
        # Create deterministic JSON string
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def _get_env_hash(self, env: Env) -> str:
        """
        Compute content hash for an environment.
        
        This needs to handle cycles carefully - an environment might
        contain bindings that reference back to itself.
        """
        env_id = id(env)
        
        # Check if we're already computing this env's hash (cycle detection)
        if env_id in self.computing:
            # Return a deterministic placeholder for this cycle
            return f"cycle_{env_id:016x}"[:16]
            
        self.computing.add(env_id)
        
        try:
            # Collect bindings from this env and its parents
            bindings = {}
            current = env
            visited = set()
            
            while current is not None:
                curr_id = id(current)
                if curr_id in visited:
                    break
                visited.add(curr_id)
                
                # Add bindings from this level (don't override child bindings)
                for name, value in current.bindings.items():
                    if name not in bindings:
                        # Skip built-in functions, but include Closures
                        if not callable(value) or isinstance(value, Closure):
                            bindings[name] = self._hash_value(value)
                
                current = current.parent
            
            # Create content for hashing
            content = {
                "type": "env",
                "bindings": bindings
            }
            
            content_str = json.dumps(content, sort_keys=True)
            return hashlib.sha256(content_str.encode()).hexdigest()[:16]
            
        finally:
            self.computing.discard(env_id)
    
    def _hash_value(self, value: Any) -> Any:
        """
        Get a hashable representation of a value.
        Used for computing environment hashes.
        """
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        elif isinstance(value, Closure):
            return {"__closure_hash__": self._get_closure_hash(value)}
        elif isinstance(value, Env):
            return {"__env_hash__": self._get_env_hash(value)}
        elif isinstance(value, list):
            return [self._hash_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._hash_value(v) for k, v in value.items()}
        else:
            # For unknown types, use their string representation
            return str(value)
    
    def _serialize_closure(self, closure: Closure) -> Dict:
        """Serialize a closure's content."""
        return {
            "__type__": "closure",
            "params": closure.params,
            "body": closure.body,
            "env": self._process_value(closure.env)
        }
    
    def _serialize_env(self, env: Env) -> Dict:
        """Serialize an environment's content."""
        env_id = id(env)
        
        # If we're already serializing this env, return a marker
        if env_id in self.computing:
            return {
                "__type__": "env",
                "__cycle__": True,
                "id": env_id
            }
        
        self.computing.add(env_id)
        
        try:
            # Collect user-defined bindings
            bindings = {}
            current = env
            visited = set()
            
            while current is not None:
                curr_id = id(current)
                if curr_id in visited:
                    break
                visited.add(curr_id)
                
                for name, value in current.bindings.items():
                    if name not in bindings:
                        # Skip built-in functions but include Closures
                        if not callable(value) or isinstance(value, Closure):
                            bindings[name] = self._process_value(value)
                
                current = current.parent
            
            return {
                "__type__": "env",
                "bindings": bindings
            }
        finally:
            self.computing.discard(env_id)


class ContentAddressableDeserializer:
    """
    Deserializer that reconstructs objects from content-addressable format.
    """
    
    def __init__(self, prelude_env: Optional[Env] = None):
        self.prelude_env = prelude_env
        # Maps hash -> reconstructed object
        self.reconstructed = {}
        # Objects table from serialized data
        self.objects = {}
        
    def deserialize(self, json_str: str) -> Any:
        """Deserialize a JSON string to JSL value."""
        data = json.loads(json_str)
        
        # Check if this is CAS format
        if isinstance(data, dict) and "__cas_version__" in data:
            self.objects = data["objects"]
            root = data["root"]
            return self._reconstruct_value(root)
        else:
            # Direct value (no complex objects)
            return self._reconstruct_value(data)
    
    def _reconstruct_value(self, data: Any) -> Any:
        """Reconstruct a value from its serialized form."""
        if isinstance(data, dict):
            if "__ref__" in data:
                # This is a reference to an object
                ref_hash = data["__ref__"]
                return self._reconstruct_object(ref_hash)
            else:
                # Regular dict - reconstruct values
                return {k: self._reconstruct_value(v) for k, v in data.items()}
                
        elif isinstance(data, list):
            return [self._reconstruct_value(item) for item in data]
            
        else:
            # Primitive value
            return data
    
    def _reconstruct_object(self, obj_hash: str) -> Any:
        """Reconstruct an object from its hash."""
        # Check if we've already reconstructed this object
        if obj_hash in self.reconstructed:
            return self.reconstructed[obj_hash]
        
        # Handle cycle placeholders
        if obj_hash.startswith("cycle_"):
            # This represents a cycle to an object we're already reconstructing
            # Try to find the corresponding object in our objects table
            # The cycle hash format is "cycle_" + hex object id
            
            # Look through objects for one that might match this cycle
            for hash_key, obj_data in self.objects.items():
                if obj_data.get("__cycle__"):
                    # This is the cycle marker itself, skip it
                    continue
                # Check if this could be the referenced object
                # For now, if we have an env being reconstructed, return it
                if hash_key in self.reconstructed:
                    obj = self.reconstructed[hash_key]
                    if isinstance(obj, Env):
                        return obj
            
            # If we can't find it, return prelude env as safe fallback
            if self.prelude_env:
                return self.prelude_env
            else:
                from .prelude import make_prelude
                return make_prelude()
        
        # Get the object data
        if obj_hash not in self.objects:
            raise ValueError(f"Unknown object hash: {obj_hash}")
            
        obj_data = self.objects[obj_hash]
        
        # Reconstruct based on type
        if obj_data.get("__type__") == "closure":
            closure = self._reconstruct_closure(obj_data, obj_hash)
            self.reconstructed[obj_hash] = closure
            return closure
            
        elif obj_data.get("__type__") == "env":
            env = self._reconstruct_env(obj_data, obj_hash)
            self.reconstructed[obj_hash] = env
            return env
            
        else:
            raise ValueError(f"Unknown object type in hash {obj_hash}")
    
    def _reconstruct_closure(self, data: Dict, obj_hash: str) -> Closure:
        """Reconstruct a closure."""
        # Validate required fields
        if "params" not in data:
            raise KeyError("Closure missing 'params' field")
        if "body" not in data:
            raise KeyError("Closure missing 'body' field")
            
        params = data["params"]
        body = data["body"]
        env_data = data.get("env")
        
        # Validate types
        if not isinstance(params, list):
            raise TypeError(f"Closure params must be a list, got {type(params).__name__}")
        # Body should typically be a list (JSL expression) or potentially a primitive
        # But for closures, body should be a list representing the function body
        if not isinstance(body, list):
            raise TypeError(f"Closure body must be a list (JSL expression), got {type(body).__name__}")
        
        # Reconstruct the environment
        if env_data:
            env = self._reconstruct_value(env_data)
        else:
            # Closures always need an environment - use prelude as fallback
            if self.prelude_env:
                env = self.prelude_env
            else:
                from .prelude import make_prelude
                env = make_prelude()
        
        return Closure(params, body, env)
    
    def _reconstruct_env(self, data: Dict, obj_hash: str) -> Env:
        """Reconstruct an environment."""
        # Check if this is a cycle marker
        if data.get("__cycle__"):
            # This is a cycle - check if we're already reconstructing this env
            original_id = data.get("id")
            if original_id:
                # Look for an env we're already reconstructing with this ID
                for cached_hash, cached_obj in self.reconstructed.items():
                    if isinstance(cached_obj, Env) and cached_hash.endswith(str(original_id)):
                        return cached_obj
            # Fallback to prelude if we can't find the original
            if self.prelude_env:
                return self.prelude_env
            else:
                from .prelude import make_prelude
                return make_prelude()
        
        # Validate required fields
        if "bindings" not in data:
            raise KeyError("Environment missing 'bindings' field")
            
        bindings_data = data["bindings"]
        
        # Validate type
        if not isinstance(bindings_data, dict):
            raise TypeError(f"Environment bindings must be a dict, got {type(bindings_data).__name__}")
        
        # Create the Env object immediately and cache it (to handle cycles)
        # Start with prelude as base if available
        if self.prelude_env:
            env = self.prelude_env.extend({})  # Empty extension for now
        else:
            env = Env({})  # Empty bindings for now
        self.reconstructed[obj_hash] = env
        
        # Reconstruct bindings and update the env
        bindings = {}
        for name, value_data in bindings_data.items():
            bindings[name] = self._reconstruct_value(value_data)
        
        # Update the env's bindings directly
        env.bindings.update(bindings)
        
        return env


# Public API functions
def serialize(obj: Any) -> str:
    """
    Serialize a JSL value to JSON string.
    
    Args:
        obj: The JSL value to serialize
    
    Returns:
        JSON string representation
    """
    serializer = ContentAddressableSerializer()
    return serializer.serialize(obj)


def deserialize(json_str: str, prelude_env: Env = None) -> Any:
    """
    Deserialize a JSON string to JSL value.
    
    Args:
        json_str: JSON string to deserialize
        prelude_env: Optional prelude environment for closure reconstruction
    
    Returns:
        Reconstructed JSL value
    """
    deserializer = ContentAddressableDeserializer(prelude_env)
    return deserializer.deserialize(json_str)


def to_json(obj: Any) -> Dict:
    """
    Convert JSL value to JSON-compatible dictionary.
    
    Args:
        obj: JSL value to convert
    
    Returns:
        JSON-compatible dictionary
    """
    serialized = serialize(obj)
    return json.loads(serialized)


def from_json(json_data: Any, prelude_env: Env = None) -> Any:
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


# Exports
__all__ = [
    'serialize',
    'deserialize',
    'to_json',
    'from_json',
    'serialize_program',
    'deserialize_program',
    'ContentAddressableSerializer',
    'ContentAddressableDeserializer'
]