# Language Overview

JSL (JSON Serializable Language) is a functional programming language designed for network transmission and distributed computing. Every JSL program is valid JSON that can be executed directly.

## Core Concepts

### Homoiconicity
JSL code and data use the same JSON representation. There's no distinction between code that executes and data that gets processed - they're all JSON values.

### Prefix Notation
All operations use prefix notation (operator comes first):

```json
["+", 1, 2, 3]        // Addition: 1 + 2 + 3 = 6
["*", 2, ["+", 3, 4]] // Multiplication: 2 * (3 + 4) = 14
```

### Immutability
JSL values are immutable. Operations return new values rather than modifying existing ones:

```json
["append", [1, 2, 3], 4]  // Returns [1, 2, 3, 4], original unchanged
```

## Data Types

JSL supports all JSON data types plus function closures:

### Primitives
- **null**: `null`
- **boolean**: `true`, `false`  
- **number**: `42`, `3.14`, `-17`
- **string**: `"hello"`, `"world"`

### Collections
- **list**: `[1, 2, 3]`, `["a", "b", "c"]`
- **object**: `{"name": "Alice", "age": 30}`

### Functions
- **built-ins**: `+`, `map`, `filter` (provided by prelude)
- **closures**: `["lambda", ["x"], ["*", "x", 2]]` (user-defined)

## Special Forms

Special forms are built-in constructs that control evaluation flow:

### `do` - Sequential Execution
Executes expressions in order, returns the last result:

```json
[
  "do",
  ["def", "x", 5],
  ["def", "y", 10], 
  ["+", "x", "y"]
]
// Result: 15
```

### `def` - Variable Definition
Binds a value to a name in the current environment:

```json
["def", "pi", 3.14159]
```

### `lambda` - Function Definition
Creates an anonymous function:

```json
["lambda", ["x", "y"], ["+", "x", "y"]]
```

### `if` - Conditional Expression
Evaluates condition and returns appropriate branch:

```json
["if", [">", "x", 0], "positive", "non-positive"]
```

### `quote` - Literal Values
Prevents evaluation of an expression:

```json
["quote", ["+", 1, 2]]  // Returns ["+", 1, 2], not 3
```

### `template` - JSON Generation
Dynamically generates JSON with computed values:

```json
["template", {
  "name": {"$": "username"},
  "timestamp": {"$": ["now"]},
  "data": [1, 2, {"value": {"$": ["*", "x", 2]}}]
}]
```

## Variable References

Variables are referenced by name as strings:

```json
[
  "do",
  ["def", "radius", 5],
  ["def", "area", ["*", "pi", "radius", "radius"]],
  "area"
]
```

## Function Calls

Functions are called by placing them first in a list:

```json
// Built-in function
["+", 1, 2, 3]

// User-defined function  
[
  "do",
  ["def", "square", ["lambda", ["x"], ["*", "x", "x"]]],
  ["square", 5]
]
```

## Lexical Scoping

JSL uses lexical scoping - functions capture their defining environment:

```json
[
  "do",
  ["def", "multiplier", 3],
  ["def", "triple", ["lambda", ["x"], ["*", "multiplier", "x"]]],
  ["def", "multiplier", 5],  // This doesn't affect 'triple'
  ["triple", 4]               // Returns 12, not 20
]
```

## Higher-Order Functions

Functions can accept and return other functions:

```json
[
  "do",
  ["def", "numbers", [1, 2, 3, 4, 5]],
  ["def", "double", ["lambda", ["x"], ["*", "x", 2]]],
  ["map", "double", "numbers"]
]
// Result: [2, 4, 6, 8, 10]
```

## Error Handling

JSL provides basic error handling through built-in functions:

```json
// Raise an error
["error", "Something went wrong!"]

// Safe operations with defaults
["get", {"a": 1}, "b", "default"]  // Returns "default"
```

## Examples

### Factorial Function

```json
[
  "do",
  ["def", "factorial",
   ["lambda", ["n"],
    ["if", ["<=", "n", 1],
     1,
     ["*", "n", ["factorial", ["-", "n", 1]]]]]],
  ["factorial", 5]
]
// Result: 120
```

### List Processing

```json
[
  "do",
  ["def", "numbers", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
  ["def", "is-even", ["lambda", ["n"], ["=", ["mod", "n", 2], 0]]],
  ["def", "evens", ["filter", "is-even", "numbers"]],
  ["def", "sum", ["reduce", "+", "evens", 0]],
  {"evens": "evens", "sum": "sum"}
]
// Result: {"evens": [2, 4, 6, 8, 10], "sum": 30}
```

### Data Transformation

```json
[
  "do",
  ["def", "users", [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
  ]],
  ["def", "adult-names",
   ["map", 
    ["lambda", ["user"], ["get", "user", "name"]],
    ["filter", 
     ["lambda", ["user"], [">=", ["get", "user", "age"], 18]],
     "users"]]],
  "adult-names"
]
// Result: ["Alice", "Bob", "Charlie"]
```

## Serialization

Every JSL value (including functions) can be serialized to JSON:

```json
// Original function
["lambda", ["x"], ["*", "x", 2]]

// After serialization and deserialization, works identically
// Can be transmitted over network, stored in database, etc.
```

## Host Interaction

JSL programs can interact with their host environment through:

1. **Built-in functions** - Provided by the prelude
2. **JHIP commands** - Host-specific operations
3. **I/O functions** - Like `print` for output

## Next Steps

- **[AST Specification](ast.md)** - Formal syntax definition
- **[Special Forms](special-forms.md)** - Detailed special form reference  
- **[Prelude Functions](prelude.md)** - Complete built-in function catalog
- **[JSON Templates](templates.md)** - Dynamic JSON generation guide
