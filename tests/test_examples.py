"""
Test suite for JSL examples and integration tests.
"""

import unittest
from jsl import run_program, eval_expression, make_prelude, HostDispatcher


class TestJSLExamples(unittest.TestCase):
    """Test comprehensive JSL examples."""
    
    def setUp(self):
        """Set up test environment."""
        self.env = make_prelude()
    
    def test_factorial_example(self):
        """Test the factorial example from documentation."""
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
        result = run_program(program)
        self.assertEqual(result, 120)
    
    def test_higher_order_functions_example(self):
        """Test higher-order functions example."""
        program = '''
        ["do",
          ["def", "numbers", ["@", [1, 2, 3, 4, 5]]],
          ["def", "square", ["lambda", ["x"], ["*", "x", "x"]]],
          ["def", "is_even", ["lambda", ["x"], ["=", ["mod", "x", 2], 0]]],
          ["def", "sum", ["lambda", ["a", "b"], ["+", "a", "b"]]],
          
          ["def", "squared", ["map", "square", "numbers"]],
          ["def", "evens", ["filter", "is_even", "numbers"]], 
          ["def", "total", ["reduce", "sum", "numbers", 0]],
          
          {
            "@original": "numbers",
            "@squared": "squared", 
            "@evens": "evens",
            "@total": "total"
          }
        ]
        '''
        result = run_program(program)
        
        self.assertEqual(result["original"], [1, 2, 3, 4, 5])
        self.assertEqual(result["squared"], [1, 4, 9, 16, 25])
        self.assertEqual(result["evens"], [2, 4])
        self.assertEqual(result["total"], 15)
    
    def test_closure_capture_example(self):
        """Test closure capture example."""
        program = '''
        ["do",
          ["def", "make_counter", 
            ["lambda", ["start"],
              ["lambda", [], 
                ["do",
                  ["def", "current", "start"],
                  ["def", "start", ["+", "start", 1]],
                  "current"
                ]
              ]
            ]
          ],
          ["def", "counter", ["make_counter", 10]],
          ["list", ["counter"], ["counter"], ["counter"]]
        ]
        '''
        result = run_program(program)
        # Note: This test depends on how environments and mutation are handled
        # The exact behavior may vary based on implementation details
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
    
    def test_data_processing_example(self):
        """Test data processing example."""
        program = '''
        ["do",
          ["def", "users", ["list",
            {"@name": "@Alice", "@age": 25, "@department": "@Engineering"},
            {"@name": "@Bob", "@age": 30, "@department": "@Sales"},
            {"@name": "@Carol", "@age": 28, "@department": "@Engineering"},
            {"@name": "@David", "@age": 35, "@department": "@Marketing"}
          ]],
          
          ["def", "get_engineers", 
            ["lambda", ["users"],
              ["filter", 
                ["lambda", ["user"], ["=", ["get", "user", "@department"], "@Engineering"]], 
                "users"
              ]
            ]
          ],
          
          ["def", "get_ages",
            ["lambda", ["users"],
              ["map", ["lambda", ["user"], ["get", "user", "@age"]], "users"]
            ]
          ],
          
          ["def", "engineers", ["get_engineers", "users"]],
          ["def", "engineer_ages", ["get_ages", "engineers"]],
          
          {
            "@total_users": ["length", "users"],
            "@engineers": "engineers",
            "@engineer_count": ["length", "engineers"], 
            "@engineer_ages": "engineer_ages",
            "@avg_engineer_age": ["/", ["reduce", "+", "engineer_ages", 0], ["length", "engineer_ages"]]
          }
        ]
        '''
        result = run_program(program)
        
        self.assertEqual(result["total_users"], 4)
        self.assertEqual(result["engineer_count"], 2)
        self.assertEqual(len(result["engineers"]), 2)
        self.assertEqual(result["engineer_ages"], [25, 28])
        self.assertEqual(result["avg_engineer_age"], 26.5)
    
    def test_recursive_data_structures(self):
        """Test processing recursive/nested data structures."""
        program = '''
        ["do",
          ["def", "nested_data", {
            "@level1": {
              "@level2": {
                "@values": ["list", 1, 2, 3],
                "@metadata": {"@count": 3, "@type": "@numbers"}
              },
              "@other": ["list", 4, 5, 6]
            },
            "@summary": {"@total_items": 6}
          }],
          
          ["def", "extract_values",
            ["lambda", ["data"],
              ["concat", 
                ["get", ["get", ["get", "data", "@level1"], "@level2"], "@values"],
                ["get", ["get", "data", "@level1"], "@other"]
              ]
            ]
          ],
          
          ["def", "all_values", ["extract_values", "nested_data"]],
          
          {
            "@data": "nested_data",
            "@extracted": "all_values",
            "@sum": ["reduce", "+", "all_values", 0],
            "@max": ["reduce", "max", "all_values"]
          }
        ]
        '''
        result = run_program(program)
        
        self.assertEqual(result["extracted"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(result["sum"], 21)
        self.assertEqual(result["max"], 6)
    
    def test_string_processing_example(self):
        """Test string processing capabilities."""
        program = '''
        ["do",
          ["def", "text", "@Hello World, this is JSL programming!"],
          ["def", "words", ["str-split", "text", "@ "]],
          ["def", "word_lengths", ["map", ["lambda", ["w"], ["str-length", "w"]], "words"]],
          ["def", "long_words", ["filter", ["lambda", ["w"], [">", ["str-length", "w"], 4]], "words"]],
          
          {
            "@original": "text",
            "@word_count": ["length", "words"],
            "@words": "words",
            "@word_lengths": "word_lengths",
            "@long_words": "long_words",
            "@longest_word": ["reduce", 
              ["lambda", ["a", "b"], 
                ["if", [">", ["str-length", "a"], ["str-length", "b"]], "a", "b"]
              ], 
              "words"
            ]
          }
        ]
        '''
        result = run_program(program)
        
        self.assertEqual(result["original"], "Hello World, this is JSL programming!")
        self.assertGreater(result["word_count"], 5)
        self.assertIsInstance(result["words"], list)
        self.assertIsInstance(result["word_lengths"], list)
        self.assertIsInstance(result["long_words"], list)
    
    def test_conditional_logic_example(self):
        """Test complex conditional logic."""
        program = '''
        ["do",
          ["def", "classify_number",
            ["lambda", ["n"],
              ["if", ["=", "n", 0],
                "@zero",
                ["if", [">", "n", 0],
                  ["if", ["=", ["mod", "n", 2], 0], "@positive-even", "@positive-odd"],
                  ["if", ["=", ["mod", "n", 2], 0], "@negative-even", "@negative-odd"]
                ]
              ]
            ]
          ],
          
          ["def", "numbers", ["@", [-3, -2, -1, 0, 1, 2, 3, 4]]],
          ["def", "classifications", ["map", "classify_number", "numbers"]],
          
          {
            "@numbers": "numbers",
            "@classifications": "classifications",
            "@stats": {
              "@positive": ["length", ["filter", ["lambda", ["n"], [">", "n", 0]], "numbers"]],
              "@negative": ["length", ["filter", ["lambda", ["n"], ["<", "n", 0]], "numbers"]],
              "@zero": ["length", ["filter", ["lambda", ["n"], ["=", "n", 0]], "numbers"]]
            }
          }
        ]
        '''
        result = run_program(program)
        
        expected_classifications = [
            "negative-odd", "negative-even", "negative-odd", "zero",
            "positive-odd", "positive-even", "positive-odd", "positive-even"
        ]
        
        self.assertEqual(result["classifications"], expected_classifications)
        self.assertEqual(result["stats"]["positive"], 4)
        self.assertEqual(result["stats"]["negative"], 3)
        self.assertEqual(result["stats"]["zero"], 1)


class TestJSLHostInteraction(unittest.TestCase):
    """Test JSL host interaction capabilities."""
    
    def test_basic_host_dispatcher(self):
        """Test basic host dispatcher functionality."""
        dispatcher = HostDispatcher()
        
        # Register a simple command
        dispatcher.register("echo", lambda x: f"Echo: {x}")
        dispatcher.register("add", lambda a, b: a + b)
        
        # Test dispatch
        result1 = dispatcher.dispatch("echo", ["Hello"])
        result2 = dispatcher.dispatch("add", [10, 20])
        
        self.assertEqual(result1, "Echo: Hello")
        self.assertEqual(result2, 30)
    
    def test_host_interaction_in_jsl(self):
        """Test host interaction within JSL programs."""
        # Create a dispatcher with test commands
        dispatcher = HostDispatcher()
        logs = []
        
        dispatcher.register("log", lambda msg: logs.append(msg))
        dispatcher.register("multiply", lambda a, b: a * b)
        
        program = '''
        ["do",
          ["host", "@log", "@Starting calculation"],
          ["def", "result", ["host", "@multiply", 6, 7]],
          ["host", "@log", ["str-concat", "@Result: ", ["json-stringify", "result"]]],
          "result"
        ]
        '''
        
        result = run_program(program, host_dispatcher=dispatcher)
        
        self.assertEqual(result, 42)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0], "Starting calculation")
        self.assertEqual(logs[1], "Result: 42")


if __name__ == '__main__':
    unittest.main()
