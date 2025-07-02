"""
Test suite for JSL core functionality.
"""

import unittest
import json
from jsl import Evaluator, Env, Closure, make_prelude, run_program, eval_expression
from jsl.core import JSLError, SymbolNotFoundError, JSLTypeError


class TestJSLCore(unittest.TestCase):
    """Test core JSL functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.env = make_prelude()
        self.evaluator = Evaluator()
    
    def eval(self, expr_str):
        """Helper to evaluate JSL expression from string."""
        return eval_expression(expr_str, self.env)
    
    # Basic evaluation tests
    def test_literals(self):
        """Test literal value evaluation."""
        self.assertEqual(self.eval('42'), 42)
        self.assertEqual(self.eval('3.14'), 3.14)
        self.assertEqual(self.eval('true'), True)
        self.assertEqual(self.eval('false'), False)
        self.assertEqual(self.eval('null'), None)
        self.assertEqual(self.eval('"@hello"'), "hello")
    
    def test_arithmetic(self):
        """Test arithmetic operations."""
        self.assertEqual(self.eval('["+", 1, 2, 3]'), 6)
        self.assertEqual(self.eval('["-", 10, 2, 3]'), 5)
        self.assertEqual(self.eval('["*", 2, 3, 4]'), 24)
        self.assertEqual(self.eval('["/", 20, 4]'), 5.0)
        self.assertEqual(self.eval('["mod", 17, 5]'), 2)  # Changed from "%" to "mod"
    
    def test_comparison(self):
        """Test comparison operations."""
        self.assertTrue(self.eval('["=", 5, 5]'))
        self.assertFalse(self.eval('["=", 5, 3]'))
        self.assertTrue(self.eval('[">", 5, 3]'))
        self.assertFalse(self.eval('[">", 3, 5]'))
        self.assertTrue(self.eval('["<=", 3, 3]'))
        self.assertTrue(self.eval('[">=", 5, 5]'))
    
    def test_logical_operations(self):
        """Test logical operations."""
        self.assertTrue(self.eval('["and", true, true]'))
        self.assertFalse(self.eval('["and", true, false]'))
        self.assertTrue(self.eval('["or", false, true]'))
        self.assertFalse(self.eval('["or", false, false]'))
        self.assertFalse(self.eval('["not", true]'))
        self.assertTrue(self.eval('["not", false]'))
    
    # Special forms tests
    def test_def_and_lookup(self):
        """Test variable definition and lookup."""
        result = self.evaluator.eval(["def", "x", 100], self.env)
        self.assertEqual(result, 100)
        self.assertEqual(self.env.get("x"), 100)
        self.assertEqual(self.eval('"x"'), 100)
    
    def test_lambda_creation(self):
        """Test lambda function creation."""
        func = self.eval('["lambda", ["x"], ["*", "x", "x"]]')
        self.assertIsInstance(func, Closure)
        self.assertEqual(func.params, ["x"])
        self.assertEqual(func.body, ["*", "x", "x"])
    
    def test_function_call(self):
        """Test function call evaluation."""
        self.eval('["def", "square", ["lambda", ["x"], ["*", "x", "x"]]]')
        result = self.eval('["square", 5]')
        self.assertEqual(result, 25)
    
    def test_if_conditional(self):
        """Test conditional evaluation."""
        self.assertEqual(self.eval('["if", true, "@yes", "@no"]'), "yes")
        self.assertEqual(self.eval('["if", false, "@yes", "@no"]'), "no")
        self.assertEqual(self.eval('["if", [">", 5, 3], "@greater", "@less"]'), "greater")
    
    def test_let_bindings(self):
        """Test local variable bindings."""
        result = self.eval('["let", [["x", 10], ["y", 20]], ["+", "x", "y"]]')
        self.assertEqual(result, 30)
        
        # Variables should not be available outside let
        with self.assertRaises(SymbolNotFoundError):
            self.env.get("x")
    
    def test_let_scoping(self):
        """Test let scoping behavior."""
        self.eval('["def", "outer_x", 100]')
        # Let shadows outer_x
        result = self.eval('["let", [["outer_x", 1]], ["+", "outer_x", 1]]')
        self.assertEqual(result, 2)
        # Outer_x remains unchanged
        self.assertEqual(self.eval('"outer_x"'), 100)
    
    def test_do_sequential(self):
        """Test sequential evaluation with do."""
        result = self.eval('["do", ["def", "a", 1], ["def", "b", 2], ["+", "a", "b"]]')
        self.assertEqual(result, 3)
        self.assertEqual(self.env.get("a"), 1)
        self.assertEqual(self.env.get("b"), 2)
    
    def test_quote(self):
        """Test quotation/literal forms."""
        self.assertEqual(self.eval('["@", "hello"]'), "hello")
        self.assertEqual(self.eval('["@", ["+", 1, 2]]'), ["+", 1, 2])
        self.assertEqual(self.eval('["quote", {"key": "value"}]'), {"key": "value"})
    
    # Higher-order function tests
    def test_map_function(self):
        """Test map higher-order function."""
        # Define a square function first
        self.eval('["def", "square", ["lambda", ["x"], ["*", "x", "x"]]]')
        result = self.eval('["map", "square", ["@", [1, 2, 3, 4]]]')
        self.assertEqual(result, [1, 4, 9, 16])
    
    def test_filter_function(self):
        """Test filter higher-order function."""
        # Define a predicate function - use "mod" instead of "%"
        self.eval('["def", "is_even", ["lambda", ["x"], ["=", ["mod", "x", 2], 0]]]')
        result = self.eval('["filter", "is_even", ["@", [1, 2, 3, 4, 5, 6]]]')
        self.assertEqual(result, [2, 4, 6])
    
    def test_reduce_function(self):
        """Test reduce higher-order function."""
        result = self.eval('["reduce", "+", ["@", [1, 2, 3, 4]], 0]')
        self.assertEqual(result, 10)
    
    # String operations tests
    def test_string_operations(self):
        """Test string manipulation functions."""
        self.assertEqual(self.eval('["str-concat", "@hello", "@world"]'), "helloworld")
        self.assertEqual(self.eval('["str-length", "@hello"]'), 5)
        self.assertEqual(self.eval('["str-upper", "@hello"]'), "HELLO")
        self.assertEqual(self.eval('["str-lower", "@HELLO"]'), "hello")
    
    # List operations tests
    def test_list_operations(self):
        """Test list manipulation functions."""
        self.assertEqual(self.eval('["list", 1, 2, 3]'), [1, 2, 3])
        self.assertEqual(self.eval('["length", ["@", [1, 2, 3]]]'), 3)
        self.assertEqual(self.eval('["first", ["@", [1, 2, 3]]]'), 1)
        self.assertEqual(self.eval('["rest", ["@", [1, 2, 3]]]'), [2, 3])
        self.assertEqual(self.eval('["last", ["@", [1, 2, 3]]]'), 3)
        self.assertEqual(self.eval('["cons", 0, ["@", [1, 2, 3]]]'), [0, 1, 2, 3])
        self.assertEqual(self.eval('["append", ["@", [1, 2]], 3]'), [1, 2, 3])
    
    # Object operations tests  
    def test_object_operations(self):
        """Test object manipulation functions."""
        # Create object using simplified syntax - both keys and values evaluated
        self.eval('["def", "test_obj", {"@name": "@Alice", "@age": 30}]')
        self.assertEqual(self.eval('["get", "test_obj", "@name"]'), "Alice")
        self.assertEqual(self.eval('["has", "test_obj", "@name"]'), True)
        self.assertEqual(self.eval('["has", "test_obj", "@email"]'), False)
        self.assertEqual(self.eval('["keys", "test_obj"]'), ["name", "age"])
    
    # Error handling tests
    def test_error_handling(self):
        """Test error cases."""
        # Test direct core evaluation - should raise SymbolNotFoundError
        with self.assertRaises(SymbolNotFoundError):
            self.evaluator.eval("undefined_variable", self.env)
        
        # Test through eval_expression wrapper - raises JSLRuntimeError
        from jsl.runner import JSLRuntimeError
        with self.assertRaises(JSLRuntimeError):
            self.eval('"undefined_variable"')
        
        with self.assertRaises(JSLRuntimeError):
            self.eval('["def"]')  # Missing arguments
        
        with self.assertRaises(JSLRuntimeError):
            self.eval('["def", "symbol-name"]')  # Missing definition argument

        with self.assertRaises(JSLRuntimeError):
            self.eval('["lambda"]')  # Missing arguments
    
    # Integration tests
    def test_factorial_recursive(self):
        """Test recursive factorial function."""
        program = '''
        ["do",
          ["def", "factorial",
            ["lambda", ["n"],
              ["if", ["<=", "n", 1],
                1,
                ["*", "n", ["factorial", ["-", "n", 1]]]
              ]
            ]
          ],
          ["factorial", 5]
        ]
        '''
        result = self.eval(program)
        self.assertEqual(result, 120)
    
    def test_fibonacci_recursive(self):
        """Test recursive Fibonacci function."""
        program = '''
        ["do",
          ["def", "fib",
            ["lambda", ["n"],
              ["if", ["<=", "n", 1],
                "n",
                ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]
              ]
            ]
          ],
          ["fib", 7]
        ]
        '''
        result = self.eval(program)
        self.assertEqual(result, 13)
    
    def test_closure_capture(self):
        """Test closure environment capture."""
        program = '''
        ["do",
          ["def", "make_adder",
            ["lambda", ["n"],
              ["lambda", ["x"], ["+", "x", "n"]]
            ]
          ],
          ["def", "add5", ["make_adder", 5]],
          ["add5", 10]
        ]
        '''
        result = self.eval(program)
        self.assertEqual(result, 15)


class TestJSLObjectConstruction(unittest.TestCase):
    """Test JSL simplified object construction."""
    
    def setUp(self):
        """Set up test environment."""
        self.env = make_prelude()
        self.evaluator = Evaluator()
    
    def eval(self, expr_str):
        """Helper to evaluate JSL expression from string."""
        return eval_expression(expr_str, self.env)
    
    def test_literal_object(self):
        """Test object with literal keys and values."""
        result = self.eval('{"@name": "@Alice", "@age": 25}')
        expected = {"name": "Alice", "age": 25}
        self.assertEqual(result, expected)
    
    def test_dynamic_object(self):
        """Test object construction with string concatenation."""
        program = '''
        ["do",
          ["def", "name", "@Alice"],
          ["def", "age", 25],
          {"@greeting": ["str-concat", "@Hello ", "name"], 
           "@info": ["str-concat", "@Age: ", "age"]}
        ]
        '''
        result = self.eval(program)
        expected = {"greeting": "Hello Alice", "info": "Age: 25"}
        self.assertEqual(result, expected)
    
    def test_variable_keys(self):
        """Test objects with dynamic keys."""
        program = '''
        ["do",
          ["def", "key_name", "@username"],
          ["def", "value", "@Alice"],
          {"key_name": "value"}
        ]
        '''
        result = self.eval(program)
        expected = {"username": "Alice"}
        self.assertEqual(result, expected)
    
    def test_key_must_be_string(self):
        """Test that object keys must evaluate to strings."""
        # Test that numeric literal as key fails - use direct evaluator to get proper exception
        with self.assertRaises(JSLTypeError):
            self.evaluator.eval({42: "@value"}, self.env)
        
        # Test through eval_expression wrapper - raises JSLRuntimeError
        from jsl.runner import JSLRuntimeError
        program = '''
        ["do",
          ["def", "numeric_key", 42],
          {"numeric_key": "@value"}
        ]
        '''
        with self.assertRaises(JSLRuntimeError):
            self.eval(program)
        
        # This should work - literal number in quotes becomes string
        result = self.eval('{"@42": "@value"}')
        self.assertEqual(result, {"42": "value"})


class TestJSLRunner(unittest.TestCase):
    """Test high-level runner functions."""
    
    def test_run_program_string(self):
        """Test running program from JSON string."""
        program = '["+", 1, 2, 3]'
        result = run_program(program)
        self.assertEqual(result, 6)
    
    def test_run_program_structure(self):
        """Test running program from parsed structure."""
        program = ["+", 1, 2, 3]
        result = run_program(program)
        self.assertEqual(result, 6)
    
    def test_eval_expression_string(self):
        """Test evaluating expression from string."""
        result = eval_expression('["*", 6, 7]')
        self.assertEqual(result, 42)


if __name__ == '__main__':
    unittest.main()
