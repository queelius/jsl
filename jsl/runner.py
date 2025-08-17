"""
JSL Runner - High-level execution interface

This module provides the JSLRunner class and related utilities for executing
JSL programs with advanced features like environment management, host interaction,
and performance monitoring.
"""

import json
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union

from .core import Evaluator, Env, HostDispatcher, JSLValue, JSLExpression, Closure
from .resources import ResourceLimits, ResourceBudget, HostGasPolicy, ResourceExhausted
from .prelude import make_prelude


class JSLRuntimeError(Exception):
    """Runtime error during JSL execution."""
    def __init__(self, message: str, remaining_expr=None, env=None):
        super().__init__(message)
        self.remaining_expr = remaining_expr
        self.env = env


class JSLSyntaxError(Exception):
    """Syntax error in JSL code."""
    pass


class ExecutionContext:
    """Context for a single execution session."""
    
    def __init__(self, environment: Env, parent: Optional['ExecutionContext'] = None):
        self.environment = environment
        self.parent = parent
        self.start_time = time.time()
        self.memory_used = 0
    
    def define(self, name: str, value: Any) -> None:
        """Define a variable in this context."""
        self.environment.define(name, value)
    
    def get_variable(self, name: str) -> Any:
        """Get a variable from this context."""
        try:
            return self.environment.get(name)
        except KeyError:
            raise JSLRuntimeError(f"Undefined variable: {name}")


class JSLRunner:
    """
    High-level JSL execution engine with advanced features.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 security: Optional[Dict[str, Any]] = None,
                 resource_limits: Optional[ResourceLimits] = None,
                 host_gas_policy: Optional[HostGasPolicy] = None):
        """
        Initialize JSL runner.
        
        Args:
            config: Configuration options (recursion depth, debugging, etc.)
            security: Security settings (allowed commands, sandbox mode, etc.)
            resource_limits: Resource limits for execution
            host_gas_policy: Gas cost policy for host operations
        """
        self.config = config or {}
        self.security = security or {}
        
        # Set up host dispatcher
        self.host_dispatcher = HostDispatcher()
        
        # Set up base environment
        self.base_environment = make_prelude()
        
        # Set up resource limits
        if resource_limits is None and self.config:
            # Build from config
            resource_limits = ResourceLimits(
                max_gas=self.config.get('max_gas'),
                max_memory=self.config.get('max_memory'),
                max_time_ms=self.config.get('max_time_ms'),
                max_stack_depth=self.config.get('max_stack_depth'),
                max_collection_size=self.config.get('max_collection_size'),
                max_string_length=self.config.get('max_string_length')
            )
        
        # Set up evaluator with resource limits
        self.evaluator = Evaluator(
            self.host_dispatcher, 
            resource_limits=resource_limits
        )
        
        # Store for reference
        self.resource_limits = resource_limits
        self.host_gas_policy = host_gas_policy
        
        # Performance tracking
        self._profiling_enabled = False
        self._performance_stats = {}
        
        # Apply configuration
        self._apply_config()
    
    def _apply_config(self):
        """Apply configuration settings."""
        # Apply recursion depth limit if supported
        max_depth = self.config.get('max_recursion_depth', 1000)
        if hasattr(self.evaluator, 'max_recursion_depth'):
            self.evaluator.max_recursion_depth = max_depth
        
        # Apply security settings for host commands
        allowed_commands = self.security.get('allowed_host_commands')
        if allowed_commands is not None:
            # Wrap the host dispatcher to restrict commands
            original_dispatch = self.host_dispatcher.dispatch
            
            def restricted_dispatch(command, args):
                if command not in allowed_commands:
                    raise JSLRuntimeError(f"Host command '{command}' not allowed by security policy")
                return original_dispatch(command, args)
            
            self.host_dispatcher.dispatch = restricted_dispatch
        
        if self.security.get('sandbox_mode', False):
            # In sandbox mode, disable all host commands unless explicitly allowed
            if allowed_commands is None:
                def no_host_dispatch(command, args):
                    raise JSLRuntimeError(f"Host commands disabled in sandbox mode")
                self.host_dispatcher.dispatch = no_host_dispatch
    
    def execute(self, expression: Union[str, JSLExpression]) -> JSLValue:
        """
        Execute a JSL expression.
        
        Args:
            expression: JSL expression as JSON string or parsed structure
            
        Returns:
            The result of evaluating the expression
            
        Raises:
            JSLSyntaxError: If the expression is malformed
            JSLRuntimeError: If execution fails
        """
        start_time = time.time() if self._profiling_enabled else None
        
        try:
            # Parse expression if it's a string
            if isinstance(expression, str):
                parse_start = time.time() if self._profiling_enabled else None
                try:
                    expression = json.loads(expression)
                except json.JSONDecodeError as e:
                    raise JSLSyntaxError(f"Invalid JSON in expression: {e}")
                
                if self._profiling_enabled and parse_start:
                    self._performance_stats['parse_time_ms'] = (time.time() - parse_start) * 1000
            
            # Execute the expression
            eval_start = time.time() if self._profiling_enabled else None
            
            # Reset resource tracking for this execution
            if self.evaluator.resources:
                # Create fresh budget for this execution
                self.evaluator.resources = ResourceBudget(
                    self.resource_limits,
                    self.host_gas_policy
                )
            
            try:
                result = self.evaluator.eval(expression, self.base_environment)
                
                # Record performance stats
                if self._profiling_enabled:
                    if eval_start:
                        self._performance_stats['eval_time_ms'] = (time.time() - eval_start) * 1000
                    if start_time:
                        self._performance_stats['total_time_ms'] = (time.time() - start_time) * 1000
                    
                    # Resource usage stats
                    if self.evaluator.resources:
                        checkpoint = self.evaluator.resources.checkpoint()
                        self._performance_stats['gas_used'] = checkpoint.get('gas_used', 0)
                        self._performance_stats['memory_used'] = checkpoint.get('memory_used', 0)
                        self._performance_stats['stack_depth_max'] = checkpoint.get('stack_depth', 0)
                    
                    # Track call count
                    self._performance_stats['call_count'] = self._performance_stats.get('call_count', 0) + 1
                
                return result
                
            except ResourceExhausted as e:
                # Record resource exhaustion in stats
                if self._profiling_enabled:
                    if self.evaluator.resources:
                        checkpoint = self.evaluator.resources.checkpoint()
                        self._performance_stats['resources_exhausted'] = True
                        self._performance_stats['gas_used'] = checkpoint.get('gas_used', 0)
                        self._performance_stats['memory_used'] = checkpoint.get('memory_used', 0)
                
                # Re-raise with context for potential resumption
                raise JSLRuntimeError(
                    str(e),
                    remaining_expr=getattr(e, 'remaining_expr', None),
                    env=getattr(e, 'env', None)
                ) from e
            
        except Exception as e:
            if self._profiling_enabled and start_time:
                self._performance_stats['error_time_ms'] = (time.time() - start_time) * 1000
                self._performance_stats['error_count'] = self._performance_stats.get('error_count', 0) + 1
            
            if isinstance(e, (JSLSyntaxError, JSLRuntimeError)):
                raise
            else:
                raise JSLRuntimeError(f"Execution failed: {e}")
    
    def define(self, name: str, value: Any) -> None:
        """
        Define a variable in the base environment.
        
        Args:
            name: Variable name
            value: Variable value
        """
        self.base_environment.define(name, value)
    
    def get_variable(self, name: str) -> Any:
        """
        Get a variable from the base environment.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value
            
        Raises:
            JSLRuntimeError: If variable is not defined
        """
        try:
            return self.base_environment.get(name)
        except KeyError:
            raise JSLRuntimeError(f"Undefined variable: {name}")
    
    @contextmanager
    def new_environment(self):
        """
        Create a new isolated environment context.
        
        Yields:
            ExecutionContext: New execution context
        """
        # Create new environment extending the base
        new_env = self.base_environment.extend({})
        context = ExecutionContext(new_env)
        
        # Create temporary runner for this context
        temp_runner = JSLRunner(self.config, self.security)
        temp_runner.base_environment = new_env
        
        try:
            yield temp_runner
        finally:
            # Cleanup happens automatically when context exits
            pass
    
    def add_host_handler(self, command: str, handler: Any) -> None:
        """
        Add a host command handler.
        
        Args:
            command: Command name (e.g., "file", "time")
            handler: Handler object or function
        """
        # Check security restrictions
        allowed_commands = self.security.get('allowed_host_commands')
        if allowed_commands and command not in allowed_commands:
            raise JSLRuntimeError(f"Host command '{command}' not allowed by security policy")
        
        self.host_dispatcher.register(command, handler)
    
    def enable_profiling(self) -> None:
        """Enable performance profiling."""
        self._profiling_enabled = True
        self._performance_stats = {}
    
    def disable_profiling(self) -> None:
        """Disable performance profiling."""
        self._profiling_enabled = False
    
    def reset_performance_stats(self) -> None:
        """Reset performance statistics."""
        self._performance_stats = {}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics including:
            - total_time_ms: Total execution time
            - parse_time_ms: Time spent parsing JSON
            - eval_time_ms: Time spent evaluating
            - call_count: Number of execute() calls
            - error_count: Number of errors encountered
            - gas_used: Amount of gas consumed (if resource limits are set)
            - resources_exhausted: True if resource limits were hit
        """
        return self._performance_stats.copy()
    
    def resume(self, expression: JSLExpression, env: Optional[Env] = None, additional_gas: Optional[int] = None) -> JSLValue:
        """
        Resume execution from where it was interrupted by resource limits.
        
        Args:
            expression: The remaining expression to evaluate
            env: The environment at interruption (if available)
            additional_gas: Additional gas to allow (if not set, uses original limit)
            
        Returns:
            The result of continuing evaluation
        """
        # Use provided environment or base environment
        resume_env = env if env is not None else self.base_environment
        
        # Temporarily adjust gas limit if requested
        if additional_gas is not None and self.evaluator.resources:
            # Add more gas to the budget
            checkpoint = self.evaluator.resources.checkpoint()
            current_gas = checkpoint.get('gas_used', 0)
            new_limit = current_gas + additional_gas
            # Create new resource limits with updated gas
            new_limits = ResourceLimits(
                max_gas=new_limit,
                max_memory=self.resource_limits.max_memory if self.resource_limits else None,
                max_time_ms=self.resource_limits.max_time_ms if self.resource_limits else None,
                max_stack_depth=self.resource_limits.max_stack_depth if self.resource_limits else None,
                max_collection_size=self.resource_limits.max_collection_size if self.resource_limits else None,
                max_string_length=self.resource_limits.max_string_length if self.resource_limits else None
            )
            self.evaluator.resources = ResourceBudget(new_limits, self.host_gas_policy)
        
        result = self.evaluator.eval(expression, resume_env)
        return result
    
    # These convenience methods are removed as they just wrap execute()
    # Users should use the fluent API or direct execute() calls instead
    
        

# Backward compatibility functions
def run_program(
    program: Union[str, JSLExpression], 
    host_dispatcher: Optional[HostDispatcher] = None,
    environment: Optional[Env] = None
) -> JSLValue:
    """
    Run a complete JSL program (legacy function).
    
    Args:
        program: JSL code as JSON string or parsed structure
        host_dispatcher: Optional host dispatcher for side effects
        environment: Optional base environment (defaults to prelude)
    
    Returns:
        The result of evaluating the program
    """
    runner = JSLRunner()
    if host_dispatcher:
        # Replace both references to the host dispatcher
        runner.host_dispatcher = host_dispatcher
        runner.evaluator.host = host_dispatcher
    if environment:
        runner.base_environment = environment
    
    return runner.execute(program)


def eval_expression(
    expression: Union[str, JSLExpression],
    environment: Optional[Env] = None,
    host_dispatcher: Optional[HostDispatcher] = None
) -> JSLValue:
    """
    Evaluate a single JSL expression (legacy function).
    
    Args:
        expression: JSL expression as JSON string or parsed structure
        environment: Environment for evaluation (defaults to prelude)
        host_dispatcher: Optional host dispatcher for side effects
    
    Returns:
        The result of evaluating the expression
    """
    runner = JSLRunner()
    if host_dispatcher:
        # Replace both references to the host dispatcher
        runner.host_dispatcher = host_dispatcher
        runner.evaluator.host = host_dispatcher
    if environment:
        runner.base_environment = environment
    
    return runner.execute(expression)


def create_repl_environment() -> Env:
    """
    Create an environment suitable for REPL usage.
    
    Returns:
        A fresh environment with the prelude loaded
    """
    return make_prelude()
