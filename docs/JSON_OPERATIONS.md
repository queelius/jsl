# JSON Operations in JSL

## Motivation

JSL's JSON manipulation features are inspired by [dotsuite](https://github.com/queelius/dotsuite), a pedagogical approach to querying, transforming, and filtering JSON data. Since JSL is a JSON-native language where all programs and data are representable as standard JSON, providing powerful JSON manipulation primitives is essential.

The dotsuite project demonstrates elegant patterns for working with JSON data through:
- **dotpath**: Deep path navigation using dot notation
- **dotpipe/dotmod**: Pipeline transformations on JSON objects
- **dotfilter**: Declarative filtering of JSON collections

JSL adapts these concepts to fit naturally within a Lisp-like functional programming paradigm, making JSON manipulation a first-class concern.

## Core Operations

### 1. Path Navigation (inspired by dotpath)

Deep path access allows navigating nested JSON structures with simple path strings:

```json
// Instead of nested gets:
["get", ["get", ["get", user, "@address"], "@city"], "@name"]

// Use path navigation:
["get-path", user, "@address.city.name"]
```

**Available functions:**
- `get-path` - Navigate to a value at a deep path
- `set-path` - Set a value at a deep path (returns new object)
- `has-path` - Check if a path exists
- `get-safe` - Safe navigation with default values
- `get-default` - Explicit default for missing paths

**Features:**
- Dot notation: `"user.address.city"`
- Array indexing: `"items.0.price"` or `"items[0].price"`
- Wildcards: `"users.*.email"` returns all email values

### 2. Declarative Filtering (inspired by dotfilter)

The `where` operator provides SQL-like declarative filtering without verbose lambda expressions:

```json
// Traditional approach with lambda:
["filter", 
  ["lambda", ["user"], 
    ["and", 
      ["=", ["get", "user", "@role"], "@admin"],
      ["get", "user", "@active"]
    ]
  ],
  users
]

// Declarative approach with where:
["where", users, 
  ["@and",
    ["@role", "@=", "@admin"],
    ["@active", "@=", true]
  ]
]
```

**Query operators:**
- Comparison: `=`, `!=`, `>`, `<`, `>=`, `<=`
- String/array: `contains`
- Pattern matching: `matches` (regex)
- Logical: `and`, `or`, `not`

### 3. Pipeline Transformations (inspired by dotpipe/dotmod)

The `transform` operator enables composable object transformations:

```json
// Apply multiple transformations in sequence:
["transform", data,
  ["@assign", "@computed", ["*", ["get", "data", "@x"], 2]],
  ["@pick", "@id", "@name", "@computed"],
  ["@rename", "@computed", "@result"],
  ["@default", "@status", "@pending"]
]
```

**Transform operations:**
- `assign` - Add or update fields
- `pick` - Keep only specified fields
- `omit` - Remove specified fields
- `rename` - Rename fields
- `default` - Set values for missing fields
- `apply` - Transform field values with functions

### 4. Collection Utilities

Additional operations for working with JSON collections:

```json
// Extract single field from each item:
["pluck", users, "@email"]
// Returns: ["alice@example.com", "bob@example.com", ...]

// Convert list to keyed object:
["index-by", users, "@id"]
// Returns: {"123": {user1}, "456": {user2}, ...}

// Group items by field value:
["group-by", users, "@department"]
// Returns: {"sales": [...], "engineering": [...], ...}
```

## Design Philosophy

Following dotsuite's pedagogical approach, these operations are designed to be:

1. **Intuitive**: Operations mirror common data manipulation patterns
2. **Composable**: Small operations combine into complex pipelines
3. **Declarative**: Express *what* you want, not *how* to get it
4. **JSON-Native**: Work naturally with JSON's structure
5. **Functional**: All operations return new data, preserving immutability

## Examples

### Example 1: Query and Transform User Data

```json
// Find active admin users and prepare for API response
["transform",
  ["where", users, 
    ["@and",
      ["@role", "@=", "@admin"],
      ["@active", "@=", true]
    ]
  ],
  ["@pick", "@id", "@name", "@email"],
  ["@assign", "@type", "@admin_user"]
]
```

### Example 2: Aggregate Nested Data

```json
// Get total value of orders from VIP customers
["reduce",
  ["lambda", ["sum", "order"], 
    ["+", "sum", ["get-path", "order", "@total"]]
  ],
  ["where", orders, ["@customer.vip", "@=", true]],
  0
]
```

### Example 3: Complex Data Pipeline

```json
// Process product catalog: filter, enrich, and index
["index-by",
  ["transform",
    ["where", products, 
      ["@and",
        ["@category", "@=", "@electronics"],
        ["@price", "@<", 1000]
      ]
    ],
    ["@assign", "@discount", 0.1],
    ["@apply", "@name", ["lambda", ["n"], ["str-upper", "n"]]],
    ["@pick", "@id", "@name", "@price", "@discount"]
  ],
  "@id"
]
```

## Comparison with Traditional Approaches

### Without JSON Operations
```json
// Deeply nested, hard to read and maintain
["map",
  ["lambda", ["item"],
    ["if",
      ["and",
        ["=", ["get", ["get", "item", "@metadata"], "@status"], "@active"],
        [">", ["get", "item", "@score"], 80]
      ],
      {
        "@id": ["get", "item", "@id"],
        "@result": ["*", ["get", "item", "@score"], 1.1]
      },
      null
    ]
  ],
  ["filter", 
    ["lambda", ["x"], ["not", ["is-null", "x"]]],
    items
  ]
]
```

### With JSON Operations
```json
// Clear, maintainable, and expressive
["transform",
  ["where", items,
    ["@and",
      ["@metadata.status", "@=", "@active"],
      ["@score", "@>", 80]
    ]
  ],
  ["@pick", "@id", "@score"],
  ["@apply", "@score", ["lambda", ["s"], ["*", "s", 1.1]]],
  ["@rename", "@score", "@result"]
]
```

## Integration with JSL

These operations integrate seamlessly with JSL's existing features:

- **Functional composition**: Use with `map`, `filter`, `reduce`
- **Lambda expressions**: Mix declarative and functional styles
- **Immutability**: All operations preserve JSL's immutable semantics
- **Serialization**: Operations and their results remain JSON-serializable
- **Network-native**: Perfect for distributed data processing

## References

- [dotsuite](https://github.com/queelius/dotsuite) - Original inspiration for these patterns
- [jq](https://stedolan.github.io/jq/) - Command-line JSON processor
- [JSONPath](https://goessner.net/articles/JsonPath/) - XPath for JSON
- [SQL/JSON](https://www.iso.org/standard/67367.html) - SQL extensions for JSON