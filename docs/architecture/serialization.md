# Code and Data Serialization

> For a conceptual overview of JSL environments and the operations you can perform on them, see the [Environments language guide](../language/environments.md).

## Overview

Serialization is fundamental to JSL's design philosophy. Since JSL code is JSON, any JSL program is already in a transmittable format. However, to capture the full, executable state of a program—including functions with captured lexical environments (closures)—JSL defines a canonical serialization payload.

This structure enables true code mobility, persistence, and robust distributed computing patterns.

## The Serialized State Payload

When a JSL state is serialized, the payload includes three key parts. This is the standard, canonical format for all JSL state serialization.

1.  **`prelude_hash`**: A hash representing the version of the core prelude functions the code depends on. This allows a receiving system to verify runtime compatibility.
2.  **`environments`**: A key-value map where each key is the content-hash of an environment, and the value is the environment object itself. This is the "environment store."
3.  **`result`**: The final value of the computation. If it's a closure, it will reference an environment by its hash.

### The Environment Object and Hashing

An **Environment Object** is the serializable representation of a scope. It has a simple, immutable structure:
- `bindings`: A JSON object mapping local variable names to their values.
- `parent`: The hash of the parent environment, or `null` for the global scope. A `null` parent indicates the end of the user-defined scope chain; the evaluator will then fall back to the system prelude for lookups.

The hash of an environment is calculated over its entire content, including the hash of its parent. This creates a **recursive hash chain** which guarantees that an environment's hash uniquely and securely identifies its entire lexical ancestry.

### Serialization Walkthrough

Consider this nested closure example:
```json
["do",
  ["def", "base", 100],
  ["def", "make_adder",
    ["lambda", ["increment"],
      ["lambda", ["x"], ["+", "x", "increment", "base"]]]],
  ["def", "add_5", ["make_adder", 5]],
  "add_5"
]
```

When evaluated, this produces a final closure (`add_5`). The complete, serialized state payload would look like this:
```json
{
  "prelude_hash": "PRELUDE_HASH_XYZ",
  "result": {
    "type": "closure",
    "params": ["x"],
    "body": ["+", "x", "increment", "base"],
    "env_hash": "H1"
  },
  "environments": {
    "H0": {
      "bindings": { "base": 100 },
      "parent": null
    },
    "H1": {
      "bindings": { "increment": 5 },
      "parent": "H0"
    }
  }
}
```
This content-addressable model is highly efficient, avoids data duplication, and correctly represents shared and nested environments in a purely serializable way.

## Serialization Patterns

The following patterns demonstrate how the canonical serialized state payload can be used.

### Network Transmission

The payload can be sent directly as the body of an HTTP request to a remote JSL node for execution.

```http
POST /execute HTTP/1.1
Content-Type: application/json
X-JSL-Prelude-Hash: PRELUDE_HASH_XYZ

{
  "result": {
    "type": "closure",
    "params": ["x"],
    "body": ["+", "x", "increment", "base"],
    "env_hash": "H1"
  },
  "environments": {
    "H0": { "bindings": { "base": 100 }, "parent": null },
    "H1": { "bindings": { "increment": 5 }, "parent": "H0" }
  }
}
```

### Code Storage

The entire payload can be stored in a database (e.g., in a JSONB column) to persist a function, a user's workflow state, or a configuration template.

```sql
INSERT INTO jsl_functions (name, payload) VALUES (
  'add_five_function',
  '{
    "prelude_hash": "PRELUDE_HASH_XYZ",
    "result": {
      "type": "closure",
      "params": ["x"],
      "body": ["+", "x", "increment", "base"],
      "env_hash": "H1"
    },
    "environments": {
      "H0": { "bindings": { "base": 100 }, "parent": null },
      "H1": { "bindings": { "increment": 5 }, "parent": "H0" }
    }
  }'::JSONB
);
```

### Object Serialization

JSON objects with embedded code serialize cleanly:

```json
{
  "response_object": {
    "@status": "@success",
    "@user": "username",
    "@computed_score": ["*", "base_score", "multiplier"],
    "@timestamp": ["host", "time/now"]
  }
}
```

When evaluated, this produces a pure JSON object with all expressions resolved.

## Conclusion

JSL's serialization model is designed for simplicity, efficiency, and portability. By leveraging JSON as the underlying format, JSL ensures that code can be easily transmitted, stored, and executed across different environments without loss of fidelity or context.
