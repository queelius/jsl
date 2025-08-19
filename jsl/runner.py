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
from .compiler import compile_to_postfix, decompile_from_postfix
from .stack_evaluator import StackEvaluator
from .sexp import from_canonical_sexp

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
                 host_gas_policy: Optional[HostGasPolicy] = None,
                 use_recursive_evaluator: bool = False):
        """
        Initialize JSL runner.
        
        Args:
            config: Configuration options (recursion depth, debugging, etc.)
            security: Security settings (allowed commands, sandbox mode, etc.)
            resource_limits: Resource limits for execution
            host_gas_policy: Gas cost policy for host operations
            use_recursive_evaluator: If True, use recursive evaluator instead of stack (default: False)
        """
        self.config = config or {}
        self.security = security or {}
        self.use_recursive_evaluator = use_recursive_evaluator
        
        # Set up host dispatcher
        self.host_dispatcher = HostDispatcher()
        
        # Set up base environment - keep prelude separate
        self.prelude = make_prelude()
        # Working environment extends the prelude (can be modified)
        self.base_environment = self.prelude.extend({})
        
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
        
        # Set up evaluators
        if use_recursive_evaluator:
            # Recursive evaluator as reference implementation
            self.recursive_evaluator = Evaluator(
                self.host_dispatcher, 
                resource_limits=resource_limits,
                host_gas_policy=host_gas_policy
            )
            self.stack_evaluator = None
        else:
            # Stack evaluator is the default for production use
            # Create resource budget if we have limits
            budget = None
            if resource_limits:
                from .resources import ResourceBudget
                budget = ResourceBudget(resource_limits, host_gas_policy)
            self.stack_evaluator = StackEvaluator(
                env=self.base_environment,
                resource_budget=budget,
                host_dispatcher=self.host_dispatcher
            )
            self.recursive_evaluator = None
        
        # Keep backward compatibility - evaluator points to the active one
        self.evaluator = self.recursive_evaluator if use_recursive_evaluator else self.stack_evaluator
        
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
        # Apply recursion depth limit if supported (only for recursive evaluator)
        if self.use_recursive_evaluator:
            max_depth = self.config.get('max_recursion_depth', 1000)
            if hasattr(self.recursive_evaluator, 'max_recursion_depth'):
                self.recursive_evaluator.max_recursion_depth = max_depth
        
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
    
    def _detect_format(self, expression: Any) -> str:
        """
        Detect the format of the input expression.
        
        Returns:
            'lisp': S-expression Lisp style (string with parens)
            'json': S-expression JSON style (JSON array)
            'jpn': JPN postfix compiled style
        """
        # If it's a string, check if it's Lisp-style
        if isinstance(expression, str):
            stripped = expression.strip()
            if stripped.startswith('(') and stripped.endswith(')'):
                return 'lisp'
            # Otherwise assume JSON (will error if not valid)
            return 'json'
        else:
            # Already parsed, detect format
            return self._detect_parsed_format(expression)
    
    def _detect_parsed_format(self, expression: Any) -> str:
        """
        Detect format of a parsed expression.
        
        JPN format characteristics:
        - Flat list (no nested lists except at top level)
        - Contains integers that aren't at the start (arities)
        - Pattern: [..., int, string, ...] where int is arity
        
        JSON S-expression characteristics:
        - First element is typically a string (operator)
        - May contain nested lists
        """
        if not isinstance(expression, list):
            # Single value, treat as JSON S-expression
            return 'json'
        
        if len(expression) == 0:
            return 'json'
        
        # Check for JPN patterns
        # JPN has flat structure with [literal/var, ..., arity, op] patterns
        has_nested = False
        has_arity_pattern = False
        
        for i, elem in enumerate(expression):
            if isinstance(elem, list):
                has_nested = True
            # Check for arity pattern: integer followed by string (operator)
            if isinstance(elem, int) and i > 0 and i < len(expression) - 1:
                next_elem = expression[i + 1]
                if isinstance(next_elem, str) and not next_elem.startswith('@'):
                    # Found arity-operator pattern
                    has_arity_pattern = True
        
        # JPN should not have nested lists and should have arity patterns
        if not has_nested and has_arity_pattern:
            return 'jpn'
        
        # Default to JSON S-expression
        return 'json'
    
    def execute(self, expression: Union[str, JSLExpression]) -> JSLValue:
        """
        Execute a JSL expression.
        
        Supports multiple input formats:
        - S-expression Lisp style: "(+ 1 2 3)"
        - S-expression JSON style: "[\"+\", 1, 2, 3]"
        - JPN postfix compiled: "[1, 2, 3, 3, \"+\"]"
        
        Args:
            expression: JSL expression as string or parsed structure
            
        Returns:
            The result of evaluating the expression
            
        Raises:
            JSLSyntaxError: If the expression is malformed
            JSLRuntimeError: If execution fails
        """
        start_time = time.time() if self._profiling_enabled else None
        
        try:
            # Detect format and parse accordingly
            format_type = self._detect_format(expression)
            parse_start = time.time() if self._profiling_enabled else None
            
            if format_type == 'lisp':
                # Parse Lisp-style S-expressions
                if isinstance(expression, str):
                    expression = from_canonical_sexp(expression)
                else:
                    raise JSLSyntaxError("Lisp format detected but expression is not a string")
            elif isinstance(expression, str):
                # Try to parse as JSON
                try:
                    expression = json.loads(expression)
                except json.JSONDecodeError:
                    # If it's a simple identifier (variable name), keep it as-is
                    # This allows execute("x") to work for variable lookup
                    if expression.isidentifier() or expression.startswith('@'):
                        expression = expression
                    else:
                        # Invalid JSON that's not a simple identifier
                        raise JSLSyntaxError(f"Invalid expression: {expression}")
            
            # Re-detect format after parsing
            if isinstance(expression, list):
                format_type = self._detect_parsed_format(expression)
            
            if self._profiling_enabled and parse_start:
                self._performance_stats['parse_time_ms'] = (time.time() - parse_start) * 1000
                self._performance_stats['input_format'] = format_type
            
            # Execute the expression
            eval_start = time.time() if self._profiling_enabled else None
            
            # Don't reset resources - they persist across executions
            # If users want fresh resources, they should create a new Runner
            
            try:
                if format_type == 'jpn':
                    # Already in JPN format, use stack evaluator directly
                    if self.use_recursive_evaluator:
                        # Need to decompile JPN back to S-expression for recursive evaluator
                        expression = decompile_from_postfix(expression)
                        result = self.recursive_evaluator.eval(expression, self.base_environment)
                    else:
                        result = self.stack_evaluator.eval(expression, env=self.base_environment)
                else:
                    # S-expression format (json or lisp parsed to json)
                    if self.use_recursive_evaluator:
                        # Use recursive evaluator directly
                        result = self.recursive_evaluator.eval(expression, self.base_environment)
                    else:
                        # Compile to JPN and use stack evaluator
                        jpn = compile_to_postfix(expression)
                        result = self.stack_evaluator.eval(jpn, env=self.base_environment)
                
                # Record performance stats
                if self._profiling_enabled:
                    if eval_start:
                        self._performance_stats['eval_time_ms'] = (time.time() - eval_start) * 1000
                    if start_time:
                        self._performance_stats['total_time_ms'] = (time.time() - start_time) * 1000
                    
                    # Resource usage stats (only for recursive evaluator currently)
                    if self.use_recursive_evaluator and self.recursive_evaluator.resources:
                        checkpoint = self.recursive_evaluator.resources.checkpoint()
                        self._performance_stats['gas_used'] = checkpoint.get('gas_used', 0)
                        self._performance_stats['memory_used'] = checkpoint.get('memory_used', 0)
                        self._performance_stats['stack_depth_max'] = checkpoint.get('stack_depth', 0)
                    
                    # Track call count
                    self._performance_stats['call_count'] = self._performance_stats.get('call_count', 0) + 1
                
                return result
                
            except ResourceExhausted as e:
                # Record resource exhaustion in stats
                if self._profiling_enabled:
                    if self.use_recursive_evaluator and self.recursive_evaluator.resources:
                        checkpoint = self.recursive_evaluator.resources.checkpoint()
                        self._performance_stats['resources_exhausted'] = True
                        self._performance_stats['gas_used'] = checkpoint.get('gas_used', 0)
                        self._performance_stats['memory_used'] = checkpoint.get('memory_used', 0)
                
                # Re-raise directly - ResourceExhausted is already informative
                # The evaluator will have already set remaining_expr and env if needed
                raise
            
        except Exception as e:
            if self._profiling_enabled and start_time:
                self._performance_stats['error_time_ms'] = (time.time() - start_time) * 1000
                self._performance_stats['error_count'] = self._performance_stats.get('error_count', 0) + 1
            
            if isinstance(e, (JSLSyntaxError, JSLRuntimeError, ResourceExhausted)):
                raise
            else:
                raise JSLRuntimeError(f"Execution failed: {e}")
    
    @contextmanager
    def new_environment(self):
        """
        Create a new isolated environment context.
        
        Yields:
            ExecutionContext: New execution context
        """
        # Create new environment extending the current base environment
        # This allows access to variables defined in the parent context
        new_env = self.base_environment.extend({})        
        context = ExecutionContext(new_env)
        
        # Create temporary runner for this context with same configuration
        temp_runner = JSLRunner(
            self.config, 
            self.security,
            use_recursive_evaluator=self.use_recursive_evaluator
        )
        temp_runner.base_environment = new_env
        
        # Update the stack evaluator's default env (if it exists)
        # Both evaluators receive env as parameter, but stack evaluator also
        # needs its internal env updated for variable lookups during evaluation
        if temp_runner.stack_evaluator:
            temp_runner.stack_evaluator.env = new_env
        
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
    
    # Note: Resumption is not supported in the recursive evaluator.
    # For resumable execution, use the stack-based evaluator which
    # compiles to JPN (JSL Postfix Notation) and can serialize its
    # execution state exactly.
    
        

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
        if runner.use_recursive_evaluator:
            runner.recursive_evaluator.host = host_dispatcher
        else:
            # Stack evaluator also needs the host dispatcher
            runner.stack_evaluator.host_dispatcher = host_dispatcher
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
        if runner.use_recursive_evaluator:
            runner.recursive_evaluator.host = host_dispatcher
    if environment:
        runner.base_environment = environment
        # Both evaluators now handle Env consistently
        if runner.stack_evaluator:
            runner.stack_evaluator.env = environment
    
    return runner.execute(expression)


def create_repl_environment() -> Env:
    """
    Create an environment suitable for REPL usage.
    
    Returns:
        A fresh environment with the prelude loaded
    """
    prelude = make_prelude()
    # Return an extended environment that can be modified
    return prelude.extend({})
