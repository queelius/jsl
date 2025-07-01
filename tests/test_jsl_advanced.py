import unittest
import json
import os
import tempfile
from unittest.mock import patch
from typing import Any

# Assuming 'jsl' is a package in PYTHONPATH or structured for such imports
from jsl.core import Env, Closure
from jsl.prelude import make_prelude
from jsl import run_program, dumps, loads, eval_expr
from jsl.modules import load_module

class TestJSLAdvanced(unittest.TestCase):

    def setUp(self):
        """Set up a fresh prelude and environment for each test."""
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

    def test_closure_serialization_deserialization(self):
        """Test that a closure can be serialized and then deserialized correctly."""
        # Define a closure that captures a variable from its environment
        self.env["captured_var"] = 10
        closure_expr = ["lambda", ["x"], ["+", "x", "captured_var"]]
        closure = eval_expr(closure_expr, self.env)

        # Serialize the closure
        serialized_closure = dumps(closure, indent=4)
        self.assertIn("captured_var", serialized_closure)
        self.assertIn("__closure_env__", serialized_closure)

        # This is the crucial part: the deserialized closure must be able to find
        # the prelude functions (like '+') to be executable.
        # The from_json function needs access to a prelude environment.
        deserialized_closure = loads(serialized_closure)
        self.assertIsInstance(deserialized_closure, Closure)

        # Create a new environment to run the deserialized closure
        run_env = Env(parent=self.prelude)
        run_env["reloaded_func"] = deserialized_closure

        # Execute the deserialized closure
        result = eval_expr(["reloaded_func", 5], run_env)
        self.assertEqual(result.value, 15)

