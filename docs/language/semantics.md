# Syntax and Semantics

## Overview

JSL uses JSON as its native syntax, making it both human-readable and machine-parseable. Every JSL program is a valid JSON value, and this document describes how those values are interpreted and evaluated.

## Core Concepts

1.  **Homoiconicity**: Code and data share the same fundamental representation (JSON).
2.  **Evaluation Environments**: Expressions are evaluated within a specific environment that holds variable bindings and links to a parent.
3.  **Lisp-like Evaluation**: The evaluation logic follows a pattern similar to Lisp, with prefix notation for function calls.

## Syntax and Evaluation Rules

### 1. Literals (Self-Evaluating Values)

Most JSON primitives are literals; they evaluate to themselves.

-   **Numbers**: `42` → `42`
-   **Booleans**: `true` → `true`
-   **Null**: `null` → `null`
-   **Objects**: `{"key": "value"}` → `{"key": "value"}`

### 2. Strings: Literals vs. Variables

The interpretation of a string depends on its syntax.

-   **Variable Reference**: A standard string is treated as a variable lookup. The evaluator will search the current environment for its value.
    - `"x"` → The value bound to the name `x`.
-   **String Literal**: A string prefixed with `@` is treated as a literal value.
    - `"@hello"` → The string `"hello"`.

### 3. Arrays: Function Calls and Special Forms

Arrays are the primary mechanism for computation in JSL. An array is evaluated by inspecting its first element.

-   **Empty Array**: An empty array `[]` evaluates to itself, representing an empty list.
-   **Function Call**: If the first element is not a special form, the array represents a function call.
    1.  All elements of the array (the operator and all arguments) are evaluated in order.
    2.  The result of the first element (which must be a function) is applied to the results of the remaining elements.
    - `["+", 1, "x"]` → Evaluates `+`, `1`, and `x`, then applies the addition function to the results.

-   **Special Forms**: If the first element is a special form, a unique evaluation rule is applied. These forms provide the core control flow and structural logic of the language. Not all arguments are necessarily evaluated.

| Form | Syntax | Description |
|---|---|---|
| `def` | `["def", "name", expr]` | Binds the result of `expr` to `name` in the current environment. |
| `lambda` | `["lambda", [params], body]` | Creates a function (closure). Does not evaluate the body. |
| `if` | `["if", cond, then, else]` | Evaluates `cond`. If truthy, evaluates `then`, otherwise evaluates `else`. |
| `do` | `["do", expr1, expr2, ...]` | Evaluates expressions in sequence, returning the result of the last one. |
| `quote` / `@` | `["quote", expr]` or `["@", expr]` | Returns `expr` as literal data without evaluating it. |
| `try` | `["try", body, handler]` | Evaluates `body`. If an error occurs, evaluates `handler` with the error. |
| `host` | `["host", cmd, ...]` | Sends a request to the host environment. |

### Complete Example

This expression calculates the factorial of 5, demonstrating variable definition (`def`), function creation (`lambda`), conditional logic (`if`), and recursive function calls.

```json
["do",
  ["def", "factorial", 
    ["lambda", ["n"], 
      ["if", ["<=", "n", 1], 
        1, 
        ["*", "n", ["factorial", ["-", "n", 1]]]
      ]
    ]
  ],
  ["factorial", 5]
]
```

## JSL for Data Construction: JSON Objects as First-Class Citizens

While the semantics described above define JSL as a general-purpose computation language, JSL also treats **JSON objects as first-class data structures** with special properties that make them ideal for data construction.

Unlike arrays (which are interpreted as S-expressions), JSON objects are always treated as data structures:
- **Objects are never function calls**: `{"name": "Alice"}` is always a data structure
- **Keys and values are evaluated**: Both use normal JSL evaluation rules
- **Keys must be strings**: Runtime type checking ensures valid JSON output
- **No operator ambiguity**: Objects provide a "safe zone" for pure data construction

This design makes JSL particularly well-suited for generating clean JSON output without worrying about the first element being interpreted as an operator.

For a complete guide on object construction, see the **[JSON Objects](./objects.md)** documentation.
