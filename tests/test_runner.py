"""
Unit tests for jsl.runner module
"""

import pytest
import json
import time
from unittest.mock import Mock, patch

from jsl.runner import (
    JSLRunner, JSLRuntimeError, JSLSyntaxError, ExecutionContext,
    run_program, eval_expression, create_repl_environment
)
from jsl.core import Env, HostDispatcher, SymbolNotFoundError


class TestJSLRunner:
    """Test cases for JSLRunner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = JSLRunner()
    
    def test_initialization(self):
        """Test runner initialization."""
        runner = JSLRunner()
        assert runner.config == {}
        assert runner.security == {}
        assert runner.base_environment is not None
        assert runner.evaluator is not None
        assert runner.host_dispatcher is not None
    
    def test_initialization_with_config(self):
        """Test runner initialization with config."""
        config = {"max_recursion_depth": 1000, "debug": True}
        security = {"sandbox_mode": True, "allowed_host_commands": ["file", "time"]}
        
        runner = JSLRunner(config=config, security=security)
        assert runner.config == config
        assert runner.security == security
    
    def test_execute_basic_arithmetic(self):
        """Test executing basic arithmetic expressions."""
        # Addition
        result = self.runner.execute(["+", 1, 2, 3])
        assert result == 6
        
        # Multiplication
        result = self.runner.execute(["*", 4, 5])
        assert result == 20
        
        # Nested operations
        result = self.runner.execute(["+", ["*", 2, 3], ["*", 4, 5]])
        assert result == 26
    
    def test_execute_json_string(self):
        """Test executing JSL expressions from JSON strings."""
        result = self.runner.execute('["+" , 1, 2]')
        assert result == 3
        
        # Test invalid JSON
        with pytest.raises(JSLSyntaxError):
            self.runner.execute('{"invalid": json')
    
    def test_define_and_get_variable(self):
        """Test variable definition and retrieval."""
        self.runner.execute(["def", "x", 42])
        assert self.runner.execute("x") == 42
        
        # Test using defined variable in expression
        result = self.runner.execute(["*", "x", 2])
        assert result == 84
        
        # Test undefined variable - should raise JSLRuntimeError (wrapped)
        with pytest.raises((JSLRuntimeError, SymbolNotFoundError)):
            self.runner.execute("undefined_var")
    
    def test_lambda_functions(self):
        """Test lambda function creation and execution."""
        # Define a square function
        square = self.runner.execute(["lambda", ["x"], ["*", "x", "x"]])
        self.runner.execute(["def", "square", square])
        
        # Use the function
        result = self.runner.execute(["square", 5])
        assert result == 25
    
    def test_conditional_logic(self):
        """Test if expressions."""
        # True condition with else clause
        result = self.runner.execute(["if", [">", 10, 5], "@yes", "@no"])
        assert result == "yes"
        
        # False condition with else clause
        result = self.runner.execute(["if", ["<", 10, 5], "@yes", "@no"])
        assert result == "no"
        
    def test_let_bindings(self):
        """Test let expressions with local bindings."""
        expr = ["let", [["x", 10], ["y", 20]], ["+", "x", "y"]]
        result = self.runner.execute(expr)
        assert result == 30
        
        # Variables should not leak into global scope
        with pytest.raises((JSLRuntimeError, SymbolNotFoundError)):
            self.runner.execute("x")
    
    def test_do_sequences(self):
        """Test do expressions for sequential execution."""
        expr = ["do", 
                ["def", "counter", 0],
                ["def", "counter", ["+", "counter", 1]],
                ["def", "counter", ["+", "counter", 1]],
                "counter"]
        result = self.runner.execute(expr)
        assert result == 2
    
    def test_quote_expressions(self):
        """Test quote expressions."""
        # Using quote
        result = self.runner.execute(["quote", ["+", 1, 2]])
        assert result == ["+", 1, 2]
        
        # Using @ shorthand
        result = self.runner.execute(["@", ["+", 1, 2]])
        assert result == ["+", 1, 2]
    
    def test_list_operations(self):
        """Test list creation and operations."""
        # Create list using quote
        self.runner.execute(["def", "numbers", ["@", [1, 2, 3, 4, 5]]])
        
        # Map over list
        doubled = self.runner.execute([
            "map", 
            ["lambda", ["x"], ["*", "x", 2]], 
            "numbers"
        ])
        assert doubled == [2, 4, 6, 8, 10]
        
        evens = self.runner.execute([
            "filter",
            ["lambda", ["x"], ["=", ["mod", "x", 2], 0]],
            "numbers"
        ])
        assert evens == [2, 4]
    
    def test_error_handling(self):
        """Test error handling with try expressions."""
        # Successful try
        result = self.runner.execute([
            "try",
            ["+", 1, 2],
            ["lambda", ["err"], "@error_occurred"]
        ])
        assert result == 3
        
        # Try with error (division by zero)
        result = self.runner.execute([
            "try",
            ["/", 1, 0],
            ["lambda", ["err"], "@division_by_zero"]
        ])
        assert result == "division_by_zero"
    
    def test_new_environment_context(self):
        """Test isolated environment contexts."""
        self.runner.execute(["def", "global_var", "@global"])
        
        with self.runner.new_environment() as env_runner:
            env_runner.execute(["def", "local_var", "@local"])
            assert env_runner.execute("global_var") == "global"
            assert env_runner.execute("local_var") == "local"
        
        # Local variable should not exist in main runner
        with pytest.raises((JSLRuntimeError, SymbolNotFoundError)):
            self.runner.execute("local_var")
    
    def test_define_function_helper(self):
        """Test define_function using execute with def and lambda."""
        self.runner.execute(["def", "double", ["lambda", ["x"], ["*", "x", 2]]])
        result = self.runner.execute(["double", 5])
        assert result == 10
    
    def test_conditional_helper(self):
        """Test conditional using execute with if."""
        result = self.runner.execute(["if", [">", 5, 3], "@greater", "@lesser"])
        assert result == "greater"
    
    def test_let_binding_helper(self):
        """Test let binding using execute."""
        result = self.runner.execute(["let", [["x", 10], ["y", 20]], ["+", "x", "y"]])
        assert result == 30
    
    def test_do_sequence_helper(self):
        """Test do sequence using execute."""
        result = self.runner.execute(["do",
            ["def", "a", 1],
            ["def", "b", 2], 
            ["+", "a", "b"]
        ])
        assert result == 3
    
    def test_quote_helper(self):
        """Test quote using execute."""
        result = self.runner.execute(["@", ["+", 1, 2]])
        assert result == ["+", 1, 2]
    
    def test_host_command_helper(self):
        """Test host command using execute."""
        # Mock host dispatcher
        mock_handler = Mock(return_value="mocked_result")
        self.runner.add_host_handler("test", mock_handler)
        
        # Use proper quoted string arguments
        result = self.runner.execute(["host", "@test", "@arg1", "@arg2"])
        assert result == "mocked_result"
        mock_handler.assert_called_once()
    
    def test_special_forms_introspection(self):
        """Test that special forms work correctly."""
        # Test basic special forms by using them
        # def
        self.runner.execute(["def", "test_var", 123])
        assert self.runner.execute("test_var") == 123
        
        # lambda
        result = self.runner.execute([["lambda", ["x"], ["*", "x", 2]], 5])
        assert result == 10
        
        # if
        result = self.runner.execute(["if", True, "@yes", "@no"])
        assert result == "yes"
        
        # let
        result = self.runner.execute(["let", [["a", 5]], "a"])
        assert result == 5
        
        # do
        result = self.runner.execute(["do", 1, 2, 3])
        assert result == 3
        
        # quote (@)
        result = self.runner.execute(["@", ["not", "evaluated"]])
        assert result == ["not", "evaluated"]
    
    def test_explain_evaluation(self):
        """Test that evaluation works for different expression types."""
        # Test def
        self.runner.execute(["def", "x", 42])
        assert self.runner.execute("x") == 42
        
        # Test function call
        result = self.runner.execute(["+", 1, 2])
        assert result == 3
        
        # Test literal
        result = self.runner.execute(42)
        assert result == 42
    
    def test_performance_profiling(self):
        """Test performance profiling functionality."""
        self.runner.enable_profiling()
        
        # Execute a simple expression
        self.runner.execute(["+", 1, 2])
        
        stats = self.runner.get_performance_stats()
        # Check for new metric names
        assert "total_time_ms" in stats or "eval_time_ms" in stats
        assert "call_count" in stats
        assert stats["call_count"] == 1
        
        # Execute another expression
        self.runner.execute(["*", 3, 4])
        stats = self.runner.get_performance_stats()
        assert stats["call_count"] == 2
        
        # Test reset
        self.runner.reset_performance_stats()
        stats = self.runner.get_performance_stats()
        assert stats == {}
        
        # Test disable
        self.runner.disable_profiling()
        self.runner.execute(["+", 5, 6])
        stats = self.runner.get_performance_stats()
        assert stats == {}
    
    def test_host_handler_security(self):
        """Test host handler security restrictions."""
        # Create runner with restricted commands
        runner = JSLRunner(security={"allowed_host_commands": ["file"]})
        
        # Should work for allowed command
        mock_handler = Mock(return_value="ok")
        runner.add_host_handler("file", mock_handler)
        
        # Should fail for disallowed command
        with pytest.raises(JSLRuntimeError):
            runner.add_host_handler("network", mock_handler)


class TestExecutionContext:
    """Test cases for ExecutionContext class."""
    
    def test_context_creation(self):
        """Test execution context creation."""
        from jsl.prelude import make_prelude
        env = make_prelude()
        context = ExecutionContext(env)
        
        assert context.environment is env
        assert context.parent is None
        assert isinstance(context.start_time, float)
    
    def test_context_variable_operations(self):
        """Test variable operations in context."""
        from jsl.prelude import make_prelude
        prelude = make_prelude()
        env = prelude.extend({})  # Extend to make modifiable
        context = ExecutionContext(env)
        
        context.define("test_var", 42)
        assert context.get_variable("test_var") == 42
        
        with pytest.raises((JSLRuntimeError, SymbolNotFoundError)):
            context.get_variable("undefined_var")


class TestLegacyFunctions:
    """Test cases for legacy compatibility functions."""
    
    def test_run_program(self):
        """Test run_program legacy function."""
        result = run_program(["+", 1, 2, 3])
        assert result == 6
        
        # Test with JSON string
        result = run_program('["*", 4, 5]')
        assert result == 20
    
    def test_eval_expression(self):
        """Test eval_expression legacy function."""
        result = eval_expression(["-", 10, 3])
        assert result == 7
        
        # Test with custom environment
        from jsl.prelude import make_prelude
        prelude = make_prelude()
        env = prelude.extend({"x": 100})
        result = eval_expression(["*", "x", 2], environment=env)
        assert result == 200
    
    def test_create_repl_environment(self):
        """Test create_repl_environment function."""
        env = create_repl_environment()
        assert env is not None
        
        # Should have prelude functions
        assert env.get("+") is not None
        assert env.get("map") is not None


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_syntax_errors(self):
        """Test syntax error handling."""
        runner = JSLRunner()
        
        # Invalid JSON
        with pytest.raises(JSLSyntaxError):
            runner.execute('{"malformed": json}')
    
    def test_runtime_errors(self):
        """Test runtime error handling."""
        runner = JSLRunner()
        
        # Undefined variable - pass as expression, not string
        with pytest.raises((JSLRuntimeError, SymbolNotFoundError)):
            runner.execute(["undefined_variable"])  # Changed from string to list
        
        # Invalid function call
        with pytest.raises(JSLRuntimeError):
            runner.execute(["nonexistent_function", 1, 2])


if __name__ == "__main__":
    pytest.main([__file__])