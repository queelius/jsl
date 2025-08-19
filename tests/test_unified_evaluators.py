"""
Unified test suite that runs all tests against BOTH evaluators.

This ensures the recursive and stack evaluators are functionally equivalent.
All tests are parameterized to run with both implementations.
"""

import pytest
import json
from typing import Any, Dict, Optional

from jsl.core import Evaluator, Env
from jsl.prelude import make_prelude
from jsl.compiler import compile_to_postfix
from jsl.stack_evaluator import StackEvaluator
from jsl.runner import JSLRunner


class EvaluatorAdapter:
    """Adapter interface for different evaluator implementations."""
    
    def eval(self, expr: Any) -> Any:
        """Evaluate an expression."""
        raise NotImplementedError
    
    def define(self, name: str, value: Any) -> None:
        """Define a variable."""
        raise NotImplementedError


class RecursiveEvaluatorAdapter(EvaluatorAdapter):
    """Adapter for recursive evaluator."""
    
    def __init__(self):
        self.evaluator = Evaluator()
        prelude = make_prelude()
        self.env = prelude.extend({})  # Extend to make modifiable
    
    def eval(self, expr: Any) -> Any:
        """Evaluate using recursive evaluator."""
        if isinstance(expr, str):
            expr = json.loads(expr)
        return self.evaluator.eval(expr, self.env)
    
    def define(self, name: str, value: Any) -> None:
        """Define a variable in environment."""
        self.env.define(name, value)
    
    def __repr__(self):
        return "RecursiveEvaluator"


class StackEvaluatorAdapter(EvaluatorAdapter):
    """Adapter for stack evaluator."""
    
    def __init__(self):
        prelude = make_prelude()
        self.env = prelude.extend({})  # Extend to make modifiable
        self.evaluator = StackEvaluator(env=self.env)
    
    def eval(self, expr: Any) -> Any:
        """Evaluate using stack evaluator."""
        if isinstance(expr, str):
            expr = json.loads(expr)
        jpn = compile_to_postfix(expr)
        return self.evaluator.eval(jpn)
    
    def define(self, name: str, value: Any) -> None:
        """Define a variable in environment."""
        self.env.define(name, value)
        self.evaluator.env.define(name, value)
    
    def __repr__(self):
        return "StackEvaluator"


class RunnerAdapter(EvaluatorAdapter):
    """Adapter for JSLRunner with both evaluator modes."""
    
    def __init__(self, use_recursive: bool = False):
        self.runner = JSLRunner(use_recursive_evaluator=use_recursive)
        self.use_recursive = use_recursive
    
    def eval(self, expr: Any) -> Any:
        """Evaluate using runner."""
        return self.runner.execute(expr)
    
    def define(self, name: str, value: Any) -> None:
        """Define a variable using def."""
        self.runner.execute(["def", name, value])
    
    def __repr__(self):
        return f"JSLRunner({'recursive' if self.use_recursive else 'stack'})"


# Parametrize all test methods to run with different evaluators
@pytest.fixture(params=[
    RecursiveEvaluatorAdapter(),
    StackEvaluatorAdapter(),
    RunnerAdapter(use_recursive=True),
    RunnerAdapter(use_recursive=False),
], ids=lambda x: str(x))
def evaluator(request):
    """Provide different evaluator implementations."""
    return request.param


class TestLiterals:
    """Test literal value evaluation."""
    
    def test_numbers(self, evaluator):
        """Test number literals."""
        assert evaluator.eval('42') == 42
        assert evaluator.eval('3.14') == 3.14
        assert evaluator.eval('-5') == -5
        assert evaluator.eval('0') == 0
    
    def test_booleans(self, evaluator):
        """Test boolean literals."""
        assert evaluator.eval('true') == True
        assert evaluator.eval('false') == False
    
    def test_null(self, evaluator):
        """Test null literal."""
        assert evaluator.eval('null') == None
    
    def test_strings(self, evaluator):
        """Test string literals."""
        assert evaluator.eval('"@hello"') == "hello"
        assert evaluator.eval('"@world"') == "world"
        assert evaluator.eval('"@"') == ""


class TestArithmetic:
    """Test arithmetic operations."""
    
    def test_addition(self, evaluator):
        """Test addition."""
        assert evaluator.eval('["+", 1, 2]') == 3
        assert evaluator.eval('["+", 1, 2, 3, 4]') == 10
        assert evaluator.eval('["+"]') == 0  # Identity
    
    def test_subtraction(self, evaluator):
        """Test subtraction."""
        assert evaluator.eval('["-", 10, 3]') == 7
        assert evaluator.eval('["-", 10, 3, 2]') == 5
        assert evaluator.eval('["-", 5]') == -5  # Negation
    
    def test_multiplication(self, evaluator):
        """Test multiplication."""
        assert evaluator.eval('["*", 2, 3]') == 6
        assert evaluator.eval('["*", 2, 3, 4]') == 24
        assert evaluator.eval('["*"]') == 1  # Identity
    
    def test_division(self, evaluator):
        """Test division."""
        assert evaluator.eval('["/", 10, 2]') == 5.0
        assert evaluator.eval('["/", 20, 4]') == 5.0
    
    def test_modulo(self, evaluator):
        """Test modulo."""
        assert evaluator.eval('["%", 10, 3]') == 1
        assert evaluator.eval('["%", 17, 5]') == 2
    
    def test_nested_arithmetic(self, evaluator):
        """Test nested arithmetic expressions."""
        assert evaluator.eval('["*", ["+", 2, 3], 4]') == 20
        assert evaluator.eval('["+", ["*", 2, 3], ["*", 4, 5]]') == 26


class TestComparison:
    """Test comparison operations."""
    
    def test_equality(self, evaluator):
        """Test equality."""
        assert evaluator.eval('["=", 5, 5]') == True
        assert evaluator.eval('["=", 5, 3]') == False
        assert evaluator.eval('["=", "@hello", "@hello"]') == True
    
    def test_inequality(self, evaluator):
        """Test inequality."""
        assert evaluator.eval('["!=", 5, 3]') == True
        assert evaluator.eval('["!=", 5, 5]') == False
    
    def test_less_than(self, evaluator):
        """Test less than."""
        assert evaluator.eval('["<", 3, 5]') == True
        assert evaluator.eval('["<", 5, 3]') == False
        assert evaluator.eval('["<", 3, 3]') == False
    
    def test_greater_than(self, evaluator):
        """Test greater than."""
        assert evaluator.eval('[">", 5, 3]') == True
        assert evaluator.eval('[">", 3, 5]') == False
        assert evaluator.eval('[">", 3, 3]') == False
    
    def test_less_equal(self, evaluator):
        """Test less than or equal."""
        assert evaluator.eval('["<=", 3, 5]') == True
        assert evaluator.eval('["<=", 3, 3]') == True
        assert evaluator.eval('["<=", 5, 3]') == False
    
    def test_greater_equal(self, evaluator):
        """Test greater than or equal."""
        assert evaluator.eval('[">=", 5, 3]') == True
        assert evaluator.eval('[">=", 3, 3]') == True
        assert evaluator.eval('[">=", 3, 5]') == False


class TestLogical:
    """Test logical operations."""
    
    def test_and(self, evaluator):
        """Test logical AND."""
        assert evaluator.eval('["and", true, true]') == True
        assert evaluator.eval('["and", true, false]') == False
        assert evaluator.eval('["and", false, true]') == False
        assert evaluator.eval('["and", false, false]') == False
        assert evaluator.eval('["and"]') == True  # Identity
    
    def test_or(self, evaluator):
        """Test logical OR."""
        assert evaluator.eval('["or", true, true]') == True
        assert evaluator.eval('["or", true, false]') == True
        assert evaluator.eval('["or", false, true]') == True
        assert evaluator.eval('["or", false, false]') == False
        assert evaluator.eval('["or"]') == False  # Identity
    
    def test_not(self, evaluator):
        """Test logical NOT."""
        assert evaluator.eval('["not", true]') == False
        assert evaluator.eval('["not", false]') == True


class TestLists:
    """Test list operations."""
    
    def test_list_creation(self, evaluator):
        """Test list creation."""
        assert evaluator.eval('["list", 1, 2, 3]') == [1, 2, 3]
        assert evaluator.eval('["list"]') == []  # Empty list
        assert evaluator.eval('[]') == []  # Empty list literal
    
    def test_cons(self, evaluator):
        """Test cons operation."""
        assert evaluator.eval('["cons", 1, ["list", 2, 3]]') == [1, 2, 3]
        assert evaluator.eval('["cons", 1, []]') == [1]
    
    def test_first(self, evaluator):
        """Test first element."""
        assert evaluator.eval('["first", ["list", 1, 2, 3]]') == 1
        assert evaluator.eval('["first", ["list", "@hello"]]') == "hello"
    
    def test_rest(self, evaluator):
        """Test rest of list."""
        assert evaluator.eval('["rest", ["list", 1, 2, 3]]') == [2, 3]
        assert evaluator.eval('["rest", ["list", 1]]') == []
    
    def test_length(self, evaluator):
        """Test list length."""
        assert evaluator.eval('["length", ["list", 1, 2, 3]]') == 3
        assert evaluator.eval('["length", []]') == 0
    
    def test_append(self, evaluator):
        """Test append operation."""
        assert evaluator.eval('["append", ["list", 1, 2], 3]') == [1, 2, 3]


class TestSpecialForms:
    """Test special forms (if, let, lambda, etc.)."""
    
    def test_if(self, evaluator):
        """Test conditional evaluation."""
        assert evaluator.eval('["if", true, 1, 2]') == 1
        assert evaluator.eval('["if", false, 1, 2]') == 2
        assert evaluator.eval('["if", ["=", 2, 2], "@yes", "@no"]') == "yes"
        assert evaluator.eval('["if", [">", 3, 5], "@yes", "@no"]') == "no"
    
    def test_let(self, evaluator):
        """Test let binding."""
        # Single binding (still needs double brackets)
        assert evaluator.eval('["let", [["x", 5]], "x"]') == 5
        assert evaluator.eval('["let", [["x", 10]], ["*", "x", 2]]') == 20
        
        # Multiple bindings
        assert evaluator.eval('["let", [["x", 3], ["y", 4]], ["+", "x", "y"]]') == 7
        
        # Nested let
        assert evaluator.eval('["let", [["x", 3]], ["let", [["y", 4]], ["+", "x", "y"]]]') == 7
        
        # Empty bindings
        assert evaluator.eval('["let", [], 42]') == 42
    
    def test_lambda(self, evaluator):
        """Test lambda creation and application."""
        # Create and immediately apply a lambda
        assert evaluator.eval('[["lambda", ["x"], ["*", "x", 2]], 5]') == 10
        assert evaluator.eval('[["lambda", ["x", "y"], ["+", "x", "y"]], 3, 4]') == 7
    
    def test_def(self, evaluator):
        """Test define."""
        result = evaluator.eval('["def", "x", 42]')
        assert result == 42
        assert evaluator.eval('"x"') == 42
        
        # Define a function
        evaluator.eval('["def", "double", ["lambda", ["x"], ["*", "x", 2]]]')
        assert evaluator.eval('["double", 5]') == 10
    
    def test_do(self, evaluator):
        """Test sequential evaluation."""
        assert evaluator.eval('["do", 1, 2, 3]') == 3
        assert evaluator.eval('["do", ["def", "x", 5], ["*", "x", 2]]') == 10
    
    def test_quote(self, evaluator):
        """Test quote."""
        assert evaluator.eval('["quote", ["*", 2, 3]]') == ["*", 2, 3]
        assert evaluator.eval('["quote", "x"]') == "x"
    
    def test_try(self, evaluator):
        """Test try/catch error handling."""
        # Successful try
        assert evaluator.eval('["try", ["+", 1, 2], ["lambda", ["err"], "@error"]]') == 3
        
        # Try with error (division by zero)
        result = evaluator.eval('["try", ["/", 1, 0], ["lambda", ["err"], "@caught"]]')
        assert result == "caught"
        
        # Try with undefined variable error
        result = evaluator.eval('["try", "undefined_var", ["lambda", ["e"], "@handled"]]')
        assert result == "handled"


class TestVariables:
    """Test variable definition and lookup."""
    
    def test_variable_lookup(self, evaluator):
        """Test looking up defined variables."""
        evaluator.define("test_var", 100)
        assert evaluator.eval('"test_var"') == 100
    
    def test_variable_in_expression(self, evaluator):
        """Test using variables in expressions."""
        evaluator.define("a", 10)
        evaluator.define("b", 20)
        assert evaluator.eval('["+", "a", "b"]') == 30
        assert evaluator.eval('["*", "a", 2]') == 20


class TestComplexExpressions:
    """Test complex nested expressions."""
    
    def test_fibonacci(self, evaluator):
        """Test recursive fibonacci."""
        # Define fibonacci function
        evaluator.eval('''
        ["def", "fib", 
            ["lambda", ["n"],
                ["if", ["<=", "n", 1],
                    "n",
                    ["+", 
                        ["fib", ["-", "n", 1]],
                        ["fib", ["-", "n", 2]]
                    ]
                ]
            ]
        ]
        ''')
        
        assert evaluator.eval('["fib", 0]') == 0
        assert evaluator.eval('["fib", 1]') == 1
        assert evaluator.eval('["fib", 5]') == 5
        assert evaluator.eval('["fib", 6]') == 8
    
    def test_factorial(self, evaluator):
        """Test recursive factorial."""
        evaluator.eval('''
        ["def", "fact",
            ["lambda", ["n"],
                ["if", ["<=", "n", 1],
                    1,
                    ["*", "n", ["fact", ["-", "n", 1]]]
                ]
            ]
        ]
        ''')
        
        assert evaluator.eval('["fact", 0]') == 1
        assert evaluator.eval('["fact", 1]') == 1
        assert evaluator.eval('["fact", 5]') == 120
    
    def test_higher_order_functions(self, evaluator):
        """Test functions that take/return functions."""
        # Define a function that returns a function
        evaluator.eval('''
        ["def", "make_adder",
            ["lambda", ["x"],
                ["lambda", ["y"], ["+", "x", "y"]]
            ]
        ]
        ''')
        
        evaluator.eval('["def", "add5", ["make_adder", 5]]')
        assert evaluator.eval('["add5", 3]') == 8
        assert evaluator.eval('["add5", 10]') == 15


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_expressions(self, evaluator):
        """Test empty expressions."""
        assert evaluator.eval('[]') == []
        assert evaluator.eval('["list"]') == []
    
    def test_deeply_nested(self, evaluator):
        """Test deeply nested expressions."""
        expr = '["+", 1, ["+", 2, ["+", 3, ["+", 4, 5]]]]'
        assert evaluator.eval(expr) == 15
    
    def test_mixed_types(self, evaluator):
        """Test operations with mixed types."""
        # Arithmetic with floats and ints
        assert evaluator.eval('["+", 1.5, 2]') == 3.5
        assert evaluator.eval('["*", 2.5, 4]') == 10.0


class TestMinMax:
    """Test min/max operations with identity elements."""
    
    def test_max(self, evaluator):
        """Test max operation."""
        assert evaluator.eval('["max", 1, 5, 3, 2]') == 5
        assert evaluator.eval('["max", -10, -5, -20]') == -5
        assert evaluator.eval('["max"]') == float('-inf')  # Identity
    
    def test_min(self, evaluator):
        """Test min operation."""
        assert evaluator.eval('["min", 1, 5, 3, 2]') == 1
        assert evaluator.eval('["min", -10, -5, -20]') == -20
        assert evaluator.eval('["min"]') == float('inf')  # Identity


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])