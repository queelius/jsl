# Serialization API

> For conceptual background on JSL's serialization design, see [Architecture: Serialization](../architecture/serialization.md).

## Overview

The JSL serialization API provides functions for converting JSL code and data structures to and from JSON representations, with special handling for closures and environment capture.

## Core Functions

::: jsl.serialization
    options:
      show_root_heading: false
      show_source: true
      members:
        - serialize
        - deserialize
        - serialize_closure
        - deserialize_closure

## Usage Examples

### Basic Serialization

```python
from jsl.serialization import serialize, deserialize

# Serialize JSL expression
expr = ["+", 1, 2]
json_str = serialize(expr)
# Result: '["+"", 1, 2]'

# Deserialize back to JSL
restored = deserialize(json_str)
# Result: ["+", 1, 2]
```

### Closure Serialization

```python
from jsl.serialization import serialize_closure, deserialize_closure

# Serialize a closure with captured environment
closure_data = {
    "params": ["x"],
    "body": ["+", "x", "captured_var"],
    "env": {"captured_var": 10}
}

serialized = serialize_closure(closure_data)
restored = deserialize_closure(serialized)
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

## Type Mappings

| JSL Type | JSON Type | Notes |
|----------|-----------|-------|
| Number | Number | Direct mapping |
| String | String | Direct mapping |  
| Boolean | Boolean | Direct mapping |
| Null | Null | Direct mapping |
| Array | Array | Recursive serialization |
| Object | Object | Recursive serialization |
| Closure | Object | Special format with type field |

## Error Handling

The serialization API handles various error conditions:

- **Circular References**: Detected and handled gracefully
- **Invalid JSON**: Proper error messages for malformed input
- **Type Errors**: Clear indication of unsupported types
- **Encoding Issues**: UTF-8 handling for international text

## Performance Notes

- **Time Complexity**: O(n) where n is the size of the data structure
- **Space Complexity**: O(d) additional space where d is the depth of nesting
- **Optimization**: Built-in caching for repeated serialization of identical structures