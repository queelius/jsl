# JSL Host Interaction Protocol (JHIP) - Version 1.0

## Introduction

The JSL Host Interaction Protocol (JHIP) defines a standardized, JSON-based
message-passing interface for JSL (JSON Serializable Language) programs to
request and interact with side-effecting operations performed by a host
environment. This protocol enables JSL's core philosophy of reifying effects
as data, allowing for secure, auditable, and portable interactions with
the external world.

## Core Principles

- Request-Response Model: JSL initiates a request; the host provides a response.
- JSON Serialization: All request and response messages MUST be valid JSON.
- Synchronous Interaction (from JSL's perspective): A `["host", ...]`
    expression in JSL blocks until the host system returns a response.
    The underlying transport may be asynchronous, but the JSL evaluation
    awaits the result.
- Stateless Commands (Recommended): Individual host commands should ideally
    be stateless, though the host system itself may maintain state.
- Host Authority: The host system is the ultimate authority on whether a
    command is permitted and how it is executed.

## Message Schemas

### Request Message (JSL -> Host)

A JSL `["host", ...]` expression is transformed into a JSON Array
representing the request.

Schema:

```json
[
    "host",                // Element 0: Literal string "host" (Protocol Identifier)
    "<command_id>",        // Element 1: String (Host-defined command identifier)
    <arg1>,                // Element 2 (optional): JSON-serializable value
    <arg2>,                // Element 3 (optional): JSON-serializable value
    ...                    // Additional arguments
]
```

Details:

- Protocol Identifier: The first element MUST be the string "host".
- command_id: A non-empty string uniquely identifying the desired host
    operation (e.g., "file/read", "http/post", "log/info"). The host
    defines the available command_ids.
- Arguments: Zero or more JSON-serializable values. These are the
    evaluated results of the argument expressions provided in the JSL
    `["host", ...]` form. The JSL interpreter ensures these are fully
    evaluated before constructing the request.

Example Request:

When we evaluate the JSL program:

```json
["host", "@file/write-string", "@/tmp/output.txt", "@Hello from JSL!"]

It is transformed into the following JSON request message:

```json
["host", "file/write-string", "/tmp/output.txt", "Hello from JSL!"]
```

### Response Message (Host -> JSL)

The host system processes the request and MUST return a single,
JSON-serializable value. This value becomes the result of the
`["host", ...]` expression in the JSL program.

Two categories of responses exist: Success and Error.

#### Success Response

Any valid JSON value that is NOT a JHIP Error Response Object (see 3.2.2).
The specific structure of a success response is defined by the host
for each `command_id`.

Examples:

- `null` (for operations with no meaningful return value, like logging)
- "File content as a string"
- 42
- true
- ["item1", "item2"]
- {"id": 123, "status": "created"}

#### Error Response Object

To clearly distinguish host-level operational errors from successful
results that might be `null`, `false`, or other potentially ambiguous
values, errors are returned as a specific JSON Object.

Schema:

```json
{
    "$jsl_host_error": {    // Top-level key indicating a JHIP error
    "type": "<ErrorType>", // String (Required): Host-defined error category
    "message": "<String>", // String (Required): Human-readable error message
    "details": { ... }     // Object (Optional): Additional structured error info
    }
}
```

Details:

- `$jsl_host_error`: The presence of this top-level key signifies
    a JHIP error response.
- `type`: A string categorizing the error (e.g., "FileSystemError",
    "NetworkError", "PermissionDenied", "InvalidArgument",
    "CommandNotFound").
- `message`: A clear, human-readable description of the error.
- `details`: An optional object providing more specific, structured
    information relevant to the error (e.g., file path, error codes,
    expected vs. actual values).

Example Error Response:

```json
{
    "$jsl_host_error": {
    "type": "PermissionDenied",
    "message": "Host denied write access to the specified path.",
    "details": {
        "path": "/etc/important_file.txt",
        "requested_operation": "file/write-string"
    }
    }
}
```

## Protocol Flow Summary

1. JSL Interpreter encounters `["host", cmd_id_expr, arg1_expr, ...]`.
2. JSL Interpreter evaluates `cmd_id_expr` and all `argN_expr` to obtain
    `command_id` (string) and `arg_values`.
3. JSL Interpreter constructs the JSON Request Message:
    `["host", command_id, ...arg_values]`.
4. JSL Runtime transmits this Request Message to the Host System Handler.
5. Host System Handler:
    a. Parses the Request Message.
    b. Validates `command_id` and arguments.
    c. Attempts to perform the operation.
    d. Constructs a JSON Response Message (Success value or Error Object).
6. Host System Handler transmits the Response Message back to the JSL Runtime.
7. JSL Runtime:
    a. Parses the Response Message.
    b. If it's an Error Response Object, the JSL `["host", ...]` expression
        might result in a JSL-level error (e.g., by evaluating `["error", ...]`).
        (The exact behavior of JSL error handling for host errors is an
        implementation detail of the JSL runtime/runner).
    c. If it's a Success Response, this value becomes the result of the
        `["host", ...]` expression.

## Versioning

This document describes JHIP v1.0. Future versions may introduce changes
but should strive for backward compatibility where feasible or provide clear
migration paths.