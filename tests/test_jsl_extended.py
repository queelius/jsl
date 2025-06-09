import unittest
import json
import os
import datetime # For timestamp tests
import uuid # For UUID tests
from unittest.mock import patch


# Assuming your project structure allows this import path
# If 'jsl' is a package in your PYTHONPATH:
from jsl import jsl
from jsl.jsl import (
    eval_expr,
    Env,
    Closure,
    make_prelude,
    to_json,
    run_program,
    load_module
)
from jsl import jsl_host_dispatcher # Import the dispatcher

# Mock for process_host_request that will be used by the main JSL evaluator
# when testing the JSL 'host' special form.
# This mock will, in turn, call the actual jsl_host_dispatcher.process_host_request
def mock_dispatch_to_actual_host_processor(request_message):
    return jsl_host_dispatcher.process_host_request(request_message)

class TestJSLExtended(unittest.TestCase):

    def setUp(self):
        jsl.prelude = None # Reset global prelude
        self.prelude = make_prelude()
        self.env = Env(parent=self.prelude)

    def eval(self, expr_str):
        expr = json.loads(expr_str)
        return eval_expr(expr, self.env)

    # --- Tests for jsl_host_dispatcher.py ---

    def test_host_dispatcher_invalid_request_format(self):
        response = jsl_host_dispatcher.process_host_request("not-a-list")
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "InvalidRequestFormat")

        response = jsl_host_dispatcher.process_host_request(["not-host", "cmd"])
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "InvalidRequestFormat")
        
        response = jsl_host_dispatcher.process_host_request(["host"]) # Too short
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "InvalidRequestFormat")


    def test_host_dispatcher_command_not_found(self):
        response = jsl_host_dispatcher.process_host_request(["host", "nonexistent/command"])
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "CommandNotFound")
        self.assertEqual(response["$jsl_host_error"]["details"]["command_id"], "nonexistent/command")

    def test_host_dispatcher_file_write_string_success(self):
        test_filepath = "/tmp/jsl_test_file_write.txt"
        test_content = "Hello from JSL host dispatcher!"
        
        request = ["host", "file/write-string", test_filepath, test_content]
        response = jsl_host_dispatcher.process_host_request(request)
        
        self.assertNotIn("$jsl_host_error", response, f"Host error: {response.get('$jsl_host_error')}")
        self.assertEqual(response.get("status"), "success")
        self.assertEqual(response.get("path"), test_filepath)
        self.assertEqual(response.get("bytes_written"), len(test_content))
        
        with open(test_filepath, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, test_content)
        
        os.remove(test_filepath) # Clean up

    def test_host_dispatcher_file_write_string_errors(self):
        # Invalid arg count
        response = jsl_host_dispatcher.process_host_request(["host", "file/write-string", "/tmp/test.txt"])
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "InvalidArgumentCount")

        # Invalid filepath type
        response = jsl_host_dispatcher.process_host_request(["host", "file/write-string", 123, "content"])
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "InvalidArgumentType")
        self.assertEqual(response["$jsl_host_error"]["details"]["argument_index"], 0)

        # Invalid content type
        response = jsl_host_dispatcher.process_host_request(["host", "file/write-string", "/tmp/test.txt", True])
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "InvalidArgumentType")
        self.assertEqual(response["$jsl_host_error"]["details"]["argument_index"], 1)

        # Path outside /tmp
        response = jsl_host_dispatcher.process_host_request(["host", "file/write-string", "/etc/passwd", "hacked"])
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "PermissionDenied")
        self.assertIn("outside the allowed directory", response["$jsl_host_error"]["message"])

    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_host_dispatcher_file_write_string_io_error(self, mock_open):
        request = ["host", "file/write-string", "/tmp/io_error_test.txt", "content"]
        response = jsl_host_dispatcher.process_host_request(request)
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "IOError")
        self.assertIn("Disk full", response["$jsl_host_error"]["message"])

    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    def test_host_dispatcher_file_write_string_permission_error_on_open(self, mock_open):
        request = ["host", "file/write-string", "/tmp/permission_test.txt", "content"]
        response = jsl_host_dispatcher.process_host_request(request)
        self.assertIn("$jsl_host_error", response)
        self.assertEqual(response["$jsl_host_error"]["type"], "PermissionDenied")
        # Update the assertion to match the actual error message format
        self.assertIn("Host denied write access to", response["$jsl_host_error"]["message"])
        self.assertIn("/tmp/permission_test.txt", response["$jsl_host_error"]["message"])


    def test_host_dispatcher_util_timestamp_iso(self):
        response = jsl_host_dispatcher.process_host_request(["host", "util/timestamp-iso"])
        self.assertNotIn("$jsl_host_error", response)
        self.assertIn("timestamp", response)
        try:
            datetime.datetime.fromisoformat(response["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            self.fail("Timestamp is not in valid ISO format")

    def test_host_dispatcher_util_random_uuid(self):
        response = jsl_host_dispatcher.process_host_request(["host", "util/random-uuid"])
        self.assertNotIn("$jsl_host_error", response)
        self.assertIn("uuid", response)
        try:
            uuid.UUID(response["uuid"])
        except ValueError:
            self.fail("UUID is not valid")

    def test_host_dispatcher_util_random_int(self):
        response = jsl_host_dispatcher.process_host_request(["host", "util/random-int", 1, 10])
        self.assertNotIn("$jsl_host_error", response)
        self.assertIn("random_int", response)
        self.assertTrue(1 <= response["random_int"] <= 10)

        # Error cases
        response_err_args = jsl_host_dispatcher.process_host_request(["host", "util/random-int", 1])
        self.assertIn("$jsl_host_error", response_err_args)
        self.assertEqual(response_err_args["$jsl_host_error"]["type"], "InvalidArgumentCount")
        
        response_err_type = jsl_host_dispatcher.process_host_request(["host", "util/random-int", 1, "10"])
        self.assertIn("$jsl_host_error", response_err_type)
        self.assertEqual(response_err_type["$jsl_host_error"]["type"], "InvalidArgumentCount") # Current dispatcher check is len + all int

    # --- Tests for JSL 'host' special form using the actual dispatcher ---
    @patch('jsl.jsl.process_host_request', side_effect=mock_dispatch_to_actual_host_processor)
    def test_jsl_host_form_with_actual_dispatcher_success(self, mock_dispatch_fn):
        # Test util/timestamp-iso through JSL 'host'
        result_ts = self.eval('["host", "@util/timestamp-iso"]')
        self.assertIn("timestamp", result_ts)
        mock_dispatch_fn.assert_called_with(["host", "util/timestamp-iso"])

        # Test file/write-string through JSL 'host'
        test_filepath = "/tmp/jsl_eval_host_write.txt"
        test_content = "Written via JSL eval -> host"
        
        # Construct the JSL arguments which are JSL string literals.
        # For example, if test_filepath is "/foo/bar", the JSL string literal is "@foo/bar".
        # In the JSON representation of the JSL program, this becomes the JSON string "\"@/foo/bar\"".
        jsl_arg_filepath = f"@{test_filepath}"
        jsl_arg_content = f"@{test_content}"

        # Now construct the JSON string for the JSL program
        jsl_program = f'["host", "@file/write-string", "{jsl_arg_filepath}", "{jsl_arg_content}"]'
        
        result_write = self.eval(jsl_program)
        
        self.assertNotIn("$jsl_host_error", result_write, f"Host error: {result_write.get('$jsl_host_error')}")
        self.assertEqual(result_write.get("status"), "success")
        mock_dispatch_fn.assert_called_with(["host", "file/write-string", test_filepath, test_content])
        
        if os.path.exists(test_filepath): # Clean up if file was created
            os.remove(test_filepath)


    @patch('jsl.jsl.process_host_request', side_effect=mock_dispatch_to_actual_host_processor)
    def test_jsl_host_form_with_actual_dispatcher_error(self, mock_dispatch_fn):
        # Test command not found through JSL 'host'
        with self.assertRaisesRegex(RuntimeError, r"Host error \(CommandNotFound\): Host command 'bad/command' is not recognized."):
            self.eval('["host", "@bad/command"]')
        mock_dispatch_fn.assert_called_with(["host", "bad/command"])

        # Test file/write-string error (path outside /tmp) through JSL 'host'
        with self.assertRaisesRegex(RuntimeError, r"Host error \(PermissionDenied\): File path is outside the allowed directory \(/tmp\)."):
            self.eval('["host", "@file/write-string", "@/etc/hosts", "@content"]')
        mock_dispatch_fn.assert_called_with(["host", "file/write-string", "/etc/hosts", "content"])

    def test_to_json_deeply_nested_and_circular_data(self):
        # Setup complex structure
        data = {"a": 1, "b": [10, 20]}
        data["c"] = data # Circular reference
        data["b"].append(data) # Another circular reference

        serialized = to_json(data)
        
        # Check basic structure and presence of $ref for circularity
        self.assertEqual(serialized["a"], 1)
        self.assertIsInstance(serialized["b"], list)
        self.assertEqual(serialized["b"][0], 10)
        self.assertEqual(serialized["b"][1], 20)
        
        # Check for circular references marked by $ref
        # id(data) would be the original object's ID
        # The exact $ref value depends on id() which is not stable across runs for new objects.
        # We check that 'c' and the third element of 'b' are dicts with a '$ref' key.
        self.assertIsInstance(serialized["c"], dict)
        self.assertIn("$ref", serialized["c"])
        
        self.assertIsInstance(serialized["b"][2], dict)
        self.assertIn("$ref", serialized["b"][2])
        
        # Ensure the $ref points back to the main object's $ref ID if it has one
        # (to_json adds $ref to dicts/lists it has seen)
        if "$ref" in serialized: # The top-level 'data' dict itself will get a $ref
             self.assertEqual(serialized["c"]["$ref"], serialized["$ref"])
             self.assertEqual(serialized["b"][2]["$ref"], serialized["$ref"])


if __name__ == '__main__':
    unittest.main()