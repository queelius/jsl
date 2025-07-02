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
from .prelude import make_prelude


class JSLRuntimeError(Exception):
    """Runtime error during JSL execution."""
    pass


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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, security: Optional[Dict[str, Any]] = None):
        """
        Initialize JSL runner.
        
        Args:
            config: Configuration options (recursion depth, debugging, etc.)
            security: Security settings (allowed commands, sandbox mode, etc.)
        """
        self.config = config or {}
        self.security = security or {}
        
        # Set up host dispatcher
        self.host_dispatcher = HostDispatcher()
        
        # Set up base environment
        self.base_environment = make_prelude()
        
        # Set up evaluator
        self.evaluator = Evaluator(self.host_dispatcher)
        
        # Performance tracking
        self._profiling_enabled = False
        self._performance_stats = {}
        
        # Apply configuration
        self._apply_config()
    
    def _apply_config(self):
        """Apply configuration settings."""
        # Apply security settings
        if self.security.get('allowed_host_commands'):
            # Filter host commands based on allowed list
            pass
        
        if self.security.get('sandbox_mode', False):
            # Enable sandbox mode
            pass
    
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
                try:
                    expression = json.loads(expression)
                except json.JSONDecodeError as e:
                    raise JSLSyntaxError(f"Invalid JSON in expression: {e}")
            
            # Execute the expression
            result = self.evaluator.eval(expression, self.base_environment)
            
            # Record performance stats
            if self._profiling_enabled and start_time:
                execution_time = (time.time() - start_time) * 1000
                self._performance_stats['execution_time_ms'] = execution_time
            
            return result
            
        except Exception as e:
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
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return self._performance_stats.copy()
    
    def define_function(self, name: str, params: List[str], body: JSLExpression) -> None:
        """
        Define a function using the lambda special form.
        
        Args:
            name: Function name
            params: Parameter names
            body: Function body expression
        """
        lambda_expr = ["lambda", params, body]
        self.define(name, self.execute(lambda_expr))
    
    def create_lambda(self, params: List[str], body: JSLExpression) -> JSLValue:
        """
        Create a lambda function.
        
        Args:
            params: Parameter names
            body: Function body expression
            
        Returns:
            Function closure
        """
        return self.execute(["lambda", params, body])
    
    def conditional(self, condition: JSLExpression, then_expr: JSLExpression, else_expr: JSLExpression = None) -> JSLValue:
        """
        Execute conditional expression.
        
        Args:
            condition: Condition to evaluate
            then_expr: Expression to evaluate if condition is truthy
            else_expr: Expression to evaluate if condition is falsy
            
        Returns:
            Result of the appropriate branch
        """
        if else_expr is None:
            else_expr = None
        return self.execute(["if", condition, then_expr, else_expr])
    
    def let_binding(self, bindings: Dict[str, JSLExpression], body: JSLExpression) -> JSLValue:
        """
        Execute expression with local bindings.
        
        Args:
            bindings: Dictionary of variable names to expressions
            body: Expression to evaluate with bindings
            
        Returns:
            Result of body expression
        """
        binding_list = [[name, expr] for name, expr in bindings.items()]
        return self.execute(["let", binding_list, body])
    
    def do_sequence(self, *expressions: JSLExpression) -> JSLValue:
        """
        Execute expressions in sequence.
        
        Args:
            *expressions: Expressions to execute in order
            
        Returns:
            Result of the last expression
        """
        return self.execute(["do"] + list(expressions))
    
    def quote(self, expression: JSLExpression) -> JSLValue:
        """
        Quote an expression (prevent evaluation).
        
        Args:
            expression: Expression to quote
            
        Returns:
            The expression as literal data
        """
        return self.execute(["quote", expression])
    
    def try_catch(self, body: JSLExpression, handler: JSLExpression) -> JSLValue:
        """
        Execute expression with error handling.
        
        Args:
            body: Expression to execute
            handler: Handler function for errors
            
        Returns:
            Result of body or handler
        """
        return self.execute(["try", body, handler])
    
    def host_command(self, command: str, *args: Any) -> JSLValue:
        """
        Execute a host command.
        
        Args:
            command: Host command name
            *args: Command arguments
            
        Returns:
            Result from host command
        """
        return self.execute(["host", command] + list(args))
    
    def evaluate_special_form(self, form: str, *args: JSLExpression) -> JSLValue:
        """
        Evaluate a special form directly.
        
        Args:
            form: Special form name (def, lambda, if, let, do, quote, try, host)
            *args: Special form arguments
            
        Returns:
            Result of special form evaluation
        """
        return self.execute([form] + list(args))
    
    def get_special_forms(self) -> List[str]:
        """
        Get list of supported special forms.
        
        Returns:
            List of special form names
        """
        return ["def", "lambda", "if", "let", "do", "quote", "@", "try", "host"]
    
    def validate_special_form(self, form: str, args: List[JSLExpression]) -> bool:
        """
        Validate special form syntax.
        
        Args:
            form: Special form name
            args: Arguments to the special form
            
        Returns:
            True if valid, False otherwise
        """
        validations = {
            "def": lambda a: len(a) == 2 and isinstance(a[0], str),
            "lambda": lambda a: len(a) == 2 and isinstance(a[0], list),
            "if": lambda a: len(a) in [2, 3],
            "let": lambda a: len(a) == 2 and isinstance(a[0], list),
            "do": lambda a: len(a) >= 1,
            "quote": lambda a: len(a) == 1,
            "@": lambda a: len(a) == 1,
            "try": lambda a: len(a) == 2,
            "host": lambda a: len(a) >= 1
        }
        
        if form not in validations:
            return False
        
        try:
            return validations[form](args)
        except:
            return False
    
    def get_special_form_help(self, form: str) -> str:
        """
        Get help text for a special form.
        
        Args:
            form: Special form name
            
        Returns:
            Help text describing the special form
        """
        help_text = {
            "def": "def - Define a variable: ['def', 'name', value_expr]",
            "lambda": "lambda - Create function: ['lambda', ['param1', 'param2'], body_expr]", 
            "if": "if - Conditional: ['if', condition, then_expr, else_expr]",
            "let": "let - Local bindings: ['let', [['var1', val1], ['var2', val2]], body_expr]",
            "do": "do - Sequential execution: ['do', expr1, expr2, ...]",
            "quote": "quote - Prevent evaluation: ['quote', expr] or ['@', expr]",
            "@": "@ - Shorthand quote: ['@', expr] same as ['quote', expr]",
            "try": "try - Error handling: ['try', body_expr, handler_expr]",
            "host": "host - Host command: ['host', 'command', arg1, arg2, ...]"
        }
        
        return help_text.get(form, f"Unknown special form: {form}")
    
    def explain_evaluation(self, expression: JSLExpression) -> str:
        """
        Explain how an expression would be evaluated.
        
        Args:
            expression: Expression to explain
            
        Returns:
            Explanation of evaluation steps
        """
        if not isinstance(expression, list) or len(expression) == 0:
            return f"Literal value: {expression}"
        
        form = expression[0]
        if form in self.get_special_forms():
            explanations = {
                "def": "Define variable - evaluates value and binds to name",
                "lambda": "Create function - captures current environment as closure",
                "if": "Conditional - evaluates condition, then one branch only",
                "let": "Local binding - creates temporary scope with new variables",
                "do": "Sequential - evaluates all expressions, returns last result",
                "quote": "Quote - returns expression without evaluation",
                "@": "Quote shorthand - returns expression without evaluation", 
                "try": "Error handling - evaluates body, calls handler on error",
                "host": "Host command - evaluates args and sends to host system"
            }
            return f"Special form '{form}': {explanations.get(form, 'Unknown')}"
        else:
            return f"Function call - evaluates '{form}' and all arguments, then calls function"
        

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
        runner.host_dispatcher = host_dispatcher
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
        runner.host_dispatcher = host_dispatcher
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
