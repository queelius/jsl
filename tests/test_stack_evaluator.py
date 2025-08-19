"""
Tests for the stack-based evaluator and compiler.
"""

import json
import pytest
from jsl.compiler import compile_to_postfix, decompile_from_postfix
from jsl.stack_evaluator import StackEvaluator, StackState
from jsl.prelude import make_prelude
from jsl.core import Env, Closure


class TestCompiler:
    """Test S-expression to postfix compilation."""
    
    def test_literals(self):
        """Test compilation of literal values."""
        assert compile_to_postfix(5) == [5]
        assert compile_to_postfix(3.14) == [3.14]
        assert compile_to_postfix(True) == [True]
        assert compile_to_postfix(None) == [None]
        assert compile_to_postfix("x") == ["x"]
        assert compile_to_postfix([]) == [0, '__empty_list__']
    
    def test_binary_ops(self):
        """Test binary operations."""
        assert compile_to_postfix(['+', 2, 3]) == [2, 3, 2, '+']
        assert compile_to_postfix(['*', 4, 5]) == [4, 5, 2, '*']
        assert compile_to_postfix(['-', 10, 3]) == [10, 3, 2, '-']
        assert compile_to_postfix(['/', 15, 3]) == [15, 3, 2, '/']
    
    def test_nested_ops(self):
        """Test nested operations."""
        # (2 + 3) * 4
        assert compile_to_postfix(['*', ['+', 2, 3], 4]) == [2, 3, 2, '+', 4, 2, '*']
        
        # 2 * (3 + 4)
        assert compile_to_postfix(['*', 2, ['+', 3, 4]]) == [2, 3, 4, 2, '+', 2, '*']
        
        # (5 - 2) + 3
        assert compile_to_postfix(['+', ['-', 5, 2], 3]) == [5, 2, 2, '-', 3, 2, '+']
    
    def test_nary_ops(self):
        """Test n-ary operations."""
        # 0-arity
        assert compile_to_postfix(['+']) == [0, '+']
        assert compile_to_postfix(['list']) == [0, 'list']
        
        # 1-arity
        assert compile_to_postfix(['+', 5]) == [5, 1, '+']
        
        # n > 2
        assert compile_to_postfix(['+', 1, 2, 3, 4]) == [1, 2, 3, 4, 4, '+']
        assert compile_to_postfix(['list', '@a', '@b', '@c']) == ['@a', '@b', '@c', 3, 'list']
    
    def test_complex_nesting(self):
        """Test complex nested expressions."""
        # ((2 + 3) * (7 - 3))
        expr = ['*', ['+', 2, 3], ['-', 7, 3]]
        expected = [2, 3, 2, '+', 7, 3, 2, '-', 2, '*']
        assert compile_to_postfix(expr) == expected
    
    def test_roundtrip(self):
        """Test that decompile reverses compile for simple cases."""
        exprs = [
            ['+', 2, 3],
            ['*', 4, 5],
            ['not', True],
            ['=', 5, 5],
        ]
        
        for expr in exprs:
            postfix = compile_to_postfix(expr)
            back = decompile_from_postfix(postfix)
            assert back == expr


class TestStackEvaluator:
    """Test the stack-based evaluator."""
    
    def setup_method(self):
        """Set up test evaluator."""
        self.evaluator = StackEvaluator()
    
    def test_literals(self):
        """Test evaluation of literals."""
        assert self.evaluator.eval([5]) == 5
        assert self.evaluator.eval([3.14]) == 3.14
        assert self.evaluator.eval([True]) == True
        assert self.evaluator.eval([None]) == None
        assert self.evaluator.eval([0, '__empty_list__']) == []
    
    def test_arithmetic(self):
        """Test arithmetic operations."""
        # Addition
        assert self.evaluator.eval([2, 3, 2, '+']) == 5
        assert self.evaluator.eval([10, 20, 30, 3, '+']) == 60
        
        # Subtraction  
        assert self.evaluator.eval([10, 3, 2, '-']) == 7
        
        # Multiplication
        assert self.evaluator.eval([4, 5, 2, '*']) == 20
        
        # Division
        assert self.evaluator.eval([15, 3, 2, '/']) == 5
    
    def test_nested_arithmetic(self):
        """Test nested arithmetic expressions."""
        # (2 + 3) * 4 = 20
        assert self.evaluator.eval([2, 3, 2, '+', 4, 2, '*']) == 20
        
        # 2 * (3 + 4) = 14
        assert self.evaluator.eval([2, 3, 4, 2, '+', 2, '*']) == 14
        
        # ((10 + 20) * (100 - 50)) = 1500
        assert self.evaluator.eval([10, 20, 2, '+', 100, 50, 2, '-', 2, '*']) == 1500
    
    def test_comparison(self):
        """Test comparison operations."""
        assert self.evaluator.eval([5, 5, 2, '=']) == True
        assert self.evaluator.eval([5, 3, 2, '=']) == False
        assert self.evaluator.eval([5, 3, 2, '>']) == True
        assert self.evaluator.eval([3, 5, 2, '<']) == True
        assert self.evaluator.eval([5, 5, 2, '>=']) == True
        assert self.evaluator.eval([5, 5, 2, '<=']) == True
        assert self.evaluator.eval([5, 3, 2, '!=']) == True
    
    def test_logical(self):
        """Test logical operations."""
        assert self.evaluator.eval([True, 1, 'not']) == False
        assert self.evaluator.eval([False, 1, 'not']) == True
    
    def test_list_operations(self):
        """Test list operations."""
        # Create list
        assert self.evaluator.eval([1, 2, 3, 3, 'list']) == [1, 2, 3]
        
        # Empty list
        assert self.evaluator.eval([0, 'list']) == []
        
        # Cons
        assert self.evaluator.eval([1, 0, '__empty_list__', 2, 'cons']) == [1]
        assert self.evaluator.eval([1, [2, 3], 2, 'cons']) == [1, 2, 3]
        
        # First/rest
        assert self.evaluator.eval([[1, 2, 3], 1, 'first']) == 1
        assert self.evaluator.eval([[1, 2, 3], 1, 'rest']) == [2, 3]
        
        # Length
        assert self.evaluator.eval([[1, 2, 3, 4], 1, 'length']) == 4
        assert self.evaluator.eval([0, '__empty_list__', 1, 'length']) == 0
    
    def test_variables(self):
        """Test variable lookup."""
        self.evaluator.env = {'x': 10, 'y': 20}
        assert self.evaluator.eval(['x']) == 10
        assert self.evaluator.eval(['y']) == 20
        assert self.evaluator.eval(['x', 'y', 2, '+']) == 30
    
    def test_string_literals(self):
        """Test @ prefix for string literals."""
        assert self.evaluator.eval(['@hello']) == 'hello'
        assert self.evaluator.eval(['@world']) == 'world'
        assert self.evaluator.eval(['@']) == ''
    
    def test_undefined_variable(self):
        """Test that undefined variables raise errors."""
        with pytest.raises(ValueError, match="Undefined variable"):
            self.evaluator.eval(['undefined_var'])
    
    def test_stack_underflow(self):
        """Test that stack underflow is detected."""
        with pytest.raises(ValueError, match="Stack underflow"):
            self.evaluator.eval([2, '+'])  # Binary + with insufficient args
    
    def test_invalid_final_stack(self):
        """Test that invalid final stack is detected."""
        with pytest.raises(ValueError, match="Invalid expression"):
            self.evaluator.eval([1, 2])  # Two values left on stack


class TestResumption:
    """Test resumption capability of stack evaluator."""
    
    def setup_method(self):
        """Set up test evaluator."""
        self.evaluator = StackEvaluator()
    
    def test_simple_resumption(self):
        """Test basic resumption."""
        instructions = [10, 20, 2, '+', 100, 50, 2, '-', 2, '*']
        
        # Execute 2 steps
        result, state = self.evaluator.eval_partial(instructions, max_steps=2)
        assert result is None
        assert state is not None
        assert state.pc == 2
        assert state.stack == [10, 20]
        
        # Resume for 1 step (arity-operator pair counts as 1 step)
        result, state = self.evaluator.eval_partial(instructions, max_steps=1, state=state)
        assert result is None
        assert state.pc == 4
        assert state.stack == [30]
        
        # Resume for 2 more steps
        result, state = self.evaluator.eval_partial(instructions, max_steps=2, state=state)
        assert result is None
        assert state.pc == 6
        assert state.stack == [30, 100, 50]
        
        # Continue until done
        result, state = self.evaluator.eval_partial(instructions, max_steps=10, state=state)
        assert result == 1500
        assert state is None
    
    def test_state_serialization(self):
        """Test that state can be serialized/deserialized."""
        instructions = [5, 3, 2, '+', 2, 2, '*']
        
        # Partial evaluation
        result, state1 = self.evaluator.eval_partial(instructions, max_steps=3)
        assert result is None
        
        # Serialize state
        state_dict = state1.to_dict()
        assert 'stack' in state_dict
        assert 'pc' in state_dict
        assert 'instructions' in state_dict
        
        # Deserialize and resume
        state2 = StackState.from_dict(state_dict)
        result, final_state = self.evaluator.eval_partial(
            instructions, max_steps=10, state=state2
        )
        assert result == 16  # (5 + 3) * 2
        assert final_state is None
    
    def test_nary_resumption(self):
        """Test resumption with n-ary operators."""
        instructions = [1, 2, 3, 4, 5, 5, '+']
        
        # Execute partially
        result, state = self.evaluator.eval_partial(instructions, max_steps=3)
        assert result is None
        assert state.stack == [1, 2, 3]
        
        # Resume to completion
        result, state = self.evaluator.eval_partial(instructions, max_steps=10, state=state)
        assert result == 15
        assert state is None


class TestUserEnvironmentResumption:
    """Test resumption with user-defined functions and variables."""
    
    def setup_method(self):
        """Set up test components."""
        prelude = make_prelude()
        env = prelude.extend({})  # Extend to make modifiable
        self.evaluator = StackEvaluator(env=env)
    
    def test_resume_with_user_function(self):
        """Test resuming execution with a user-defined function."""
        # Define a user function using Env's define method with a proper Closure
        double_closure = Closure(
            params=['x'],
            body=['*', 'x', 2],
            env=self.evaluator.env  # Capture current environment
        )
        self.evaluator.env.define('double', double_closure)
        
        # Execute partially
        instructions = [10, 1, 'double']  # Should return 20
        result, state = self.evaluator.eval_partial(instructions, max_steps=1)
        
        assert result is None
        assert state is not None
        assert 'double' in state.env
        
        # Create fresh evaluator and resume
        fresh_prelude = make_prelude()
        fresh_env = fresh_prelude.extend({})  # Extend to make modifiable
        fresh_evaluator = StackEvaluator(env=fresh_env)
        
        # Resume execution
        final_result, final_state = fresh_evaluator.eval_partial(
            instructions, max_steps=100, state=state
        )
        
        assert final_result == 20
        assert final_state is None
    
    def test_resume_with_captured_variables(self):
        """Test resuming with closures that capture variables."""
        # Define variables and a closure that captures them
        self.evaluator.env.define('multiplier', 5)
        
        # Create closure that captures the environment with 'multiplier'
        add_multiply_closure = Closure(
            params=['a', 'b'],
            body=['*', ['+', 'a', 'b'], 'multiplier'],
            env=self.evaluator.env  # This captures 'multiplier'
        )
        self.evaluator.env.define('add-and-multiply', add_multiply_closure)
        
        # Execute partially - (3 + 4) * 5 = 35
        instructions = [3, 4, 2, 'add-and-multiply']
        result, state = self.evaluator.eval_partial(instructions, max_steps=2)
        
        assert result is None
        assert state is not None
        assert 'add-and-multiply' in state.env
        assert 'multiplier' in state.env
        
        # Create fresh evaluator and resume
        fresh_prelude = make_prelude()
        fresh_env = fresh_prelude.extend({})  # Extend to make modifiable
        fresh_evaluator = StackEvaluator(env=fresh_env)
        
        # Resume execution
        final_result, final_state = fresh_evaluator.eval_partial(
            instructions, max_steps=100, state=state
        )
        
        assert final_result == 35
        assert final_state is None
    
    def test_state_serialization_with_user_env(self):
        """Test that state with user environment can be JSON serialized."""
        # Define a user function and variable
        self.evaluator.env.define('scale', 10)
        
        # Create closure that captures 'scale'
        scale_closure = Closure(
            params=['n'],
            body=['*', 'n', 'scale'],
            env=self.evaluator.env  # Captures 'scale'
        )
        self.evaluator.env.define('scale-it', scale_closure)
        
        # Execute partially
        instructions = [7, 1, 'scale-it']  # Should return 70
        result, state = self.evaluator.eval_partial(instructions, max_steps=1)
        
        assert state is not None
        
        # Serialize state to JSON
        state_dict = state.to_dict()
        json_str = json.dumps(state_dict)
        
        # Deserialize state
        restored_dict = json.loads(json_str)
        fresh_prelude = make_prelude()
        fresh_env = fresh_prelude.extend({})  # Extend to make modifiable
        restored_state = StackState.from_dict(restored_dict, fresh_env)
        
        # Create fresh evaluator and resume with restored state
        fresh_evaluator = StackEvaluator(env=fresh_prelude)
        
        final_result, final_state = fresh_evaluator.eval_partial(
            instructions, max_steps=100, state=restored_state
        )
        
        assert final_result == 70
        assert final_state is None


class TestIntegration:
    """Test compiler and evaluator together."""
    
    def setup_method(self):
        """Set up test components."""
        self.evaluator = StackEvaluator()
    
    def eval_sexpr(self, expr):
        """Helper to compile and evaluate S-expression."""
        postfix = compile_to_postfix(expr)
        return self.evaluator.eval(postfix)
    
    def test_arithmetic_expressions(self):
        """Test various arithmetic S-expressions."""
        assert self.eval_sexpr(['+', 2, 3]) == 5
        assert self.eval_sexpr(['*', 4, 5]) == 20
        assert self.eval_sexpr(['-', 10, 3]) == 7
        assert self.eval_sexpr(['/', 20, 4]) == 5
    
    def test_nested_expressions(self):
        """Test nested S-expressions."""
        # (2 + 3) * (7 - 3)
        assert self.eval_sexpr(['*', ['+', 2, 3], ['-', 7, 3]]) == 20
        
        # ((10 + 20) * (100 - 50))
        assert self.eval_sexpr(['*', ['+', 10, 20], ['-', 100, 50]]) == 1500
    
    def test_nary_expressions(self):
        """Test n-ary S-expressions."""
        assert self.eval_sexpr(['+']) == 0  # Identity element
        assert self.eval_sexpr(['+', 1]) == 1
        assert self.eval_sexpr(['+', 1, 2, 3, 4, 5]) == 15
        assert self.eval_sexpr(['*']) == 1  # Identity element
        assert self.eval_sexpr(['list', '@a', '@b', '@c']) == ['a', 'b', 'c']
    
    def test_comparison_expressions(self):
        """Test comparison S-expressions."""
        assert self.eval_sexpr(['=', 5, 5]) == True
        assert self.eval_sexpr(['>', 10, 5]) == True
        assert self.eval_sexpr(['<', 3, 7]) == True
        assert self.eval_sexpr(['not', ['=', 1, 2]]) == True