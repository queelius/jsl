# Code and Data Serialization

> For a conceptual overview of JSL environments and the operations you can perform on them, see the [Environments language guide](../language/environments.md).

## Overview

Serialization is fundamental to JSL's design philosophy. Since JSL code is JSON, any JSL program is already in a transmittable format. However, to capture the full, executable state of a program—including functions with captured lexical environments (closures)—JSL uses a content-addressable serialization format.

This structure enables true code mobility, persistence, and robust distributed computing patterns while handling circular references elegantly.

## Content-Addressable Serialization Format

JSL uses a content-addressable serialization format where each unique object gets a deterministic hash based on its content. When a JSL value is serialized, the payload includes three key parts:

1.  **`__cas_version__`**: Version number of the content-addressable serialization format (currently 1).
2.  **`objects`**: A key-value map where each key is the content-hash of a complex object (closure or environment), and the value is the object itself. This is the "object store."
3.  **`root`**: The root value of the serialization. If it's a complex object, it will reference an object by its hash using `{"__ref__": "hash"}`.

### Complex Object Structure

**Environment Objects** represent scopes and have the structure:
- `__type__`: Always `"env"` to identify the object type
- `bindings`: A JSON object mapping variable names to their values (which may include references to other objects)

**Closure Objects** represent functions and have the structure:
- `__type__`: Always `"closure"` to identify the object type  
- `params`: List of parameter names
- `body`: The function body as a JSL expression
- `env`: Reference to the captured environment (may be `{"__ref__": "hash"}`)

The hash of each object is calculated over its content, creating a stable identifier. Objects that reference each other use the `{"__ref__": "hash"}` format, which allows the deserializer to reconstruct the object graph correctly.

### Serialization Walkthrough

Consider this simple closure example:
```json
["do",
  ["def", "base", 100],
  ["lambda", ["x"], ["+", "x", "base"]]
]
```

When evaluated, this produces a closure that captures the `base` variable. The serialized payload might look like this:
```json
{
  "__cas_version__": 1,
  "root": {"__ref__": "a1b2c3d4e5f6g7h8"},
  "objects": {
    "a1b2c3d4e5f6g7h8": {
      "__type__": "closure",
      "params": ["x"],
      "body": ["+", "x", "base"],
      "env": {"__ref__": "h8g7f6e5d4c3b2a1"}
    },
    "h8g7f6e5d4c3b2a1": {
      "__type__": "env",
      "bindings": {
        "base": 100
      }
    }
  }
}
```

For primitive values (numbers, strings, booleans, simple arrays/objects), the serialization is direct JSON without the CAS wrapper:
```json
// Simple values serialize directly
42              → "42"
[1, 2, 3]      → "[1,2,3]"
{"key": "val"} → "{\"key\":\"val\"}"
```

This content-addressable model efficiently handles circular references, avoids data duplication, and correctly represents complex object relationships in a purely serializable way.

## Serialization Patterns

The following patterns demonstrate how the canonical serialized state payload can be used.

### Network Transmission

The serialized payload can be sent directly as the body of an HTTP request to a remote JSL node for execution.

```http
POST /execute HTTP/1.1
Content-Type: application/json

{
  "__cas_version__": 1,
  "root": {"__ref__": "a1b2c3d4e5f6g7h8"},
  "objects": {
    "a1b2c3d4e5f6g7h8": {
      "__type__": "closure",
      "params": ["x"],
      "body": ["+", "x", "base"],
      "env": {"__ref__": "h8g7f6e5d4c3b2a1"}
    },
    "h8g7f6e5d4c3b2a1": {
      "__type__": "env",
      "bindings": {"base": 100}
    }
  }
}
```

### Code Storage

The entire payload can be stored in a database (e.g., in a JSONB column) to persist a function, a user's workflow state, or a configuration template.

```sql
INSERT INTO jsl_functions (name, payload) VALUES (
  'increment_function',
  '{
    "__cas_version__": 1,
    "root": {"__ref__": "a1b2c3d4e5f6g7h8"},
    "objects": {
      "a1b2c3d4e5f6g7h8": {
        "__type__": "closure",
        "params": ["x"],
        "body": ["+", "x", "base"],
        "env": {"__ref__": "h8g7f6e5d4c3b2a1"}
      },
      "h8g7f6e5d4c3b2a1": {
        "__type__": "env",
        "bindings": {"base": 100}
      }
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
