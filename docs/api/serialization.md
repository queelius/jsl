# Serialization API

> For conceptual background on JSL's serialization design, see [Architecture: Serialization](../architecture/serialization.md).

## Overview

The JSL serialization API provides functions for converting JSL code and data structures to and from JSON representations using content-addressable storage. This approach elegantly handles circular references and ensures efficient serialization of complex object graphs including closures and environments.

## Core Functions

::: jsl.serialization
    options:
      show_root_heading: false
      show_source: true
      members:
        - serialize
        - deserialize
        - to_json
        - from_json
        - serialize_program
        - deserialize_program

## Usage Examples

### Basic Serialization

```python
from jsl.serialization import serialize, deserialize

# Serialize simple JSL values
expr = ["+", 1, 2]
json_str = serialize(expr)
# Result: '["+", 1, 2]'

# Deserialize back to JSL
restored = deserialize(json_str)
# Result: ["+", 1, 2]

# Complex values use content-addressable format
from jsl import eval_expression, make_prelude
closure = eval_expression('["lambda", ["x"], ["+", "x", 1]]', make_prelude())
serialized = serialize(closure)
# Result contains "__cas_version__", "root", and "objects" fields
```

### Closure Serialization

```python
from jsl import eval_expression, make_prelude, serialize, deserialize

# Create and serialize a closure with captured environment
program = '''
["do",
  ["def", "base", 100],
  ["lambda", ["x"], ["+", "x", "base"]]
]
'''
closure = eval_expression(program, make_prelude())
serialized = serialize(closure)

# Deserialize with prelude environment
restored = deserialize(serialized, make_prelude())
```

### Network Transmission

```python
import json
from jsl.serialization import serialize

# Prepare JSL code for network transmission
code = ["lambda", ["x"], ["*", "x", "x"]]
payload = {
    "type": "execute",
    "code": serialize(code),
    "timestamp": "2023-12-01T10:00:00Z"
}

# Send as JSON
json_payload = json.dumps(payload)
```

### Program Serialization

```python
from jsl.serialization import serialize_program, deserialize_program

# Serialize complete program with metadata
program = ["+", 1, 2, 3]
program_data = serialize_program(program, prelude_hash="v1.0")

# Result includes version, prelude_hash, and program data
# {
#   "version": "0.1.0",
#   "prelude_hash": "v1.0", 
#   "program": 6,
#   "timestamp": null
# }

# Deserialize program
restored = deserialize_program(program_data)
```

## Type Mappings

| JSL Type | JSON Type | Notes |
|----------|-----------|-------|
| Number | Number | Direct mapping for primitives |
| String | String | Direct mapping for primitives |  
| Boolean | Boolean | Direct mapping for primitives |
| Null | Null | Direct mapping for primitives |
| Array | Array | Direct for simple arrays, CAS for arrays containing closures |
| Object | Object | Direct for simple objects, CAS for objects containing closures |
| Closure | Object | CAS format with `__type__: "closure"` |
| Environment | Object | CAS format with `__type__: "env"` |

## Serialization Formats

JSL uses two serialization formats depending on the complexity of the data:

1. **Direct JSON**: For primitive values and simple structures without closures
2. **Content-Addressable Storage (CAS)**: For complex objects containing closures or environments

```python
# Direct JSON format
serialize(42)              # "42"
serialize([1, 2, 3])      # "[1,2,3]"
serialize({"key": "val"}) # "{\"key\":\"val\"}"

# CAS format (contains closures/environments)
serialize(some_closure)   # {"__cas_version__": 1, "root": {...}, "objects": {...}}
```

## Error Handling

The serialization API handles various error conditions:

- **Circular References**: Handled elegantly using content-addressable storage
- **Invalid JSON**: Proper error messages for malformed input
- **Type Errors**: Clear indication of unsupported types
- **Encoding Issues**: UTF-8 handling for international text
- **Missing Objects**: Validation of object references during deserialization

## Performance Notes

- **Time Complexity**: O(n) where n is the size of the data structure
- **Space Complexity**: Efficient sharing of identical objects through content addressing
- **Circular Reference Handling**: No stack overflow or infinite loops
- **Deterministic Hashing**: Same content always produces same hash
