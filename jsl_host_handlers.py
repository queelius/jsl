import json
import os

def process_host_request(request_message: list) -> any:
    """
    Processes a JHIP request message and returns a JHIP response.
    """
    if not (isinstance(request_message, list) and
            len(request_message) >= 2 and
            request_message[0] == "host"):
        return {
            "$jsl_host_error": {
                "type": "InvalidRequestFormat",
                "message": "Request does not conform to JHIP structure.",
                "details": {"request_preview": str(request_message)[:100]}
            }
        }

    command_id = request_message[1]
    args = request_message[2:]

    # --- Dispatch to specific command handlers ---
    if command_id == "file/write-string":
        return handle_file_write_string(args)
    elif command_id == "util/timestamp-iso":
        import datetime
        return {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    elif command_id == "util/random-uuid":
        import uuid
        return {"uuid": str(uuid.uuid4())}
    elif command_id == "util/random-int":
        import random
        if len(args) != 2 or not all(isinstance(x, int) for x in args):
            return {
                "$jsl_host_error": {
                    "type": "InvalidArgumentCount",
                    "message": "'util/random-int' expects 2 integer arguments: min and max.",
                    "details": {"expected": 2, "received": len(args)}
                }
            }
        return {"random_int": random.randint(args[0], args[1])}
    else:
        return {
            "$jsl_host_error": {
                "type": "CommandNotFound",
                "message": f"Host command '{command_id}' is not recognized.",
                "details": {"command_id": command_id}
            }
        }

def handle_file_write_string(args: list) -> any:
    """
    Handles the 'file/write-string' JHIP command.
    Expected args: [filepath_str, content_str]
    """
    if len(args) != 2:
        return {
            "$jsl_host_error": {
                "type": "InvalidArgumentCount",
                "message": "'file/write-string' expects 2 arguments: filepath and content.",
                "details": {"expected": 2, "received": len(args)}
            }
        }

    filepath = args[0]
    content = args[1]

    if not isinstance(filepath, str):
        return {
            "$jsl_host_error": {
                "type": "InvalidArgumentType",
                "message": "Filepath argument for 'file/write-string' must be a string.",
                "details": {"argument_index": 0, "expected_type": "string", "received_type": type(filepath).__name__}
            }
        }
    if not isinstance(content, str):
        return {
            "$jsl_host_error": {
                "type": "InvalidArgumentType",
                "message": "Content argument for 'file/write-string' must be a string.",
                "details": {"argument_index": 1, "expected_type": "string", "received_type": type(content).__name__}
            }
        }

    try:
        # Basic security: prevent writing outside /tmp for this example
        # A real implementation would have more robust path validation and security.
        if not os.path.abspath(filepath).startswith(os.path.abspath("/tmp/")):
             return {
                "$jsl_host_error": {
                    "type": "PermissionDenied",
                    "message": "File path is outside the allowed directory (/tmp).",
                    "details": {"filepath": filepath}
                }
            }

        with open(filepath, 'w', encoding='utf-8') as f:
            bytes_written = f.write(content)
        
        # Success response
        return {
            "status": "success",
            "path": filepath,
            "bytes_written": bytes_written
        }
    except PermissionError:
        return {
            "$jsl_host_error": {
                "type": "PermissionDenied",
                "message": f"Host denied write access to '{filepath}'.",
                "details": {"path": filepath}
            }
        }
    except IOError as e:
        return {
            "$jsl_host_error": {
                "type": "IOError",
                "message": f"An I/O error occurred while writing to '{filepath}': {e}",
                "details": {"path": filepath, "error_details": str(e)}
            }
        }
    except Exception as e: # Catch-all for other unexpected errors
        return {
            "$jsl_host_error": {
                "type": "UnhandledHostError",
                "message": f"An unexpected error occurred on the host: {e}",
                "details": {"command_id": "file/write-string"}
            }
        }

