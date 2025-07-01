import unittest
import json
from unittest.mock import patch

# Import from the refactored modules
from jsl import (
    eval_expr,
    Env,
    Closure,
    make_prelude,
    to_json,
    from_json,
    run_program,
)
from jsl import modules
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
        self.eval('[\"def\", \"outer_x\", 100]')
        # Let shadows outer_x
        self.assertEqual(self.eval('[\"let\", [[\"outer_x\", 1]], [\"+\", \"outer_x\", 1]]'), 2)
        # Outer_x remains unchanged
        self.assertEqual(self.eval('\"outer_x\"'), 100)

    def test_load_module(self):
        # Mock the file system to provide a virtual module file
        mock_file_content = '{"exports": {"my_var": 123, "my_func": ["lambda", ["x"], ["*", "x", 2]]}}'
        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_file_content)) as mock_file:
            # The path here is virtual, as we're mocking open
            module_env = modules.load_module("virtual/path/to/my_module.json", self.env)
            self.assertEqual(module_env.lookup("my_var"), 123)
            
            # Test that the function from the module works
            # Add module bindings to the current environment
            for name, value in module_env.get_bindings().items():
                self.env[name] = value
            self.assertEqual(self.eval('["my_func", 7]'), 14)

class TestJSLRunner(unittest.TestCase):

    def setUp(self):
        """Set up a fresh prelude for each test."""
        self.prelude = make_prelude()
        self.env = Env(parent=self.prelude)

    def eval(self, expr_str):
        """Helper to evaluate a JSL expression string."""
        expr = json.loads(expr_str)
        return eval_expr(expr, self.env)

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