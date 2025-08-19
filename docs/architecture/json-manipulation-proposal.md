# JSON Manipulation Features for JSL

Since JSL is JSON-native, it should excel at JSON data manipulation. Based on the dotsuite patterns, here are proposed features:

## 1. Deep Path Navigation

### Current Limitation
```json
// Currently need nested gets:
["get", ["get", ["get", user, "@address"], "@city"], "@name"]

// Or define a function:
["lambda", ["obj"], 
  ["get", ["get", ["get", "obj", "@address"], "@city"], "@name"]]
```

### Proposed: `get-path` operator
```json
// Direct path access
["get-path", user, "@address.city.name"]

// With array indexing
["get-path", data, "@items.0.price"]

// With wildcards
["get-path", data, "@users.*.email"]  // Returns all emails
```

### Implementation
```json
["def", "get-path", ["lambda", ["obj", "path"],
  ["reduce", 
    ["lambda", ["acc", "key"], ["get", "acc", "key"]],
    ["str-split", "path", "@."],
    "obj"
  ]
]]
```

## 2. Query-Based Filtering

### Current Limitation
```json
// Currently need explicit lambdas:
["filter", 
  ["lambda", ["user"], 
    ["and", 
      ["=", ["get", "user", "@role"], "@admin"],
      ["get", "user", "@active"]
    ]
  ],
  users
]
```

### Proposed: `where` operator
```json
// Declarative filtering
["where", users, ["@role", "=", "@admin"]]

// Compound conditions
["where", users, 
  ["and",
    ["@role", "=", "@admin"],
    ["@active", "=", true]
  ]
]

// Nested paths
["where", users, ["@address.country", "=", "@USA"]]
```

### Query Operators
- `["@field", "=", value]` - Equality
- `["@field", "!=", value]` - Inequality  
- `["@field", ">", value]` - Greater than
- `["@field", "<", value]` - Less than
- `["@field", "contains", value]` - String/array contains
- `["@field", "matches", pattern]` - Regex match

## 3. Object Transformation Pipelines

### Current Limitation
```json
// Currently need multiple steps:
["do",
  ["def", "temp", ["get", data, "@user"]],
  ["def", "temp", ["set", "temp", "@fullName", 
    ["str-concat", ["get", "temp", "@firstName"], "@ ", ["get", "temp", "@lastName"]]
  ]],
  ["def", "result", {"@user": "temp", "@timestamp": ["now"]}],
  "result"
]
```

### Proposed: `transform` operator
```json
// Pipeline transformations
["transform", data,
  ["assign", "@fullName", ["concat-path", "@firstName", "@ ", "@lastName"]],
  ["pick", "@id", "@fullName", "@email"],
  ["rename", "@email", "@contact"],
  ["default", "@status", "@active"]
]
```

### Transform Operations
- `["assign", field, value]` - Add/update field
- `["pick", ...fields]` - Keep only specified fields
- `["omit", ...fields]` - Remove specified fields
- `["rename", old, new]` - Rename field
- `["default", field, value]` - Set if missing
- `["apply", field, function]` - Transform field value

## 4. Collection Operations

### Proposed: Enhanced collection operations
```json
// Group by
["group-by", users, "@department"]
// Returns: {"@engineering": [...], "@sales": [...]}

// Unique values
["unique", ["get-path", users, "@*.email"]]

// Pluck single field
["pluck", users, "@email"]
// Equivalent to: ["map", ["lambda", ["x"], ["get", "x", "@email"]], users]

// Index by
["index-by", users, "@id"]
// Returns: {"@123": {user1}, "@456": {user2}}
```

## 5. Safe Navigation

### Proposed: `get-safe` operator
```json
// Returns null instead of error if path doesn't exist
["get-safe", user, "@address.city.name"]

// With default value
["get-default", user, "@address.city.name", "@Unknown"]
```

## Implementation Strategy

These features could be implemented in phases:

### Phase 1: Core Path Operations
- `get-path` - Deep path access
- `set-path` - Deep path setting
- `has-path` - Check if path exists
- `get-safe` - Safe navigation

### Phase 2: Query Operations  
- `where` - Declarative filtering
- Query expression evaluation

### Phase 3: Transform Operations
- `transform` - Pipeline transformations
- Individual transform operations

### Phase 4: Advanced Collections
- `group-by` - Group collection by field
- `index-by` - Convert to keyed object
- `pluck` - Extract single field
- `unique` - Unique values

## Benefits

1. **More Intuitive**: Declarative operations are easier to read/write than nested lambdas
2. **JSON-Native**: Leverages JSL's JSON foundation
3. **Composable**: Operations can be easily combined
4. **Network-Friendly**: All operations remain serializable
5. **Performance**: Can be optimized in the evaluator

## Examples

### Before (Current JSL)
```json
["filter",
  ["lambda", ["user"],
    ["and",
      ["=", ["get", "user", "@role"], "@admin"],
      ["get", "user", "@active"]
    ]
  ],
  ["map",
    ["lambda", ["user"],
      {"@id": ["get", "user", "@id"],
       "@name": ["str-concat", 
         ["get", "user", "@firstName"], 
         "@ ", 
         ["get", "user", "@lastName"]
       ],
       "@email": ["get", "user", "@email"]}
    ],
    users
  ]
]
```

### After (With Proposed Features)
```json
["transform",
  ["where", users, 
    ["and", 
      ["@role", "=", "@admin"],
      ["@active", "=", true]
    ]
  ],
  ["assign", "@name", ["concat-path", "@firstName", "@ ", "@lastName"]],
  ["pick", "@id", "@name", "@email"]
]
```

## Compatibility

All proposed features can be implemented as:
1. Built-in functions in the prelude
2. Special forms in the evaluator
3. Macro expansions to existing operations

This ensures backward compatibility while adding powerful JSON manipulation capabilities.