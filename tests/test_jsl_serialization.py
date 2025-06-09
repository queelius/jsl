import unittest
import json
import tempfile
import os
from typing import Any

from jsl import jsl
from jsl.jsl import (
    Env,
    Closure,
    make_prelude,
    to_json,
    from_json,
    eval_expr
)

class TestSerializationCompatibility(unittest.TestCase):
    """
    Comprehensive tests for serialization/deserialization compatibility.
    
    These tests verify that values can be serialized with to_json and
    accurately reconstructed with from_json, maintaining semantic equivalence.
    """

    def setUp(self):
        """Set up fresh prelude and environment for each test."""
        jsl.prelude = None
        self.prelude = make_prelude()
        jsl.prelude = self.prelude  # Set global prelude for from_json
        self.env = Env(parent=self.prelude)

    def test_primitive_values_roundtrip(self):
        """Test that primitive values serialize and deserialize correctly."""
        test_values = [
            None,
            True,
            False,
            42,
            3.14159,
            "hello world",
            "",
            0,
            -1,
            0.0,
            float('inf'),
            float('-inf')
        ]
        
        for original in test_values:
            with self.subTest(value=original):
                serialized = to_json(original)
                deserialized = from_json(serialized, self.prelude)
                self.assertEqual(original, deserialized)

    def test_list_values_roundtrip(self):
        """Test that lists serialize and deserialize correctly."""
        test_lists = [
            [],
            [1, 2, 3],
            ["a", "b", "c"],
            [1, "hello", True, None],
            [[1, 2], [3, 4]],  # nested lists
            [{"key": "value"}, [1, 2]],  # mixed content
        ]
        
        for original in test_lists:
            with self.subTest(list_value=original):
                serialized = to_json(original)
                deserialized = from_json(serialized, self.prelude)
                self.assertEqual(original, deserialized)

    def test_dict_values_roundtrip(self):
        """Test that dictionaries serialize and deserialize correctly."""
        test_dicts = [
            {},
            {"key": "value"},
            {"a": 1, "b": 2, "c": 3},
            {"nested": {"inner": "value"}},
            {"mixed": [1, 2, {"inner": True}]},
            {"numbers": 42, "strings": "hello", "bools": False, "nulls": None}
        ]
        
        for original in test_dicts:
            with self.subTest(dict_value=original):
                serialized = to_json(original)
                deserialized = from_json(serialized, self.prelude)
                self.assertEqual(original, deserialized)

    def test_simple_closure_roundtrip(self):
        """Test serialization of a simple closure without captured variables."""
        # Create a simple closure
        closure_expr = ["lambda", ["x"], ["+", "x", 1]]
        original_closure = eval_expr(closure_expr, self.env)
        
        # Serialize and deserialize
        serialized = to_json(original_closure)
        deserialized = from_json(serialized, self.prelude)
        
        # Verify structure
        self.assertIsInstance(deserialized, Closure)
        self.assertEqual(deserialized.params, ["x"])
        self.assertEqual(deserialized.body, ["+", "x", 1])
        
        # Test functional equivalence
        test_env = Env(parent=self.prelude)
        test_env["orig_fn"] = original_closure
        test_env["deser_fn"] = deserialized
        
        orig_result = eval_expr(["orig_fn", 5], test_env)
        deser_result = eval_expr(["deser_fn", 5], test_env)
        
        self.assertEqual(orig_result, deser_result)
        self.assertEqual(deser_result, 6)

    def test_closure_with_captured_variables_roundtrip(self):
        """Test serialization of closures that capture variables from their environment."""
        # Set up environment with captured values
        self.env["multiplier"] = 10
        self.env["offset"] = 5
        
        # Create closure that captures these variables
        closure_expr = ["lambda", ["x"], ["+", ["*", "x", "multiplier"], "offset"]]
        original_closure = eval_expr(closure_expr, self.env)
        
        # Serialize and deserialize
        serialized = to_json(original_closure)
        deserialized = from_json(serialized, self.prelude)
        
        # Verify structure
        self.assertIsInstance(deserialized, Closure)
        self.assertEqual(deserialized.params, ["x"])
        
        # Test functional equivalence
        test_env = Env(parent=self.prelude)
        test_env["deser_fn"] = deserialized
        
        result = eval_expr(["deser_fn", 3], test_env)
        self.assertEqual(result, 35)  # (3 * 10) + 5

    def test_nested_closure_roundtrip(self):
        """Test serialization of closures that return other closures."""
        # Create a closure factory
        self.env["base"] = 100
        factory_expr = ["lambda", ["multiplier"], 
                       ["lambda", ["x"], ["+", ["*", "x", "multiplier"], "base"]]]
        original_factory = eval_expr(factory_expr, self.env)
        
        # Serialize and deserialize the factory
        serialized = to_json(original_factory)
        deserialized = from_json(serialized, self.prelude)
        
        # Test that the factory works
        test_env = Env(parent=self.prelude)
        test_env["factory"] = deserialized
        
        # Create a specific function using the factory
        specific_fn = eval_expr(["factory", 5], test_env)
        self.assertIsInstance(specific_fn, Closure)
        
        # Test the specific function
        test_env["specific"] = specific_fn
        result = eval_expr(["specific", 4], test_env)
        self.assertEqual(result, 120)  # (4 * 5) + 100

    def test_closure_with_self_reference_roundtrip(self):
        """Test serialization of recursive closures."""
        # Define a recursive factorial function
        factorial_def = ["def", "factorial", 
                        ["lambda", ["n"], 
                         ["if", ["=", "n", 0], 
                          1, 
                          ["*", "n", ["factorial", ["-", "n", 1]]]]]]
        eval_expr(factorial_def, self.env)

        original_factorial = self.env["factorial"]
        
        # Serialize and deserialize
        serialized = to_json(original_factorial)
        print("\nSerialized closure:")
        print(json.dumps(serialized, indent=2))

        deserialized = from_json(serialized, self.prelude)
        print("\nDeserialized closure:")
        print(deserialized)
        
        # Test functional equivalence
        test_env = Env(parent=self.prelude)
        test_env["fact"] = deserialized
        
        result = eval_expr(["fact", 5], test_env)
        self.assertEqual(result, 120)  # 5!

    def test_environment_serialization_only_captures_used_variables(self):
        """Test that only referenced variables are included in serialized environments."""
        # Set up environment with many variables
        self.env["used_var"] = 42
        self.env["unused_var1"] = "not_used"
        self.env["unused_var2"] = [1, 2, 3]
        self.env["another_used"] = "hello"
        
        # Create closure that only uses some variables
        closure_expr = ["lambda", ["x"], ["+", "used_var", ["length", "another_used"]]]
        closure = eval_expr(closure_expr, self.env)
        
        # Serialize
        serialized = to_json(closure)
        
        # Verify only used variables are in the serialized environment
        env_data = serialized["env"]
        self.assertIn("used_var", json.dumps(env_data))
        self.assertIn("another_used", json.dumps(env_data))
        self.assertNotIn("unused_var1", json.dumps(env_data))
        self.assertNotIn("unused_var2", json.dumps(env_data))

    def test_circular_reference_handling(self):
        """Test that circular references in data structures are handled correctly."""
        # Create a circular structure
        circular_dict = {"name": "root"}
        circular_dict["self"] = circular_dict
        
        # This should not crash (though exact behavior depends on implementation)
        try:
            serialized = to_json(circular_dict)
            # If serialization succeeds, test that it includes reference markers
            self.assertIn("$ref", json.dumps(serialized))
        except (ValueError, TypeError):
            # If circular references cause an error, that's acceptable too
            pass

    def test_complex_nested_structure_roundtrip(self):
        """Test serialization of complex nested structures with closures."""
        # Set up a complex environment
        self.env["config"] = {"multiplier": 2, "offset": 10}
        self.env["processors"] = [
            eval_expr(["lambda", ["x"], ["*", "x", 2]], self.env),
            eval_expr(["lambda", ["x"], ["+", "x", 5]], self.env)
        ]
        
        # Create a complex closure that uses nested structures
        complex_expr = ["lambda", ["data"], 
                       ["map", ["first", "processors"], "data"]]
        original_complex = eval_expr(complex_expr, self.env)
        
        # Serialize and deserialize
        serialized = to_json(original_complex)
        deserialized = from_json(serialized, self.prelude)
        
        # Test functional equivalence
        test_env = Env(parent=self.prelude)
        test_env["fn"] = deserialized
        
        result = eval_expr(["fn", [1, 2, 3]], test_env)
        self.assertEqual(result, [2, 4, 6])  # Each element multiplied by 2

    def test_serialization_preserves_closure_semantics(self):
        """Test that closure semantics are preserved across serialization."""
        # Test lexical scoping preservation
        outer_expr = ["lambda", ["x"], 
                     ["lambda", ["y"], ["+", "x", "y"]]]
        outer_fn = eval_expr(outer_expr, self.env)
        
        # Create inner function
        test_env = Env(parent=self.prelude)
        test_env["outer"] = outer_fn
        inner_fn = eval_expr(["outer", 10], test_env)
        
        # Serialize and deserialize the inner function
        serialized = to_json(inner_fn)
        deserialized = from_json(serialized, self.prelude)
        
        # Test that lexical scoping still works
        test_env2 = Env(parent=self.prelude)
        test_env2["inner"] = deserialized
        result = eval_expr(["inner", 5], test_env2)
        self.assertEqual(result, 15)  # 10 + 5

    def test_json_format_compatibility(self):
        """Test that serialized format is valid JSON and follows expected structure."""
        # Create a test closure
        self.env["captured"] = {"key": "value"}
        closure_expr = ["lambda", ["x"], ["get", "captured", "@key"]]
        closure = eval_expr(closure_expr, self.env)
        
        # Serialize
        serialized = to_json(closure)
        
        # Verify it's valid JSON
        json_str = json.dumps(serialized)
        reparsed = json.loads(json_str)
        self.assertEqual(serialized, reparsed)
        
        # Verify expected structure
        self.assertEqual(reparsed["type"], "closure")
        self.assertIn("params", reparsed)
        self.assertIn("body", reparsed)
        self.assertIn("env", reparsed)
        self.assertIn("$ref", reparsed)

    def test_builtin_functions_not_serialized(self):
        """Test that built-in functions are not included in serialized environments."""
        # Create closure that uses built-ins
        closure_expr = ["lambda", ["lst"], ["map", ["+", 1], "lst"]]
        closure = eval_expr(closure_expr, self.env)
        
        # Serialize
        serialized = to_json(closure)
        
        # Verify built-ins are not in the serialized environment
        env_str = json.dumps(serialized["env"])
        self.assertNotIn("map", env_str)
        self.assertNotIn("+", env_str)
        self.assertNotIn("lambda", env_str)

    def test_large_data_structure_roundtrip(self):
        """Test serialization of larger data structures."""
        # Create a larger test structure
        large_list = list(range(1000))
        large_dict = {f"key_{i}": f"value_{i}" for i in range(100)}
        
        self.env["large_data"] = {"list": large_list, "dict": large_dict}
        
        closure_expr = ["lambda", [], ["length", ["get", "large_data", "@list"]]]
        closure = eval_expr(closure_expr, self.env)
        
        # Serialize and deserialize
        serialized = to_json(closure)
        deserialized = from_json(serialized, self.prelude)
        
        # Test functionality
        test_env = Env(parent=self.prelude)
        test_env["fn"] = deserialized
        result = eval_expr(["fn"], test_env)
        self.assertEqual(result, 1000)

if __name__ == '__main__':
    unittest.main()