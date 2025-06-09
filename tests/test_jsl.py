import unittest
import json
from unittest.mock import patch

# Adjust the import path based on how you run your tests
# If running `python -m unittest discover` from the root, this should work:
from jsl.jsl import (
    eval_expr,
    Env,
    Closure,
    make_prelude,
    to_json,
    # from_json, # Add if you implement and want to test it
    run_program,
    load_module
)
# If jsl_host_dispatcher is in the same jsl package:
from jsl import jsl_host_dispatcher

# A simple mock for process_host_request
def mock_process_host_request(request_message):
    command = request_message[1]
    args = request_message[2:]
    if command == "echo":
        return args[0] if args else None
    if command == "test/add":
        return sum(args)
    if command == "test/error":
        return {"$jsl_host_error": {"type": "TestError", "message": "This is a test error", "details": {"arg": args[0] if args else None}}}
    return {"$jsl_host_error": {"type": "UnknownCommand", "message": f"Unknown command: {command}"}}

class TestJSLEvaluator(unittest.TestCase):

    def setUp(self):
        """Set up a fresh prelude for each test."""
        self.prelude = make_prelude()
        self.env = Env(parent=self.prelude)

    def eval(self, expr_str):
        """Helper to evaluate a JSL expression string."""
        # JSL expressions are lists/atoms, so we parse the JSON string representation
        expr = json.loads(expr_str)
        return eval_expr(expr, self.env)

    def test_literals(self):
        self.assertEqual(self.eval("123"), 123)
        self.assertEqual(self.eval('"@hello"'), "hello") # Note: JSL string literals start with @
        self.assertEqual(self.eval("true"), True)
        self.assertEqual(self.eval("false"), False)
        self.assertEqual(self.eval("null"), None)

    def test_arithmetic(self):
        self.assertEqual(self.eval('["+", 1, 2, 3]'), 6)
        self.assertEqual(self.eval('["-", 10, 2, 3]'), 5)
        self.assertEqual(self.eval('["*", 2, 3, 4]'), 24)
        self.assertEqual(self.eval('["/", 20, 2, 5]'), 2.0)

    def test_def_and_lookup(self):
        self.eval('["def", "x", 100]')
        self.assertEqual(self.env.lookup("x"), 100)
        # Corrected line: "x" is a JSL symbol, its JSON representation is "\"x\""
        self.assertEqual(self.eval('"x"'), 100)

    def test_lambda_and_application(self):
        self.eval('["def", "add", ["lambda", ["a", "b"], ["+", "a", "b"]]]')
        self.assertEqual(self.eval('["add", 5, 7]'), 12)

        closure = self.eval('["lambda", ["x"], ["*", "x", 2]]')
        self.assertIsInstance(closure, Closure)

    def test_if_special_form(self):
        self.assertEqual(self.eval('["if", true, 1, 2]'), 1)
        self.assertEqual(self.eval('["if", false, 1, 2]'), 2)
        self.assertEqual(self.eval('["if", ["=", 1, 1], "@yes", "@no"]'), "yes")

    def test_do_special_form(self):
        self.assertEqual(self.eval('["do", ["def", "a", 1], ["def", "b", 2], ["+", "a", "b"]]'), 3)
        self.assertEqual(self.env.lookup("a"), 1)
        self.assertEqual(self.env.lookup("b"), 2)

    def test_let_special_form_simple(self):
        # Simple let binding
        self.assertEqual(self.eval('["let", [["x", 10]], "x"]'), 10)
        # Ensure 'x' is not defined in the outer environment
        with self.assertRaises(NameError):
            self.env.lookup("x")

        # Multiple bindings
        self.assertEqual(self.eval('["let", [["x", 2], ["y", 3]], ["*", "x", 4, "y"]]'), 24)
        with self.assertRaises(NameError):
            self.env.lookup("x")
        with self.assertRaises(NameError):
            self.env.lookup("y")
            
    def test_let_special_form_scoping(self):
        self.eval('["def", "outer_x", 100]')
        # Let shadows outer_x
        self.assertEqual(self.eval('["let", [["outer_x", 1]], ["+", "outer_x", 1]]'), 2)
        # Outer_x remains unchanged
        self.assertEqual(self.eval('"outer_x"'), 100)

        # Bindings in 'let' are evaluated in the outer scope (parallel binding)
        self.eval('["def", "a", 5]')
        self.assertEqual(self.eval('["let", [["x", "a"], ["a", 10]], "x"]'), 5) # x gets old 'a'
        self.assertEqual(self.eval('"a"'), 5) # outer 'a' is unchanged by let's internal 'a' binding

    def test_let_special_form_nested(self):
        # program = '''
        # ["let", [["x", 10]],
        #     ["let", [["y", ["+", "x", 5]]],
        #         ["*", "x", "y"]
        #     ]
        # ]
        # '''
        # self.assertEqual(self.eval(program), 150) # 10 * (10 + 5)

        program_shadowing = '''
        ["let", [["x", 1]],
            ["let", [["x", 2], ["y", "x"]], 
                ["+", "x", "y"] 
            ]
        ]
        '''
        # Inner 'y' should bind to outer 'x' (1) due to parallel binding evaluation
        # Inner 'x' is 2. So, 2 + 1 = 3
        self.assertEqual(self.eval(program_shadowing), 3)


    def test_let_special_form_with_closures(self):
        self.eval('["def", "global_val", 50]')
        program = '''
        ["let", [["local_val", 10]],
            ["let", [
                ["get_local", ["lambda", [], "local_val"]],
                ["get_global_not_shadowed", ["lambda", [], "global_val"]], 
                ["global_val", 5] 
              ],
              ["list", 
                ["get_local"], 
                ["get_global_not_shadowed"] 
              ]
            ]
        ]
        '''
        # get_local should capture local_val = 10
        # get_global_not_shadowed should capture the outer's global_val = 50, since
        # the variables in the let list are lexically scoped to the outer body
        results = self.eval(program)
        self.assertEqual(results[0], 10) 
        self.assertEqual(results[1], 50)
        
        # Ensure outer global_val is not affected
        # self.assertEqual(self.eval('"global_val"'), 50)

    def test_let_special_form_empty_bindings(self):
        self.assertEqual(self.eval('["let", [], 42]'), 42)
        self.eval('["def", "k", 99]')
        self.assertEqual(self.eval('["let", [], "k"]'), 99)

    def test_let_special_form_invalid_syntax(self):
        with self.assertRaisesRegex(ValueError, "let expects exactly two arguments"):
            self.eval('["let", [["x", 1]]]') # Missing body
        with self.assertRaisesRegex(ValueError, "let bindings must be a list"):
            self.eval('["let", {"x": 1}, "x"]') # Bindings not a list
        with self.assertRaisesRegex(ValueError, "Each let binding must be a list"):
            self.eval('["let", [["x"], ["y", 2]], "x"]') # Invalid binding pair
        with self.assertRaisesRegex(ValueError, "Each let binding must be a list"):
            self.eval('["let", [["x", 1, 2]], "x"]') # Invalid binding pair length
        # Adjust the regex to match the actual error message format
        with self.assertRaisesRegex(ValueError, r"let binding name must be a string, got int"):
            self.eval('["let", [[123, 1]], "x"]') # Variable name not a string

    def test_quote_special_form(self):
        self.assertEqual(self.eval('["quote", [1, 2, "a"]]'), [1, 2, "a"])
        self.assertEqual(self.eval('["quote", "x"]'), "x")

    def test_json_special_form_simple(self):
        # Test with JSL string literals for keys and values, and other JSON primitives
        program = '["json", {"@name": "@Alice", "@age": 30, "@isActive": true, "@data": null}]'
        expected = {"name": "Alice", "age": 30, "isActive": True, "data": None}
        self.assertEqual(self.eval(program), expected)

        # Test with a list template containing JSL string literals and other JSON primitives
        program_list = '["json", ["@item1", 100, false, null]]'
        expected_list = ["item1", 100, False, None]
        self.assertEqual(self.eval(program_list), expected_list)

    def test_json_special_form_with_symbol_lookups(self):
        self.eval('["def", "user_name_var", "@Bob"]') # user_name_var is bound to Python string "Bob"
        self.eval('["def", "user_age_var", 42]')
        self.eval('["def", "key_name_var", "@status"]') # key_name_var is bound to Python string "status"
        self.eval('["def", "is_active_var", true]')
        self.eval('["def", "details_var", {"@city": "@New York", "@zip": 10001}]') # details_var is bound to a Python dict

        # Template uses symbols that will be looked up.
        # eval_template will use the *values* of these symbols.
        program = '["json", {"@name": "user_name_var", "key_name_var": "is_active_var", "@fixed_key": "user_age_var", "@nested": "details_var"}]'
        expected = {
            "name": "Bob",                          # eval_template("user_name_var") -> lookup -> "Bob"
            "status": True,                         # eval_template("key_name_var") -> "status" (key)
                                                    # eval_template("is_active_var") -> lookup -> True (value)
            "fixed_key": 42,                        # eval_template("@fixed_key") -> "fixed_key" (key)
                                                    # eval_template("user_age_var") -> lookup -> 42 (value)
            "nested": {"city": "New York", "zip": 10001} # eval_template("details_var") -> lookup -> {"@city":"@New York", ...}
                                                         # then eval_template is called on this looked-up dict:
                                                         # eval_template({"@city":"@New York", "@zip":10001})
                                                         # -> {"city":"New York", "zip":10001}
        }
        self.assertEqual(self.eval(program), expected)

        program_list = '["json", ["user_name_var", "user_age_var", "is_active_var", "details_var"]]'
        expected_list = [
            "Bob",
            42,
            True,
            {"city": "New York", "zip": 10001} # Same logic as above for details_var
        ]
        self.assertEqual(self.eval(program_list), expected_list)

    def test_prelude_list_functions(self):
        self.assertEqual(self.eval('["list", 1, 2, 3]'), [1, 2, 3])
        self.assertEqual(self.eval('["first", ["list", 1, 2]]'), 1)
        self.assertEqual(self.eval('["rest", ["list", 1, 2, 3]]'), [2, 3])
        self.assertEqual(self.eval('["length", ["list", 1, 2, 3, 4]]'), 4)

    def test_prelude_map_function(self):
        self.eval('["def", "double", ["lambda", ["x"], ["*", "x", 2]]]')
        self.assertEqual(self.eval('["map", "double", ["list", 1, 2, 3]]'), [2, 4, 6])

    @patch('jsl.jsl.process_host_request', side_effect=mock_process_host_request)
    def test_host_special_form_success(self, mock_host_fn):
        # Test successful host call
        result = self.eval('["host", "@echo", "@hello world"]')
        self.assertEqual(result, "hello world")
        mock_host_fn.assert_called_with(["host", "echo", "hello world"])

        result_add = self.eval('["host", "@test/add", 10, 20]')
        self.assertEqual(result_add, 30)
        mock_host_fn.assert_called_with(["host", "test/add", 10, 20])
        
    @patch('jsl.jsl.process_host_request', side_effect=mock_process_host_request)
    def test_host_special_form_jhip_error(self, mock_host_fn):
        # Test host call that returns a JHIP error
        # Corrected regex: use r"..." for raw string and expect 'fail' instead of '@fail' in details
        with self.assertRaisesRegex(RuntimeError, r"Host error \(TestError\): This is a test error - Details: {'arg': 'fail'}"):
            self.eval('["host", "@test/error", "@fail"]')
        mock_host_fn.assert_called_with(["host", "test/error", "fail"])

    def test_serialization_simple_values(self):
        self.assertEqual(to_json(123), 123)
        self.assertEqual(to_json("hello"), "hello")
        self.assertEqual(to_json(True), True)
        self.assertEqual(to_json(None), None)
        self.assertEqual(to_json([1, "a", False]), [1, "a", False])
        self.assertEqual(to_json({"x": 1, "y": "b"}), {"x": 1, "y": "b"})

    def test_serialization_closure(self):
        # Define a closure in an environment
        self.eval('["def", "outer_var", 10]')
        self.eval('["def", "my_closure", ["lambda", ["x"], ["+", "x", "outer_var"]]]')
        
        closure_obj = self.env.lookup("my_closure")
        self.assertIsInstance(closure_obj, Closure)
        
        serialized_closure = to_json(closure_obj)
        
        self.assertIsInstance(serialized_closure, dict)
        self.assertEqual(serialized_closure.get("type"), "closure")
        self.assertEqual(serialized_closure.get("params"), ["x"])
        self.assertIsNotNone(serialized_closure.get("body"))
        self.assertIsNotNone(serialized_closure.get("env"))
        
        # Check that only 'outer_var' is in the serialized env (and not prelude items)
        # This part of the test depends heavily on the exact structure of to_json_env_user_only
        # and find_free_variables.
        # For a simple test, we can check if 'outer_var' is present in the serialized env representation.
        # A more robust test would involve deserializing and checking functionality.
        
        # A simple check:
        env_dump = json.dumps(serialized_closure["env"]) # Check if serializable
        self.assertIn("outer_var", env_dump)
        self.assertNotIn("'+'", env_dump) # '+' is a prelude function

    # Add test_deserialization when from_json is robust

    def test_load_module(self):
        # Create a dummy module file
        module_content = '''
        [
            ["def", "mod_func", ["lambda", ["y"], ["*", "y", 10]]],
            ["def", "mod_val", 100]
        ]
        '''
        with open("temp_module.json", "w") as f:
            f.write(module_content)
        
        exports = load_module("temp_module.json", self.prelude)
        
        self.assertIn("mod_func", exports)
        self.assertIn("mod_val", exports)
        self.assertIsInstance(exports["mod_func"], Closure)
        self.assertEqual(exports["mod_val"], 100)
        
        # Clean up dummy file
        import os
        os.remove("temp_module.json")

    def test_run_program_simple_list(self):
        program = [
            ["def", "a", 5],
            ["+", "a", 3]
        ]
        result = run_program(program, self.env)
        self.assertEqual(result, 8)
        self.assertEqual(self.env.lookup("a"), 5)

    def test_run_program_dict_with_entrypoint(self):
        program = {
            "forms": [
                ["def", "b", 12]
            ],
            "entrypoint": ["*", "b", 2]
        }
        result = run_program(program, self.env)
        self.assertEqual(result, 24)
        self.assertEqual(self.env.lookup("b"), 12)

    def test_run_program_dict_no_entrypoint(self):
        program = {
            "forms": [
                ["def", "c", 3],
                ["+", "c", 1] # This should be the result
            ]
        }
        result = run_program(program, self.env)
        self.assertEqual(result, 4)


if __name__ == '__main__':
    unittest.main()