"""
Test suite for JSL object construction functionality.

This file replaces the old template tests and demonstrates 
JSL's first-class object construction capabilities.
"""

import unittest
from jsl import eval_expression, make_prelude


class TestJSLObjectConstruction(unittest.TestCase):
    """Test JSL object construction as replacement for templates."""
    
    def setUp(self):
        """Set up test environment."""
        prelude = make_prelude()
        self.env = prelude.extend({})  # Extend to make modifiable
    
    def eval(self, expr_str):
        """Helper to evaluate JSL expression from string."""
        return eval_expression(expr_str, self.env)
    
    def test_simple_object_construction(self):
        """Test basic object construction with literal keys and values."""
        program = '{"@message": "@Hello", "@user": "@Alice"}'
        result = self.eval(program)
        expected = {"message": "Hello", "user": "Alice"}
        self.assertEqual(result, expected)
    
    def test_dynamic_string_construction(self):
        """Test object construction with dynamic string values."""
        program = '''
        ["do",
          ["def", "greeting", "@Hello"],
          ["def", "name", "@Alice"],
          {"@message": ["str-concat", "greeting", "@, ", "name", "@!"]}
        ]
        '''
        result = self.eval(program)
        expected = {"message": "Hello, Alice!"}
        self.assertEqual(result, expected)
    
    def test_nested_object_construction(self):
        """Test nested object construction."""
        program = '''
        ["do",
          ["def", "name", "@Alice"],
          ["def", "age", 25],
          {
            "@user": {
              "@name": "name",
              "@age": "age",
              "@is_adult": [">", "age", 18]
            },
            "@metadata": {
              "@version": "@1.0",
              "@timestamp": 1640995200
            }
          }
        ]
        '''
        result = self.eval(program)
        expected = {
            "user": {
                "name": "Alice",
                "age": 25,
                "is_adult": True
            },
            "metadata": {
                "version": "1.0",
                "timestamp": 1640995200
            }
        }
        self.assertEqual(result, expected)
    
    def test_object_with_arrays(self):
        """Test objects containing arrays."""
        program = '''
        ["do",
          ["def", "items", ["@", ["item1", "item2", "item3"]]],
          {
            "@data": "items",
            "@count": ["length", "items"],
            "@tags": ["@", ["tag1", "tag2"]]
          }
        ]
        '''
        result = self.eval(program)
        expected = {
            "data": ["item1", "item2", "item3"],
            "count": 3,
            "tags": ["tag1", "tag2"]
        }
        self.assertEqual(result, expected)
    
    def test_dynamic_keys(self):
        """Test objects with dynamically computed keys."""
        program = '''
        ["do",
          ["def", "field_name", "@username"],
          ["def", "field_value", "@alice"],
          {"field_name": "field_value"}
        ]
        '''
        result = self.eval(program)
        expected = {"username": "alice"}
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
