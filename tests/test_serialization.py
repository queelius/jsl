"""
Comprehensive test suite for JSL serialization functionality.

NOTE: These tests are specific to the recursive evaluator implementation
which uses Closure objects. The stack evaluator has its own serialization
tests in test_stack_serialization.py.
"""

import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

# These tests require the recursive evaluator
# The serialization module is designed for Closure objects from recursive evaluator
from jsl import (
    make_prelude, serialize, deserialize, 
    to_json, from_json, Closure, Env
)
from jsl.serialization import (
    serialize_program, deserialize_program
)
from jsl.core import JSLError, JSLTypeError, Evaluator

# Use recursive evaluator directly for these tests
def eval_expression(expr, env):
    """Helper that uses recursive evaluator directly."""
    evaluator = Evaluator()
    if isinstance(expr, str):
        import json
        expr = json.loads(expr)
    return evaluator.eval(expr, env)


class TestBasicSerialization(unittest.TestCase):
    """Test basic serialization functionality."""
    
    def setUp(self):
        """Set up test environment."""
        prelude = make_prelude()
        self.env = prelude.extend({})
    
    def test_serialize_primitives(self):
        """Test serialization of primitive values."""
        test_cases = [
            (42, "42"),
            (-17, "-17"),
            (3.14159, "3.14159"),
            (-2.5, "-2.5"),
            (0, "0"),
            (True, "true"),
            (False, "false"),
            (None, "null"),
            ("", '""'),
            ("hello", '"hello"'),
            ("with\nnewline", '"with\\nnewline"'),
            ("with\"quotes", '"with\\"quotes"'),
            ("unicode: 🚀", '"unicode: \\ud83d\\ude80"'),
        ]
        
        for value, expected_json in test_cases:
            with self.subTest(value=value):
                serialized = serialize(value)
                self.assertEqual(serialized, expected_json)
                
                # Round trip test
                deserialized = deserialize(serialized)
                self.assertEqual(value, deserialized)
    
    def test_serialize_collections(self):
        """Test serialization of lists and dictionaries."""
        test_cases = [
            # Empty collections
            ([], "[]"),
            ({}, "{}"),
            
            # Simple collections
            ([1, 2, 3], "[1, 2, 3]"),
            ({"a": 1, "b": 2}, '{"a": 1, "b": 2}'),
            
            # Nested collections
            ([[1, 2], [3, 4]], "[[1, 2], [3, 4]]"),
            ({"outer": {"inner": "value"}}, '{"outer": {"inner": "value"}}'),
            
            # Mixed types
            ([1, "hello", True, None], '[1, "hello", true, null]'),
            ({"num": 42, "str": "test", "bool": True, "null": None}, 
             '{"num": 42, "str": "test", "bool": true, "null": null}'),
        ]
        
        for value, expected_json in test_cases:
            with self.subTest(value=value):
                serialized = serialize(value)
                # Parse both to compare structure (order may vary for dicts)
                self.assertEqual(json.loads(serialized), json.loads(expected_json))
                
                # Round trip test
                deserialized = deserialize(serialized)
                self.assertEqual(value, deserialized)
    


class TestClosureSerialization(unittest.TestCase):
    """Test serialization of closures and functions."""
    
    def setUp(self):
        """Set up test environment."""
        prelude = make_prelude()
        self.env = prelude.extend({})
    
    def test_simple_closure_serialization(self):
        """Test serialization of simple closures."""
        # Simple lambda
        closure_expr = '["lambda", ["x"], ["*", "x", "x"]]'
        closure = eval_expression(closure_expr, self.env)
        
        serialized = serialize(closure)
        deserialized = deserialize(serialized, make_prelude())
        
        self.assertIsInstance(deserialized, Closure)
        self.assertEqual(deserialized.params, ["x"])
        self.assertEqual(deserialized.body, ["*", "x", "x"])
    
    def test_closure_with_multiple_params(self):
        """Test closure with multiple parameters."""
        closure_expr = '["lambda", ["x", "y", "z"], ["+", "x", "y", "z"]]'
        closure = eval_expression(closure_expr, self.env)
        
        serialized = serialize(closure)
        deserialized = deserialize(serialized, make_prelude())
        
        self.assertEqual(deserialized.params, ["x", "y", "z"])
        self.assertEqual(deserialized.body, ["+", "x", "y", "z"])
    
    def test_closure_with_captured_variables(self):
        """Test closure that captures variables from outer scope."""
        program = '''
        ["do",
          ["def", "outer_var", 100],
          ["def", "another_var", "@captured"],
          ["lambda", ["x"], ["+", "x", "outer_var", ["str-length", "another_var"]]]
        ]
        '''
        closure = eval_expression(program, self.env)
        
        serialized = serialize(closure)
        deserialized = deserialize(serialized, make_prelude())
        
        self.assertIsInstance(deserialized, Closure)
        self.assertEqual(deserialized.params, ["x"])
        # Environment should be captured
        self.assertIsNotNone(deserialized.env)
    
    def test_nested_closures(self):
        """Test serialization of nested closures (higher-order functions)."""
        program = '''
        ["do",
          ["def", "make_multiplier",
            ["lambda", ["factor"],
              ["lambda", ["x"], ["*", "x", "factor"]]
            ]
          ],
          ["def", "double", ["make_multiplier", 2]],
          "double"
        ]
        '''
        closure = eval_expression(program, self.env)
        
        serialized = serialize(closure)
        deserialized = deserialize(serialized, make_prelude())
        
        self.assertIsInstance(deserialized, Closure)
        # Should be the inner lambda with factor=2 captured
        self.assertEqual(deserialized.params, ["x"])
        self.assertEqual(deserialized.body, ["*", "x", "factor"])
    
    def test_recursive_closure(self):
        """Test serialization of recursive closures."""
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
          "factorial"
        ]
        '''
        closure = eval_expression(program, self.env)
        
        serialized = serialize(closure)
        deserialized = deserialize(serialized, make_prelude())
        
        self.assertIsInstance(deserialized, Closure)
        self.assertEqual(deserialized.params, ["n"])
        # Should have captured the recursive reference
        self.assertIsNotNone(deserialized.env)
    
    def test_closure_with_complex_body(self):
        """Test closure with complex, nested body."""
        program = '''
        ["lambda", ["data"],
          ["let", [["processed", ["map", ["lambda", ["x"], ["*", "x", 2]], "data"]]],
            ["reduce", "+", "processed", 0]
          ]
        ]
        '''
        closure = eval_expression(program, self.env)
        
        serialized = serialize(closure)
        deserialized = deserialize(serialized, make_prelude())
        
        self.assertIsInstance(deserialized, Closure)
        self.assertEqual(deserialized.params, ["data"])
        # Complex body should be preserved
        self.assertIsInstance(deserialized.body, list)
        self.assertEqual(deserialized.body[0], "let")


class TestEnvironmentSerialization(unittest.TestCase):
    """Test serialization of environments and scoping."""
    
    def setUp(self):
        """Set up test environment."""
        prelude = make_prelude()
        self.env = prelude.extend({})
    
    def test_environment_serialization(self):
        """Test serialization of environments."""
        # Create environment with bindings
        program = '''
        ["do",
          ["def", "x", 10],
          ["def", "y", "@hello"],
          ["def", "z", ["@", [1, 2, 3]]],
          ["lambda", ["a"], ["+", "a", "x"]]
        ]
        '''
        closure = eval_expression(program, self.env)
        
        serialized = serialize(closure)
        data = json.loads(serialized)
        
        # For CAS format, check the structure is correct
        if "__cas_version__" in data:
            # CAS format - env is in the objects table
            self.assertIn("objects", data)
            self.assertIn("root", data)
            
            # Find the closure object and check it has an env reference
            root_ref = data["root"]["__ref__"]
            closure_obj = data["objects"][root_ref]
            self.assertIn("env", closure_obj)
            
            # Find the env object and check bindings
            env_ref = closure_obj["env"]["__ref__"]
            env_obj = data["objects"][env_ref]
            self.assertIn("bindings", env_obj)
            
            bindings = env_obj["bindings"]
            self.assertIn("x", bindings)
            self.assertIn("y", bindings)
            self.assertIn("z", bindings)
            self.assertEqual(bindings["x"], 10)
            self.assertEqual(bindings["y"], "hello")
            self.assertEqual(bindings["z"], [1, 2, 3])
        else:
            # Direct format (shouldn't happen for closures, but handle it)
            self.assertIn("env", data)
            env_data = data["env"]
            self.assertIn("bindings", env_data)
            
            bindings = env_data["bindings"]
            self.assertIn("x", bindings)
            self.assertIn("y", bindings)
            self.assertIn("z", bindings)
            self.assertEqual(bindings["x"], 10)
            self.assertEqual(bindings["y"], "hello")
            self.assertEqual(bindings["z"], [1, 2, 3])
    
    def test_nested_environment_serialization(self):
        """Test serialization of nested environments."""
        program = '''
        ["let", [["outer", 100]],
          ["let", [["inner", 200]],
            ["lambda", ["x"], ["+", "x", "outer", "inner"]]
          ]
        ]
        '''
        closure = eval_expression(program, self.env)
        
        serialized = serialize(closure)
        deserialized = deserialize(serialized, make_prelude())
        
        # Should preserve nested scoping
        self.assertIsInstance(deserialized, Closure)
        self.assertIsNotNone(deserialized.env)
    
    def test_shared_environment_references(self):
        """Test that shared environments are handled correctly."""
        program = '''
        ["do",
          ["def", "shared_var", 42],
          ["def", "func1", ["lambda", ["x"], ["+", "x", "shared_var"]]],
          ["def", "func2", ["lambda", ["y"], ["*", "y", "shared_var"]]],
          ["list", "func1", "func2"]
        ]
        '''
        result = eval_expression(program, self.env)
        
        serialized = serialize(result)
        deserialized = deserialize(serialized, make_prelude())
        
        # Both functions should share the same environment
        self.assertIsInstance(deserialized, list)
        self.assertEqual(len(deserialized), 2)
        
        func1, func2 = deserialized
        self.assertIsInstance(func1, Closure)
        self.assertIsInstance(func2, Closure)


class TestComplexDataStructures(unittest.TestCase):
    """Test serialization of complex, mixed data structures."""
    
    def setUp(self):
        """Set up test environment."""
        prelude = make_prelude()
        self.env = prelude.extend({})

    def test_quoted_vs_unquoted_data(self):
        """Test that quoting prevents evaluation of lambda expressions."""
        program = '''
        ["do",
          ["def", "data", {
            "@quoted_lambdas": ["@", [
              ["lambda", ["x"], ["*", "x", 2]],
              ["lambda", ["y"], ["+", "y", 1]]
            ]],
            "@unquoted_lambdas": ["list",
              ["lambda", ["x"], ["*", "x", 2]],
              ["lambda", ["y"], ["+", "y", 1]]
            ]
          }],
          "data"
        ]
        '''
        result = eval_expression(program, self.env)
        
        serialized = serialize(result)
        deserialized = deserialize(serialized, make_prelude())
        
        # Quoted lambdas should remain as literal data (lists)
        quoted_lambdas = deserialized["quoted_lambdas"]
        self.assertIsInstance(quoted_lambdas, list)
        self.assertEqual(len(quoted_lambdas), 2)
        self.assertIsInstance(quoted_lambdas[0], list)  # Still a list, not a Closure
        self.assertEqual(quoted_lambdas[0], ["lambda", ["x"], ["*", "x", 2]])
        
        # Unquoted lambdas should be evaluated to Closures
        unquoted_lambdas = deserialized["unquoted_lambdas"]
        self.assertIsInstance(unquoted_lambdas, list)
        self.assertEqual(len(unquoted_lambdas), 2)
        self.assertIsInstance(unquoted_lambdas[0], Closure)  # Evaluated to Closure
        self.assertIsInstance(unquoted_lambdas[1], Closure)  # Evaluated to Closure
    
    def test_mixed_data_with_closures(self):
        """Test serialization of mixed data containing closures."""
        program = '''
        ["do",
          ["def", "func1", ["lambda", ["x"], ["*", "x", 2]]],
          ["def", "func2", ["lambda", ["y"], ["+", "y", 1]]],
          ["def", "data", {
            "@functions": ["list", "func1", "func2"],
            "@values": ["@", [1, 2, 3, 4, 5]],
            "@metadata": {"@version": 1, "@type": "@computation"}
          }],
          "data"
        ]
        '''
        result = eval_expression(program, self.env)
        
        serialized = serialize(result)
        deserialized = deserialize(serialized, make_prelude())
        
        # Structure should be preserved
        self.assertIsInstance(deserialized, dict)
        self.assertIn("functions", deserialized)
        self.assertIn("values", deserialized)
        self.assertIn("metadata", deserialized)
        
        # Functions should be closures (because func1 and func2 are variables that resolve to closures)
        functions = deserialized["functions"]
        self.assertIsInstance(functions, list)
        self.assertEqual(len(functions), 2)
        self.assertIsInstance(functions[0], Closure)  # Change: Closure, not list
        self.assertIsInstance(functions[1], Closure)  # Change: Closure, not list
        
        # Check closure properties instead of literal comparison
        self.assertEqual(functions[0].params, ["x"])     # Change: check params
        self.assertEqual(functions[0].body, ["*", "x", 2])  # Change: check body
        
        # Values should be preserved
        self.assertEqual(deserialized["values"], [1, 2, 3, 4, 5])
        
        # Metadata should be preserved
        metadata = deserialized["metadata"]
        self.assertEqual(metadata["version"], 1)
        self.assertEqual(metadata["type"], "computation")
    
    def test_deeply_nested_structures(self):
        """Test serialization of deeply nested structures."""
        program = '''
        {
          "@level1": {
            "@level2": {
              "@level3": {
                "@data": ["@", [1, 2, 3]],
                "@func": ["lambda", ["x"], ["*", "x", 10]]
              }
            }
          },
          "@other": ["@", [
            {"@name": "@item1", "@value": 100},
            {"@name": "@item2", "@value": 200}
          ]]
        }
        '''
        result = eval_expression(program, self.env)
        
        serialized = serialize(result)
        deserialized = deserialize(serialized, make_prelude())
        
        # Navigate to deeply nested function
        nested_func = deserialized["level1"]["level2"]["level3"]["func"]
        self.assertIsInstance(nested_func, Closure)
        self.assertEqual(nested_func.params, ["x"])
        
        # Other data should be preserved
        other_data = deserialized["other"]
        self.assertEqual(len(other_data), 2)
        self.assertEqual(other_data[0]["@name"], "@item1")
        self.assertEqual(other_data[1]["@value"], 200)
    
    def test_circular_references_in_data(self):
        """Test handling of circular references in data structures."""
        # Note: Pure data structures with circular refs can't be serialized
        data = {"a": 1}
        data["self"] = data  # Circular reference
        
        # Should raise RecursionError or similar for pure data circular references
        with self.assertRaises((RecursionError, ValueError, TypeError)) as ctx:
            serialize(data)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in serialization."""
    
    def setUp(self):
        """Set up test environment.""" 
        self.env = make_prelude()
    
    def test_invalid_json_deserialization(self):
        """Test deserialization of invalid JSON."""
        invalid_json_cases = [
            '{"invalid": json}',  # Invalid syntax
            '{invalid: "json"}',  # Unquoted keys
            '{"unclosed": "string',  # Unclosed string
            '[1, 2, 3,]',  # Trailing comma
            '',  # Empty string
            'undefined',  # Invalid literal
        ]
        
        for invalid_json in invalid_json_cases:
            with self.subTest(json_str=invalid_json):
                with self.assertRaises((json.JSONDecodeError, ValueError)):
                    deserialize(invalid_json)
    
    def test_unsupported_types_serialization(self):
        """Test serialization of unsupported types."""
        # Custom class that can't be serialized
        class CustomClass:
            def __init__(self, value):
                self.value = value
        
        unsupported_values = [
            CustomClass(42),
            lambda x: x + 1,  # Python lambda (not JSL closure)
            open(__file__),  # File object
            complex(1, 2),  # Complex number
        ]
        
        for value in unsupported_values:
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(TypeError):
                    serialize(value)
                    
        # Clean up file handle
        if hasattr(unsupported_values[2], 'close'):
            unsupported_values[2].close()
    
    def test_malformed_closure_data(self):
        """Test deserialization of malformed closure data."""
        # For CAS format, malformed data in objects table
        malformed_cases = [
            # Missing required fields
            {
                "__cas_version__": 1,
                "root": {"__ref__": "test"},
                "objects": {"test": {"__type__": "closure"}}  # Missing params and body
            },
            {
                "__cas_version__": 1,
                "root": {"__ref__": "test"},
                "objects": {"test": {"__type__": "closure", "params": ["x"]}}  # Missing body
            },
            {
                "__cas_version__": 1,
                "root": {"__ref__": "test"},
                "objects": {"test": {"__type__": "closure", "body": ["+", "x", 1]}}  # Missing params
            },
            # Invalid field types
            {
                "__cas_version__": 1,
                "root": {"__ref__": "test"},
                "objects": {"test": {"__type__": "closure", "params": "not_a_list", "body": ["+", "x", 1], "env": None}}
            },
            {
                "__cas_version__": 1,
                "root": {"__ref__": "test"},
                "objects": {"test": {"__type__": "closure", "params": ["x"], "body": "not_a_list", "env": None}}
            },
        ]
        
        for malformed_data in malformed_cases:
            with self.subTest(data=malformed_data):
                with self.assertRaises((KeyError, TypeError, AttributeError)):
                    deserialize(json.dumps(malformed_data), make_prelude())
    
    def test_environment_reconstruction_errors(self):
        """Test errors in environment reconstruction."""
        # For CAS format, create invalid env object in the objects table
        invalid_cas_data = {
            "__cas_version__": 1,
            "root": {"__ref__": "test_closure"},
            "objects": {
                "test_closure": {
                    "__type__": "closure",
                    "params": ["x"],
                    "body": ["+", "x", 1],
                    "env": {"__ref__": "test_env"}
                },
                "test_env": {
                    "__type__": "env",
                    "bindings": "not_a_dict"  # Should be dict
                }
            }
        }
        
        with self.assertRaises((TypeError, AttributeError, ValueError)):
            deserialize(json.dumps(invalid_cas_data), make_prelude())




class TestProgramSerialization(unittest.TestCase):
    """Test high-level program serialization functions."""
    
    def setUp(self):
        """Set up test environment."""
        prelude = make_prelude()
        self.env = prelude.extend({})
    
    def test_serialize_program(self):
        """Test serialize_program function."""
        program = ["+", 1, 2, 3]
        
        serialized = serialize_program(program, "test_prelude_hash")
        
        self.assertIsInstance(serialized, dict)
        self.assertIn("version", serialized)
        self.assertIn("prelude_hash", serialized)
        self.assertIn("program", serialized)
        self.assertEqual(serialized["prelude_hash"], "test_prelude_hash")
    
    def test_deserialize_program(self):
        """Test deserialize_program function."""
        original_program = ["*", 6, 7]
        program_data = serialize_program(original_program)
        
        reconstructed = deserialize_program(program_data, self.env)
        
        self.assertEqual(reconstructed, original_program)
    
    def test_program_serialization_round_trip(self):
        """Test complete program serialization round trip."""
        # Complex program with closures
        program = '''
        ["do",
          ["def", "fibonacci",
            ["lambda", ["n"],
              ["if", ["<=", "n", 1],
                "n",
                ["+", ["fibonacci", ["-", "n", 1]], ["fibonacci", ["-", "n", 2]]]
              ]
            ]
          ],
          ["fibonacci", 8]
        ]
        '''
        original_result = eval_expression(program, self.env)
        
        # Serialize as program
        program_data = serialize_program(original_result, "v1.0")
        
        # Deserialize
        reconstructed = deserialize_program(program_data, make_prelude())
        
        self.assertEqual(reconstructed, original_result)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_to_json_from_json_round_trip(self):
        """Test to_json and from_json round trip."""
        test_data = {
            "numbers": [1, 2, 3, 4, 5],
            "text": "hello world",
            "nested": {
                "boolean": True,
                "null_value": None,
                "float": 3.14159
            }
        }
        
        json_data = to_json(test_data)
        reconstructed = from_json(json_data)
        
        self.assertEqual(reconstructed, test_data)
    
    def test_from_json_with_string_input(self):
        """Test from_json with string input."""
        json_string = '{"key": "value", "number": 42}'
        
        result = from_json(json_string)
        
        expected = {"key": "value", "number": 42}
        self.assertEqual(result, expected)
    
    def test_from_json_with_dict_input(self):
        """Test from_json with dict input."""
        json_dict = {"key": "value", "number": 42}
        
        result = from_json(json_dict)
        
        self.assertEqual(result, json_dict)


class TestPerformanceAndEdgeCases(unittest.TestCase):
    """Test performance characteristics and edge cases."""
    
    def setUp(self):
        """Set up test environment."""
        prelude = make_prelude()
        self.env = prelude.extend({})
    
    def test_large_data_structures(self):
        """Test serialization of large data structures."""
        # Large list
        large_list = list(range(10000))
        serialized = serialize(large_list)
        deserialized = deserialize(serialized)
        self.assertEqual(deserialized, large_list)
        
        # Large dictionary
        large_dict = {f"key_{i}": f"value_{i}" for i in range(1000)}
        serialized = serialize(large_dict)
        deserialized = deserialize(serialized)
        self.assertEqual(deserialized, large_dict)
    
    def test_deeply_nested_structures(self):
        """Test deeply nested data structures."""
        # Create deeply nested list
        nested = []
        current = nested
        for i in range(100):
            inner = []
            current.append(inner)
            current = inner
        current.append("deep_value")
        
        serialized = serialize(nested)
        deserialized = deserialize(serialized)
        
        # Navigate to deep value
        current = deserialized
        for i in range(100):
            current = current[0]
        self.assertEqual(current[0], "deep_value")
    
    def test_unicode_handling(self):
        """Test proper Unicode handling."""
        unicode_data = {
            "emoji": "🚀🌟💫",
            "chinese": "你好世界",
            "arabic": "مرحبا بالعالم",
            "russian": "Привет мир",
            "mixed": "Hello 世界 🌍"
        }
        
        serialized = serialize(unicode_data)
        deserialized = deserialize(serialized)
        
        self.assertEqual(deserialized, unicode_data)
    
    def test_special_float_values(self):
        """Test handling of special float values."""
        import math
        
        # We use strict JSON, so inf/nan should raise errors
        special_values = [float('inf'), float('-inf'), float('nan')]
        
        for value in special_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    serialize(value)
    
    def test_empty_structures(self):
        """Test handling of empty structures."""
        empty_cases = [
            [],
            {},
            "",
            [[]],
            [{}],
            {"empty_list": [], "empty_dict": {}, "empty_string": ""}
        ]
        
        for case in empty_cases:
            with self.subTest(case=case):
                serialized = serialize(case)
                deserialized = deserialize(serialized)
                self.assertEqual(deserialized, case)


class TestFileSystemIntegration(unittest.TestCase):
    """Test serialization with file system operations."""
    
    def setUp(self):
        """Set up test environment."""
        prelude = make_prelude()
        self.env = prelude.extend({})
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_serialize_to_file(self):
        """Test serializing data to file."""
        data = {"message": "Hello, file system!", "numbers": [1, 2, 3]}
        file_path = os.path.join(self.temp_dir, "test_data.json")
        
        # Serialize to file (without indent parameter)
        serialized = serialize(data)
        
        # Pretty print manually if needed
        pretty_json = json.dumps(json.loads(serialized), indent=2)
        
        with open(file_path, 'w') as f:
            f.write(pretty_json)
        
        # Read back and deserialize
        with open(file_path, 'r') as f:
            content = f.read()
        
        deserialized = deserialize(content)
        self.assertEqual(deserialized, data)
    
    def test_serialize_closure_to_file(self):
        """Test serializing closure to file."""
        program = '''
        ["do",
          ["def", "base_value", 100],
          ["lambda", ["x"], ["+", "x", "base_value"]]
        ]
        '''
        closure = eval_expression(program, self.env)
        file_path = os.path.join(self.temp_dir, "closure.json")
        
        # Serialize to file (without indent parameter)
        serialized = serialize(closure)
        
        # Pretty print manually if needed
        pretty_json = json.dumps(json.loads(serialized), indent=2)
        
        with open(file_path, 'w') as f:
            f.write(pretty_json)
        
        # Read back and deserialize
        with open(file_path, 'r') as f:
            content = f.read()
        
        deserialized = deserialize(content, make_prelude())
        self.assertIsInstance(deserialized, Closure)
        self.assertEqual(deserialized.params, ["x"])
    
