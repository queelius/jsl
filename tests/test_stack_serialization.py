"""
Test suite for stack evaluator serialization functionality.

Tests the serialization of Closure objects and environments in the stack evaluator.
"""

import unittest
import json
from jsl.runner import JSLRunner
from jsl import make_prelude
from jsl.core import Closure, Env


class TestStackClosureSerialization(unittest.TestCase):
    """Test serialization of stack evaluator closures."""
    
    def setUp(self):
        """Set up test environment with stack evaluator."""
        self.runner = JSLRunner(use_recursive_evaluator=False)
    
    def test_simple_closure_structure(self):
        """Test structure of Closure objects."""
        # Create a closure
        self.runner.execute('["def", "square", ["lambda", ["x"], ["*", "x", "x"]]]')
        closure = self.runner.stack_evaluator.env.get("square")
        
        # Check it's a Closure object
        self.assertIsInstance(closure, Closure)
        self.assertEqual(closure.params, ["x"])
        self.assertEqual(closure.body, ["*", "x", "x"])
        self.assertIsInstance(closure.env, Env)
    
    def test_closure_with_captured_env(self):
        """Test closure that captures variables."""
        program = '''
        ["do",
          ["def", "factor", 10],
          ["def", "multiplier", ["lambda", ["x"], ["*", "x", "factor"]]]
        ]
        '''
        self.runner.execute(program)
        closure = self.runner.stack_evaluator.env.get("multiplier")
        
        # Check captured environment
        self.assertIsInstance(closure, Closure)
        self.assertIsInstance(closure.env, Env)
        # The closure's env should have access to 'factor'
        self.assertEqual(closure.env.get("factor"), 10)
    
    def test_nested_closures(self):
        """Test nested closures (higher-order functions)."""
        program = '''
        ["do",
          ["def", "make_adder",
            ["lambda", ["n"],
              ["lambda", ["x"], ["+", "x", "n"]]
            ]
          ],
          ["def", "add5", ["make_adder", 5]]
        ]
        '''
        self.runner.execute(program)
        closure = self.runner.stack_evaluator.env.get("add5")
        
        # Should be the inner closure with n=5 captured
        self.assertIsInstance(closure, Closure)
        self.assertEqual(closure.params, ["x"])
        self.assertEqual(closure.body, ["+", "x", "n"])
        # Check that n is captured in the closure's environment
        self.assertEqual(closure.env.get("n"), 5)
    
    def test_closure_execution_after_reconstruction(self):
        """Test that closures work after manual reconstruction."""
        # Create a closure
        self.runner.execute('["def", "double", ["lambda", ["x"], ["*", "x", 2]]]')
        original = self.runner.stack_evaluator.env.get("double")
        
        # Create a new Closure object with minimal environment
        # We need to preserve the prelude functions for it to work
        minimal_env = make_prelude()
        reconstructed = Closure(
            params=original.params,
            body=original.body,
            env=minimal_env
        )
        
        # Create new runner and install the reconstructed closure
        new_runner = JSLRunner(use_recursive_evaluator=False)
        new_runner.stack_evaluator.env.define("double", reconstructed)
        
        # Test that it works
        result = new_runner.execute('["double", 21]')
        self.assertEqual(result, 42)
    
    def test_multiple_closures_structure(self):
        """Test structure of multiple closures."""
        program = '''
        ["do",
          ["def", "add", ["lambda", ["x", "y"], ["+", "x", "y"]]],
          ["def", "sub", ["lambda", ["x", "y"], ["-", "x", "y"]]],
          ["def", "mul", ["lambda", ["x", "y"], ["*", "x", "y"]]],
          ["list", "add", "sub", "mul"]
        ]
        '''
        closures = self.runner.execute(program)
        
        # All should be Closure objects
        for closure in closures:
            self.assertIsInstance(closure, Closure)
            self.assertEqual(len(closure.params), 2)
        
        # Check bodies
        self.assertEqual(closures[0].body, ["+", "x", "y"])
        self.assertEqual(closures[1].body, ["-", "x", "y"])
        self.assertEqual(closures[2].body, ["*", "x", "y"])


class TestStackDataSerialization(unittest.TestCase):
    """Test serialization of data structures with stack evaluator."""
    
    def setUp(self):
        """Set up test environment."""
        self.runner = JSLRunner(use_recursive_evaluator=False)
    
    def test_simple_data_serialization(self):
        """Test serializing simple data structures."""
        program = '''
        {
          "@numbers": ["@", [1, 2, 3]],
          "@strings": ["@", ["hello", "world"]],
          "@mixed": {"@a": 1, "@b": "@text"}
        }
        '''
        result = self.runner.execute(program)
        
        # This should be JSON serializable as-is
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        
        self.assertEqual(deserialized["numbers"], [1, 2, 3])
        self.assertEqual(deserialized["strings"], ["hello", "world"])
        self.assertEqual(deserialized["mixed"]["a"], 1)
        self.assertEqual(deserialized["mixed"]["b"], "text")
    
    def test_deeply_nested_structures(self):
        """Test serialization of deeply nested structures."""
        program = '''
        {
          "@level1": {
            "@level2": {
              "@level3": {
                "@data": ["@", [1, 2, 3]]
              }
            }
          }
        }
        '''
        result = self.runner.execute(program)
        
        # Should be directly JSON serializable
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        
        # Structure should be preserved
        self.assertEqual(
            deserialized["level1"]["level2"]["level3"]["data"],
            [1, 2, 3]
        )
    
    def test_closure_info_extraction(self):
        """Test extracting serializable info from closures."""
        program = '''
        ["do",
          ["def", "user_var", 42],
          ["def", "test_func", ["lambda", ["x"], ["+", "x", "user_var"]]]
        ]
        '''
        self.runner.execute(program)
        closure = self.runner.stack_evaluator.env.get("test_func")
        
        # Extract serializable parts from Closure object
        self.assertIsInstance(closure, Closure)
        closure_info = {
            "type": "closure",
            "params": closure.params,
            "body": closure.body,
            "captured_vars": {
                "user_var": closure.env.get("user_var")
            }
        }
        
        # This should be serializable
        serialized = json.dumps(closure_info)
        deserialized = json.loads(serialized)
        
        self.assertEqual(deserialized["params"], ["x"])
        self.assertEqual(deserialized["body"], ["+", "x", "user_var"])
        self.assertEqual(deserialized["captured_vars"]["user_var"], 42)


class TestJPNSerialization(unittest.TestCase):
    """Test JPN (compiled format) serialization."""
    
    def setUp(self):
        """Set up test environment."""
        self.runner = JSLRunner(use_recursive_evaluator=False)
    
    def test_simple_jpn_serialization(self):
        """Test that simple JPN can be serialized."""
        from jsl.compiler import compile_to_postfix
        
        # Simple expression without special forms
        expr = ["+", 1, 2, 3]
        jpn = compile_to_postfix(expr)
        
        # Should be JSON serializable
        serialized = json.dumps(jpn)
        deserialized = json.loads(serialized)
        
        # Should be executable
        from jsl.stack_evaluator import StackEvaluator
        evaluator = StackEvaluator()
        result = evaluator.eval(deserialized)
        self.assertEqual(result, 6)
    
    def test_jpn_with_objects(self):
        """Test JPN serialization with objects."""
        from jsl.compiler import compile_to_postfix
        
        # Expression with object
        expr = {"@key": "@value", "@number": 42}
        jpn = compile_to_postfix(expr)
        
        # Should be serializable
        serialized = json.dumps(jpn)
        deserialized = json.loads(serialized)
        
        # Should be executable
        from jsl.stack_evaluator import StackEvaluator
        evaluator = StackEvaluator()
        result = evaluator.eval(deserialized)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["number"], 42)
    
    def test_jpn_special_form_handling(self):
        """Test that JPN with special forms needs special handling."""
        from jsl.compiler import compile_to_postfix
        from jsl.stack_special_forms import Opcode
        
        # Expression with special form
        expr = ["if", True, 1, 2]
        jpn = compile_to_postfix(expr)
        
        # Contains Opcode enum which isn't directly serializable
        self.assertIn(Opcode.SPECIAL_FORM, jpn)
        
        # Need to convert Opcode to string for serialization
        jpn_serializable = []
        for item in jpn:
            if isinstance(item, Opcode):
                jpn_serializable.append(item.value)  # Use the string value
            else:
                jpn_serializable.append(item)
        
        # Now it should be serializable
        serialized = json.dumps(jpn_serializable)
        deserialized = json.loads(serialized)
        
        # To execute, would need to convert back to Opcode
        # This shows the serialization challenge with special forms


if __name__ == '__main__':
    unittest.main()