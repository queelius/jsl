"""
Unified test suite that runs tests on BOTH evaluators.

This demonstrates that recursive and stack evaluators are functionally
equivalent - the same tests pass for both implementations.
"""

import pytest
from jsl.core import Evaluator, Env
from jsl.compiler import compile_to_postfix
from jsl.stack_evaluator import StackEvaluator


class EvaluatorWrapper:
    """Base wrapper class for evaluators."""
    pass


class RecursiveEvaluatorWrapper(EvaluatorWrapper):
    """Wrapper for recursive evaluator."""
    
    def __init__(self):
        from jsl.prelude import make_prelude
        self.evaluator = Evaluator()
        self.env = make_prelude()
    
    def eval(self, expr, env_dict=None):
        if env_dict:
            # Extend prelude with user environment
            eval_env = self.env.extend(env_dict)
        else:
            eval_env = self.env
        return self.evaluator.eval(expr, eval_env)
    
    def __repr__(self):
        return "RecursiveEvaluator"


class StackEvaluatorWrapper(EvaluatorWrapper):
    """Wrapper for stack evaluator."""
    
    def __init__(self):
        from jsl.prelude import make_prelude
        self.evaluator = StackEvaluator()
        # Add prelude functions to built-ins
        prelude = make_prelude()
        self.base_env = prelude.to_dict()
    
    def eval(self, expr, env_dict=None):
        # Compile S-expression to postfix
        postfix = compile_to_postfix(expr)
        
        # Combine prelude with user environment
        if env_dict:
            self.evaluator.env = {**self.base_env, **env_dict}
        else:
            self.evaluator.env = self.base_env.copy()
        
        return self.evaluator.eval(postfix)
    
    def __repr__(self):
        return "StackEvaluator"


# Parametrize tests to run with both evaluators
@pytest.fixture(params=[RecursiveEvaluatorWrapper, StackEvaluatorWrapper])
def evaluator(request):
    """Fixture that provides both evaluator types."""
    return request.param()


class TestBothEvaluators:
    """Tests that should pass for BOTH evaluators."""
    
    def test_literals(self, evaluator):
        """Test literal values."""
        assert evaluator.eval(5) == 5
        assert evaluator.eval(3.14) == 3.14
        assert evaluator.eval(True) == True
        assert evaluator.eval(None) == None
        assert evaluator.eval([]) == []
    
    def test_arithmetic(self, evaluator):
        """Test arithmetic operations."""
        assert evaluator.eval(['+', 2, 3]) == 5
        assert evaluator.eval(['*', 4, 5]) == 20
        assert evaluator.eval(['-', 10, 3]) == 7
        assert evaluator.eval(['/', 20, 5]) == 4
    
    def test_nested_arithmetic(self, evaluator):
        """Test nested arithmetic."""
        # (2 + 3) * 4 = 20
        assert evaluator.eval(['*', ['+', 2, 3], 4]) == 20
        
        # (5 - 2) + 3 = 6
        assert evaluator.eval(['+', ['-', 5, 2], 3]) == 6
        
        # ((10 + 20) * (100 - 50)) = 1500
        assert evaluator.eval(['*', ['+', 10, 20], ['-', 100, 50]]) == 1500
    
    def test_comparison(self, evaluator):
        """Test comparison operations."""
        assert evaluator.eval(['=', 5, 5]) == True
        assert evaluator.eval(['=', 5, 3]) == False
        assert evaluator.eval(['>', 5, 3]) == True
        assert evaluator.eval(['<', 3, 5]) == True
    
    def test_nary_operations(self, evaluator):
        """Test n-ary operations."""
        # Multiple arguments
        assert evaluator.eval(['+', 1, 2, 3, 4]) == 10
        
        # Zero arguments
        assert evaluator.eval(['+']) == 0  # Identity element
        assert evaluator.eval(['*']) == 1  # Identity element
        
        # One argument
        assert evaluator.eval(['+', 5]) == 5
    
    def test_string_literals(self, evaluator):
        """Test string literals with @ prefix."""
        assert evaluator.eval('@hello') == 'hello'
        assert evaluator.eval('@world') == 'world'
    
    def test_variables(self, evaluator):
        """Test variable lookup."""
        env = {'x': 10, 'y': 20}
        assert evaluator.eval('x', env) == 10
        assert evaluator.eval('y', env) == 20
        assert evaluator.eval(['+', 'x', 'y'], env) == 30
    
    def test_complex_expressions(self, evaluator):
        """Test complex nested expressions."""
        # ((2 + 3) * (7 - 3)) + ((10 / 2) - 1)
        expr = ['+',
                ['*', ['+', 2, 3], ['-', 7, 3]],
                ['-', ['/', 10, 2], 1]]
        
        # (5 * 4) + (5 - 1) = 20 + 4 = 24
        assert evaluator.eval(expr) == 24


class TestStackEvaluatorOnly:
    """Tests specific to stack evaluator (resumption, postfix, etc.)"""
    
    def test_resumption(self):
        """Test that stack evaluator can resume."""
        evaluator = StackEvaluator()
        instructions = [10, 20, 2, '+', 100, 50, 2, '-', 2, '*']
        
        # Execute partially
        result, state = evaluator.eval_partial(instructions, max_steps=3)
        assert result is None
        assert state is not None
        
        # Resume
        result, state = evaluator.eval_partial(instructions, max_steps=10, state=state)
        assert result == 1500
        assert state is None
    
    def test_direct_postfix(self):
        """Test evaluating postfix directly without compilation."""
        evaluator = StackEvaluator()
        
        # Direct postfix evaluation
        assert evaluator.eval([2, 3, 2, '+']) == 5
        assert evaluator.eval([2, 3, 2, '+', 4, 2, '*']) == 20
    
    def test_state_serialization(self):
        """Test saving and restoring evaluation state."""
        evaluator = StackEvaluator()
        instructions = [5, 10, 2, '+', 3, 2, '*']
        
        # Partial evaluation
        _, state1 = evaluator.eval_partial(instructions, max_steps=2)
        
        # Serialize
        state_dict = state1.to_dict()
        
        # Deserialize and resume
        from jsl.stack_evaluator import StackState
        state2 = StackState.from_dict(state_dict)
        
        result, _ = evaluator.eval_partial(instructions, max_steps=10, state=state2)
        assert result == 45  # (5 + 10) * 3


class TestRecursiveEvaluatorOnly:
    """Tests specific to recursive evaluator (closures, special forms, etc.)"""
    
    def test_lambda_creation(self):
        """Test lambda/closure creation (not yet in stack evaluator)."""
        evaluator = Evaluator()
        env = Env()
        
        # Create a lambda
        result = evaluator.eval(['lambda', ['x', 'y'], ['+', 'x', 'y']], env)
        
        from jsl.core import Closure
        assert isinstance(result, Closure)
        assert result.params == ['x', 'y']
    
    def test_let_binding(self):
        """Test let special form (not yet in stack evaluator)."""
        from jsl.prelude import make_prelude
        evaluator = Evaluator()
        env = make_prelude()
        
        # Let binding
        result = evaluator.eval(['let', [['x', 5]], ['*', 'x', 2]], env)
        assert result == 10
    
    def test_if_conditional(self):
        """Test if special form (not yet in stack evaluator)."""
        evaluator = Evaluator()
        env = Env()
        
        # If true branch
        result = evaluator.eval(['if', True, 10, 20], env)
        assert result == 10
        
        # If false branch
        result = evaluator.eval(['if', False, 10, 20], env)
        assert result == 20


# Run the unified tests
if __name__ == "__main__":
    import sys
    
    print("=== Running Unified Test Suite ===\n")
    print("This runs the same tests on BOTH evaluators to prove equivalence.\n")
    
    # Run with pytest
    pytest.main([__file__, '-v', '--tb=short'])