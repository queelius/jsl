"""
Resource management for JSL execution.

Provides gas metering, memory tracking, and time limits to prevent
DOS attacks and ensure fair resource allocation in network-native environments.
"""

import time
from typing import Optional, Dict, Any
from enum import IntEnum


class GasCost(IntEnum):
    """Gas costs for different operation types."""
    # Basic operations
    LITERAL = 1
    VARIABLE = 2
    
    # Arithmetic and logic
    ARITHMETIC = 3
    COMPARISON = 3
    LOGICAL = 3
    
    # Control flow
    IF = 5
    LET = 10
    DO = 5
    DEF = 10
    
    # Functions
    LAMBDA_CREATE = 20
    FUNCTION_CALL = 10
    
    # Collections
    LIST_CREATE = 5
    LIST_PER_ITEM = 1
    DICT_CREATE = 5
    DICT_PER_ITEM = 2
    
    MAP_BASE = 20
    MAP_PER_ITEM = 3
    FILTER_BASE = 20
    FILTER_PER_ITEM = 3
    REDUCE_BASE = 20
    REDUCE_PER_ITEM = 5
    
    # Strings
    STRING_CONCAT = 10
    STRING_SPLIT = 20
    STRING_UPPER = 5
    STRING_LOWER = 5
    
    # Default host operation cost
    HOST_DEFAULT = 100


class HostGasPolicy:
    """
    Hierarchical gas cost policy for host operations.
    
    Costs are inherited from parent namespaces, with more specific
    paths overriding general ones.
    """
    
    def __init__(self, cost_tree: Optional[Dict] = None):
        """
        Initialize with a cost tree.
        
        Args:
            cost_tree: Hierarchical dict of namespace costs.
                      Use "_cost" key for namespace defaults.
        """
        self.cost_tree = cost_tree or self._default_costs()
    
    @staticmethod
    def _default_costs() -> Dict:
        """Default cost structure for common host operations."""
        return {
            "@": 100,  # Default for unknown operations
            "@file": {
                "_cost": 500,
                "read": 200,
                "write": 1000,
                "delete": 2000,
                "exists": 50,
                "size": 50,
                "list": 300,
            },
            "@network": {
                "_cost": 1000,
                "http": {
                    "_cost": 1000,
                    "get": 500,
                    "post": 1500,
                    "put": 1500,
                    "delete": 1000,
                },
                "dns": 200,
            },
            "@time": {
                "_cost": 20,
                "now": 10,
                "sleep": 10000,  # Very expensive (DOS risk)
                "format": 50,
            },
            "@math": {
                "_cost": 10,
                "random": 20,
                "sqrt": 15,
                "pow": 20,
            },
            "@crypto": {
                "_cost": 1000,
                "hash": 100,
                "hmac": 200,
                "sign": 2000,
                "verify": 2000,
                "random": 50,
            },
            "@system": {
                "_cost": 5000,
                "env": 100,
                "arch": 50,
                "pid": 50,
            },
            "@json": {
                "_cost": 100,
                "parse": 200,
                "stringify": 200,
            },
        }
    
    def get_cost(self, operation: str) -> int:
        """
        Get gas cost for a host operation.
        
        Args:
            operation: Host operation path (e.g., "@file/read")
            
        Returns:
            Gas cost for the operation
        """
        # Handle non-@ operations
        if not operation.startswith("@"):
            return GasCost.HOST_DEFAULT
        
        # Split path and walk tree
        parts = operation.split('/')
        current = self.cost_tree
        cost = GasCost.HOST_DEFAULT
        
        for part in parts:
            if isinstance(current, dict):
                if part in current:
                    node = current[part]
                    if isinstance(node, int):
                        return node  # Found exact cost
                    elif isinstance(node, dict):
                        if "_cost" in node:
                            cost = node["_cost"]  # Update inherited cost
                        current = node
                    else:
                        current = node
                elif "_cost" in current:
                    cost = current["_cost"]
                    break
            elif isinstance(current, int):
                return current
        
        return cost


class ResourceLimits:
    """Configuration for resource limits."""
    
    def __init__(self,
                 max_gas: Optional[int] = None,
                 max_memory: Optional[int] = None,
                 max_time_ms: Optional[int] = None,
                 max_stack_depth: Optional[int] = 100,
                 max_collection_size: Optional[int] = 10000,
                 max_string_length: Optional[int] = 100000):
        self.max_gas = max_gas
        self.max_memory = max_memory
        self.max_time_ms = max_time_ms
        self.max_stack_depth = max_stack_depth
        self.max_collection_size = max_collection_size
        self.max_string_length = max_string_length


class ResourceExhausted(Exception):
    """Base exception for resource exhaustion."""
    pass


class GasExhausted(ResourceExhausted):
    """Raised when gas limit is exceeded."""
    pass


class MemoryExhausted(ResourceExhausted):
    """Raised when memory limit is exceeded."""
    pass


class TimeExhausted(ResourceExhausted):
    """Raised when time limit is exceeded."""
    pass


class StackOverflow(ResourceExhausted):
    """Raised when stack depth limit is exceeded."""
    pass


class ResourceBudget:
    """
    Comprehensive resource tracking for secure JSL execution.
    
    Tracks gas consumption, memory allocation, execution time,
    and stack depth to prevent DOS attacks and ensure fair
    resource allocation.
    """
    
    def __init__(self, 
                 limits: Optional[ResourceLimits] = None,
                 host_gas_policy: Optional[HostGasPolicy] = None):
        """
        Initialize resource budget.
        
        Args:
            limits: Resource limits configuration
            host_gas_policy: Gas cost policy for host operations
        """
        self.limits = limits or ResourceLimits()
        self.host_gas_policy = host_gas_policy or HostGasPolicy()
        
        # Current usage
        self.gas_used = 0
        self.memory_used = 0
        self.start_time = time.monotonic()  # Start tracking time from creation
        self.stack_depth = 0
        
        # For tracking collections
        self.object_count = 0
    
    def consume_gas(self, amount: int, operation: str = ""):
        """
        Consume gas for an operation.
        
        Args:
            amount: Gas amount to consume
            operation: Description of operation (for error messages)
            
        Raises:
            GasExhausted: If gas limit would be exceeded
        """
        if self.limits.max_gas is None:
            return
        
        self.gas_used += amount
        if self.gas_used > self.limits.max_gas:
            raise GasExhausted(
                f"Gas limit {self.limits.max_gas} exceeded "
                f"(used {self.gas_used}) at {operation}"
            )
    
    def consume_host_gas(self, operation: str):
        """
        Consume gas for a host operation based on namespace.
        
        Args:
            operation: Host operation path (e.g., "@file/read")
        """
        cost = self.host_gas_policy.get_cost(operation)
        self.consume_gas(cost, f"host:{operation}")
    
    def allocate_memory(self, bytes_count: int, description: str = ""):
        """
        Account for memory allocation.
        
        Args:
            bytes_count: Number of bytes to allocate
            description: Description of allocation
            
        Raises:
            MemoryExhausted: If memory limit would be exceeded
        """
        if self.limits.max_memory is None:
            return
        
        self.memory_used += bytes_count
        if self.memory_used > self.limits.max_memory:
            raise MemoryExhausted(
                f"Memory limit {self.limits.max_memory} exceeded "
                f"(used {self.memory_used}): {description}"
            )
    
    def check_time(self):
        """
        Check if time limit has been exceeded.
        
        Raises:
            TimeExhausted: If time limit has been exceeded
        """
        if self.limits.max_time_ms is None:
            return
        
        elapsed_ms = (time.monotonic() - self.start_time) * 1000
        if elapsed_ms > self.limits.max_time_ms:
            raise TimeExhausted(
                f"Time limit {self.limits.max_time_ms}ms exceeded "
                f"(elapsed {elapsed_ms:.1f}ms)",
            )
    
    def enter_call(self):
        """
        Enter a function call (increase stack depth).
        
        Raises:
            StackOverflow: If stack depth limit would be exceeded
        """
        self.stack_depth += 1
        if (self.limits.max_stack_depth is not None and 
            self.stack_depth > self.limits.max_stack_depth):
            raise StackOverflow(
                f"Stack depth {self.limits.max_stack_depth} exceeded",
            )
    
    def exit_call(self):
        """Exit a function call (decrease stack depth)."""
        self.stack_depth = max(0, self.stack_depth - 1)
    
    def check_collection_size(self, size: int):
        """
        Check if a collection size is within limits.
        
        Args:
            size: Size of the collection
            
        Raises:
            MemoryExhausted: If collection size exceeds limit
        """
        if self.limits.max_collection_size and size > self.limits.max_collection_size:
            raise MemoryExhausted(
                f"Collection size {size} exceeds limit {self.limits.max_collection_size}",
            )
    
    def check_string_length(self, length: int):
        """
        Check if a string length is within limits.
        
        Args:
            length: Length of the string
            
        Raises:
            MemoryExhausted: If string length exceeds limit
        """
        if self.limits.max_string_length and length > self.limits.max_string_length:
            raise MemoryExhausted(
                f"String length {length} exceeds limit {self.limits.max_string_length}",
            )
    
    def check_result(self, result: Any) -> None:
        """
        Check resource constraints for a computed result.
        
        This centralizes checking for collection sizes, string lengths, etc.
        
        Args:
            result: The result value to check
        """
        if result is None:
            return
        
        if isinstance(result, list):
            self.check_collection_size(len(result))
            # Track memory for the list
            self.allocate_memory(
                len(result) * 8,  # Rough estimate: 8 bytes per element
                f"list of size {len(result)}"
            )
        elif isinstance(result, str):
            self.check_string_length(len(result))
            # Track memory for the string
            self.allocate_memory(
                len(result) * 2,  # 2 bytes per character for Unicode
                f"string of length {len(result)}"
            )
        elif isinstance(result, dict):
            self.check_collection_size(len(result))
            # Track memory for the dict
            self.allocate_memory(
                len(result) * 24,  # Rough estimate for dict overhead
                f"dict of size {len(result)}"
            )
        # For other types, we don't need special checking
    
    def checkpoint(self) -> Dict[str, Any]:
        """
        Create a checkpoint of current resource usage.
        
        Returns:
            Dictionary with current resource usage
        """
        return {
            "gas_used": self.gas_used,
            "memory_used": self.memory_used,
            "stack_depth": self.stack_depth,
            "elapsed_ms": (time.monotonic() - self.start_time) * 1000,
            "object_count": self.object_count,
        }
    
    def restore(self, checkpoint: Dict[str, Any]):
        """
        Restore resource usage from a checkpoint.
        
        Args:
            checkpoint: Previously saved checkpoint
        """
        self.gas_used = checkpoint.get("gas_used", 0)
        self.memory_used = checkpoint.get("memory_used", 0)
        self.stack_depth = checkpoint.get("stack_depth", 0)
        self.object_count = checkpoint.get("object_count", 0)
        
        # Adjust start time to account for elapsed time
        elapsed = checkpoint.get("elapsed_ms", 0) / 1000
        self.start_time = time.monotonic() - elapsed