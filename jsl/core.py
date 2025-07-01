"""
JSL Core Data Structures

Contains the fundamental data structures used throughout the JSL runtime.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List

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

class Env:
    """
    Lexical environment with parent chaining for scope resolution.
    Manages its own bindings and provides dictionary-like access.
    """
    
    def __init__(self, bindings: Dict[str, Any] | None = None, parent: "Env|None" = None):
        self._bindings: Dict[str, Any] = bindings or {}
        self.parent: Env | None = parent
        self._id: str | None = None  # Computed lazily
    
    def lookup(self, name: str) -> Any:
        if name in self._bindings:
            return self._bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        raise NameError(f"Unbound symbol: {name}")
    
    def extend(self, bindings: Dict[str, Any]) -> "Env":
        # Create a new environment with the current one as parent
        return Env(bindings, parent=self)
    
    def __setitem__(self, name: str, value: Any):
        """Allows setting bindings like env[name] = value."""
        self._bindings[name] = value

    def __getitem__(self, name: str) -> Any:
        """Allows getting bindings like env[name], raises KeyError if not found directly."""
        if name in self._bindings:
            return self._bindings[name]
        raise KeyError(name) # Consistent with dict behavior for direct access

    def __contains__(self, name: str) -> bool:
        """Allows checking bindings like name in env."""
        return name in self._bindings

    def items(self) -> list[tuple[str, Any]]:
        """Returns a list of (name, value) pairs for direct bindings."""
        return list(self._bindings.items())

    def get(self, name: str, default: Any = None) -> Any:
        """Gets a binding, returning a default if not found directly."""
        return self._bindings.get(name, default)

    def get_bindings(self) -> Dict[str, Any]:
        """Returns a copy of the direct bindings in this environment."""
        return self._bindings.copy()

    def get_id(self) -> str:
        """Get a unique ID for this environment instance."""
        if self._id is None:
            self._id = str(id(self))
        return self._id
    
# Global reference to the prelude for closure environment fixing
prelude: Env | None = None # Ensure type hint matches
