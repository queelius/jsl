import unittest
import json
import os
import tempfile
from unittest.mock import patch
from typing import Any

# Assuming 'jsl' is a package in PYTHONPATH or structured for such imports
from jsl import jsl 
from jsl.jsl import (
    Env,
    Closure,
    make_prelude,
    run_with_imports,
    to_json,
    from_json, # Assuming from_json is ready for testing
    eval_expr  # For testing deserialized closures
)

class TestJSLAdvanced(unittest.TestCase):

    def setUp(self):
        """Set up a fresh prelude and environment for each test."""
        jsl.prelude = None # Reset global prelude to ensure make_prelude creates a fresh one
        self.prelude = make_prelude()
        self.env = Env(parent=self.prelude)
        self.temp_files = []

    def tearDown(self):
        """Clean up any temporary files created during tests."""
        for f_path in self.temp_files:
            try:
                if os.path.exists(f_path):
                    os.remove(f_path)
            except OSError:
                pass # Ignore cleanup errors
        self.temp_files = []

    def _create_temp_file(self, name_prefix: str, content_obj: Any, suffix: str = ".json") -> str:
        """Helper to create a temporary JSON file and return its path."""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=f"{name_prefix}_", text=True)
        with os.fdopen(fd, "w") as tmp:
            json.dump(content_obj, tmp)
        self.temp_files.append(path)
        return path

    def test_nested_module_imports(self):
        """Test a module that imports another module."""
        # Grandchild module (gc_mod.json)
        gc_mod_content = [
            ["def", "gc_val", 100]
        ]
        gc_mod_path = self._create_temp_file("gc_mod", gc_mod_content)

        # Child module (child_mod.json) - imports gc_mod
        # For child_mod to import gc_mod, its program structure needs to support it.
        # Assuming run_with_imports is called recursively or load_module handles nested structures.
        # For this test, we'll assume child_mod's environment is pre-configured
        # by how load_module or run_program within load_module would work.
        # This test might be more about how load_module itself sets up the env for the module code.
        
        # Let's simplify: child_mod defines a function that *would* use gc_mod if it were bound.
        # We'll bind gc_mod when loading child_mod.
        # This tests if the environment passed to load_module is used.

        child_mod_content = [
            ["def", "get_gc_val_plus", ["lambda", ["x"], ["+", "x", ["get", "grandchild", "@gc_val"]]]]
        ]
        child_mod_path = self._create_temp_file("child_mod_nested", child_mod_content)
        
        # Main program imports child_mod
        main_prog_content = {
            "entrypoint": [["get", "child", "@get_gc_val_plus"], 50]
        }
        main_prog_path = self._create_temp_file("main_nested", main_prog_content)

        # To make this work, load_module needs to be able to take an environment
        # that might already have other modules bound.
        # run_with_imports sets up the top-level env.
        # If child_mod itself had an "imports" section, that would be more complex.
        # Let's test a simpler scenario: main binds child, and child expects 'grandchild' to be in its load-time env.
        # This means the 'prelude_env' for load_module needs to be richer.

        # This test setup is tricky with the current run_with_imports.
        # A true nested import would require modules to declare their own imports.
        # For now, let's simulate by having main bind both and child use grandchild.
        
        main_prog_content_v2 = {
            # grandchild is bound directly by main, child uses it.
            "entrypoint": [["get", "child", "@get_gc_val_plus"], 50]
        }
        main_prog_path_v2 = self._create_temp_file("main_nested_v2", main_prog_content_v2)

        cli_bindings = {
            "child": child_mod_path,
            "grandchild": gc_mod_path # Main program binds grandchild too
        }
        # When child_mod_path is loaded, its load_module call will use a prelude_env.
        # If run_with_imports makes 'grandchild' available in that env, it works.
        # The current load_module(module_path, prelude_env) uses prelude_env as parent.
        # So, for child_mod to see 'grandchild', 'grandchild' must be in prelude_env.
        # This is not how run_with_imports currently structures it.

        # Let's adjust the test to reflect how run_with_imports works:
        # All modules are loaded into the main program's environment.
        # If a module's code (e.g., a lambda defined in it) needs to access another module,
        # that other module must have been available in the environment where the lambda was defined.

        # child_mod.json:
        #   ["def", "child_func", ["lambda", ["x"], ["+", "x", ["get", "gc_alias_in_child_env", "@gc_val"]]]]
        # This means when child_mod is loaded, its environment must contain "gc_alias_in_child_env".
        # This is not directly supported by simple load_module(path, prelude).

        # Let's simplify the test to a module using another module's value IF that value
        # was passed into its defining environment (which is not standard module import).

        # Test: Module A defines a function. Module B calls it.
        mod_callee_content = [["def", "util_func", ["lambda", ["a"], ["*", "a", 10]]]]
        mod_callee_path = self._create_temp_file("mod_callee", mod_callee_content)

        mod_caller_content = [["def", "call_util", ["lambda", ["b"], [["get", "utils", "@util_func"], "b"]]]]
        mod_caller_path = self._create_temp_file("mod_caller", mod_caller_content)

        main_prog_content_v3 = {
            "entrypoint": [["get", "caller", "@call_util"], 7]
        }
        main_prog_path_v3 = self._create_temp_file("main_nested_v3", main_prog_content_v3)
        
        cli_bindings_v3 = {
            "utils": mod_callee_path,
            "caller": mod_caller_path
        }
        # When mod_caller is loaded, its `load_module` gets `prelude` as parent.
        # The lambda for `call_util` captures an env parented by prelude.
        # When `run_with_imports` runs main, `utils` and `caller` are in `env_for_main_program`.
        # The `call_util` closure, when called, will execute in an env:
        #   `captured_env_of_call_util.extend({"b": 7})`
        # `captured_env_of_call_util` is `module_env_of_caller`.
        # `module_env_of_caller.lookup("utils")` should find the `utils` module object.
        result = run_with_imports(main_prog_path_v3, cli_allowed_imports=[], cli_bindings=cli_bindings_v3)
        self.assertEqual(result, 70)


    def test_module_exports_and_uses_closure(self):
        """Test a module exporting a closure that captures its module's internal state."""
        mod_closure_content = [
            ["def", "factor", 5],
            ["def", "multiplier", ["lambda", ["x"], ["*", "x", "factor"]]] # Captures 'factor'
        ]
        mod_closure_path = self._create_temp_file("mod_closure_export", mod_closure_content)

        main_prog_content = {
            "entrypoint": [["get", "m", "@multiplier"], 10]
        }
        main_prog_path = self._create_temp_file("main_use_mod_closure", main_prog_content)
        cli_bindings = {"m": mod_closure_path}

        result = run_with_imports(main_prog_path, cli_allowed_imports=[], cli_bindings=cli_bindings)
        self.assertEqual(result, 50) # 10 * 5

    def test_serialization_deserialization_simple_closure(self):
        """Test to_json and from_json for a simple closure."""
        self.env["captured_val"] = 100
        jsl_lambda_expr = ["lambda", ["x"], ["+", "x", "captured_val"]]
        
        closure_obj = eval_expr(jsl_lambda_expr, self.env)
        self.assertIsInstance(closure_obj, Closure)

        serialized_closure = to_json(closure_obj)
        # print("\nSerialized Closure:", json.dumps(serialized_closure, indent=2))

        # Ensure basic structure
        self.assertEqual(serialized_closure.get("type"), "closure")
        self.assertEqual(serialized_closure.get("params"), ["x"])
        self.assertIsNotNone(serialized_closure.get("body"))
        self.assertIsNotNone(serialized_closure.get("env"))
        self.assertIn("captured_val", json.dumps(serialized_closure["env"])) # Check if captured_val is in env dump

        # For from_json to work, the global prelude must be set.
        jsl.prelude = self.prelude # Ensure from_json can access the current prelude
        
        # The from_json in jsl.py is a stub, this test will likely fail or need from_json to be implemented.
        # Assuming from_json is implemented:
        try:
            deserialized_closure = from_json(serialized_closure, self.prelude)
        except Exception as e:
            self.fail(f"from_json failed during deserialization: {e}")

        self.assertIsInstance(deserialized_closure, Closure)
        self.assertEqual(deserialized_closure.params, ["x"])
        
        # Test the deserialized closure's functionality
        # It needs an environment to run, eval_expr provides it.
        # The deserialized_closure.env should be correctly reconstructed.
        # We'll call it using eval_expr with a new top-level env for the call.
        
        # Create a new environment for calling the deserialized closure
        call_env = Env(parent=self.prelude) # Fresh env, prelude is parent
        call_env["my_deserialized_func"] = deserialized_closure
        
        result = eval_expr(["my_deserialized_func", 20], call_env)
        self.assertEqual(result, 120) # 20 + 100 (captured_val)

    def test_module_evaluation_error(self):
        """Test error handling when a module itself has an error during evaluation."""
        mod_error_content = [
            ["def", "a", 10],
            ["def", "b", ["/", "a", 0]] # Division by zero error
        ]
        mod_error_path = self._create_temp_file("mod_with_error", mod_error_content)

        main_prog_content = {"entrypoint": ["@wont_run"]}
        main_prog_path = self._create_temp_file("main_error_mod", main_prog_content)
        cli_bindings = {"bad_mod": mod_error_path}

        # The error should propagate from load_module up through run_with_imports
        with self.assertRaisesRegex(RuntimeError, r"Failed to load module 'bad_mod' from '.*mod_with_error.*\.json':.*division by zero"):
            run_with_imports(main_prog_path, cli_allowed_imports=[], cli_bindings=cli_bindings)

    def test_module_imports_module_that_fails_to_load(self):
        """
        Test scenario where main imports ModA, and ModA tries to use ModB,
        but ModB is not bound or fails to load.
        This tests how errors within a module's own logic (like a failed 'get' for another module) are handled.
        """
        mod_a_content = [
            ["def", "try_get_b", ["lambda", [], ["get", "modB", "@some_val"]]]
            # This lambda, when called, will try to access 'modB'
        ]
        mod_a_path = self._create_temp_file("mod_a_needs_b", mod_a_content)

        main_prog_content = {
            "entrypoint": [["get", "modA", "@try_get_b"]] # Call the function from modA
        }
        main_prog_path = self._create_temp_file("main_imports_needy_a", main_prog_content)

        # Scenario 1: modB is not bound at all
        cli_bindings_no_b = {"modA": mod_a_path}
        with self.assertRaisesRegex(NameError, r"Unbound symbol: modB"):
            run_with_imports(main_prog_path, cli_allowed_imports=[], cli_bindings=cli_bindings_no_b)

        # Scenario 2: modB is bound but points to a non-existent file
        cli_bindings_b_not_found = {
            "modA": mod_a_path,
            "modB": "path/to/nonexistent_mod_b.json"
        }
        # This error occurs when run_with_imports tries to load modB
        with self.assertRaisesRegex(RuntimeError, r"Failed to load module 'modB' from 'path/to/nonexistent_mod_b.json': Module file not found"):
            run_with_imports(main_prog_path, cli_allowed_imports=[], cli_bindings=cli_bindings_b_not_found)

if __name__ == '__main__':
    unittest.main()

