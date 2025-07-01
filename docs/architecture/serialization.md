# Code and Data Serialization

> For Python API usage examples, see [API Reference: Serialization](../api/serialization.md).

## Overview

Serialization is fundamental to JSL's design philosophy. Since JSL code is JSON, serialization becomes trivial - every JSL program is already in a serialized, transmittable format. This enables powerful patterns for code mobility, persistence, and distributed computing.

## JSON as Universal Format

### Code Serialization

JSL functions serialize naturally as JSON arrays:

```json
// Function definition
["lambda", ["x", "y"], ["+", ["*", "x", "x"], ["*", "y", "y"]]]

// This is already serialized! Can be:
// - Transmitted over HTTP
// - Stored in databases  
// - Cached in files
// - Embedded in other JSON
```

### Data Serialization

All JSL data structures are JSON-compatible:

```json
{
  "users": [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
  ],
  "metadata": {
    "created": "2023-12-01",
    "version": "1.0"
  }
}
```

## Closure Serialization

### Environment Capture

JSL closures capture their lexical environment for serialization:

```json
// Original code with environment
["do",
  ["def", "multiplier", 10],
  ["def", "scale", ["lambda", ["x"], ["*", "x", "multiplier"]]],
  "scale"]

// Serialized closure with captured environment
{
  "type": "closure",
  "params": ["x"],
  "body": ["*", "x", "multiplier"],
  "env": {"multiplier": 10}
}
```

### Nested Closures

Complex nested environments are preserved:

```json
// Nested closure example
["do",
  ["def", "base", 100],
  ["def", "make_adder", 
    ["lambda", ["increment"],
      ["lambda", ["x"], ["+", ["+", "x", "increment"], "base"]]]],
  ["make_adder", 5]]

// Serialized nested closure
{
  "type": "closure",
  "params": ["x"],
  "body": ["+", ["+", "x", "increment"], "base"],
  "env": {
    "increment": 5,
    "base": 100
  }
}
```

## Serialization Patterns

### Code Transmission

```json
// Send function to remote system
{
  "action": "execute",
  "code": ["map", ["lambda", ["x"], ["*", "x", 2]], [1, 2, 3, 4]],
  "context": {}
}

// Remote system can execute directly
// Result: [2, 4, 6, 8]
```

### Code Storage

```json
// Store JSL functions in database
{
  "function_library": {
    "math": {
      "square": ["lambda", ["x"], ["*", "x", "x"]],
      "factorial": ["lambda", ["n"], 
        ["if", ["<=", "n", 1], 1, 
         ["*", "n", ["factorial", ["-", "n", 1]]]]]
    },
    "strings": {
      "reverse": ["lambda", ["s"], ["host", "string/reverse", "s"]],
      "upper": ["lambda", ["s"], ["host", "string/upper", "s"]]
    }
  }
}
```

### Template Serialization

Templates with embedded code serialize cleanly:

```json
{
  "response_template": {
    "status": "success",
    "user": "@username",
    "computed_score": ["$eval", ["*", "@base_score", "@multiplier"]],
    "timestamp": ["$eval", ["host", "time/now"]]
  }
}
```

## Advanced Serialization

### Partial Application

```json
// Partially applied function
["def", "add_ten", ["partial", "+", 10]]

// Serializes as:
{
  "type": "partial",
  "function": "+",
  "args": [10],
  "remaining_arity": 1
}
```

### Recursive Functions

```json
// Self-referential functions serialize with special handling
["def", "fibonacci", 
  ["lambda", ["n"],
    ["if", ["<", "n", 2],
      "n",
      ["+", ["fibonacci", ["-", "n", 1]], 
           ["fibonacci", ["-", "n", 2]]]]]]

// Serialized with recursive reference
{
  "type": "recursive_closure",
  "name": "fibonacci",
  "params": ["n"],
  "body": ["if", ["<", "n", 2], "n", 
           ["+", ["@self", ["-", "n", 1]], 
                ["@self", ["-", "n", 2]]]],
  "env": {}
}
```

## Serialization APIs

### Manual Serialization

```json
// Serialize any JSL value
["host", "serialize", some_value]
// Returns JSON string representation

// Deserialize JSON back to JSL
["host", "deserialize", json_string]
// Returns original JSL value
```

### Automatic Serialization

```json
// JSL runtime handles serialization automatically for:
// - Function transmission
// - Data persistence  
// - Network communication
// - Template processing
```

## Performance Considerations

### Serialization Cost

- **Functions**: O(1) - already JSON
- **Closures**: O(e) where e = environment size
- **Data**: O(n) where n = data size
- **Templates**: O(t) where t = template complexity

### Optimization Strategies

```json
// Lazy serialization - serialize only when needed
["def", "heavy_function", 
  ["lambda", ["data"], 
    ["map", "expensive_operation", "data"]]]

// Environment pruning - capture only needed variables
["lambda", ["x"], 
  ["let", [["needed", "some_variable"]], 
    ["+", "x", "needed"]]]
```

## Network Serialization

### HTTP Transport

```http
POST /execute HTTP/1.1
Content-Type: application/json

{
  "code": ["do",
    ["def", "data", ["host", "file/read", "input.json"]],
    ["map", ["lambda", ["item"], ["process", "item"]], "data"]
  ]
}
```

### WebSocket Streaming

```json
// Stream serialized code over WebSocket
{
  "type": "code_stream",
  "chunk": 1,
  "data": ["lambda", ["x"], 
  "continuation": true
}

{
  "type": "code_stream", 
  "chunk": 2,
  "data": ["*", "x", "x"]],
  "continuation": false
}
```

## Storage Serialization

### File System

```json
// functions.jsl
{
  "version": "1.0",
  "functions": {
    "utility": ["lambda", ["x"], ["host", "log", "x"]],
    "transform": ["lambda", ["data"], ["map", "process", "data"]]
  }
}
```

### Database Storage

```sql
-- PostgreSQL with JSONB
CREATE TABLE jsl_code (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  code JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO jsl_code (name, code) VALUES (
  'data_processor',
  '["lambda", ["items"], ["filter", ["lambda", ["x"], [">", "x", 0]], "items"]]'::JSONB
);
```

### Distributed Storage

```json
// Code distributed across multiple nodes
{
  "node_1": {
    "functions": ["math_functions"],
    "data": ["user_data_shard_1"]
  },
  "node_2": {
    "functions": ["string_functions"],
    "data": ["user_data_shard_2"] 
  }
}
```

JSL's native JSON serialization makes code and data completely portable, enabling powerful distributed computing patterns while maintaining simplicity and debuggability.