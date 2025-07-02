# JSL Special Forms

## Overview

Special forms are the fundamental building blocks of JSL that have special evaluation rules. Unlike regular function calls, special forms control how their arguments are evaluated and provide the core language constructs for variable binding, control flow, and meta-programming.

## Core Special Forms

### Variable Definition - `def`

Binds a value to a variable name in the current environment.

```json
["def", "variable_name", value_expression]
```

**Evaluation Rules:**
1. Evaluate `value_expression` 
2. Bind the result to `variable_name` in current environment
3. Return the bound value

**Examples:**

```json
// Simple value binding
["def", "x", 42]
// Result: 42, x is now bound to 42

// Expression binding
["def", "doubled", ["*", "x", 2]]
// Result: 84, doubled is now bound to 84

// Function binding
["def", "square", ["lambda", ["n"], ["*", "n", "n"]]]
// Result: <function>, square is now bound to the function
```

### Function Definition - `lambda`

Creates anonymous functions (closures) that capture their lexical environment.

```json
["lambda", ["param1", "param2", ...], body_expression]
```

**Evaluation Rules:**
1. Do NOT evaluate parameters (they are binding names)
2. Do NOT evaluate body (it's evaluated when function is called)
3. Capture current environment as closure environment
4. Return function object

**Examples:**

```json
// Simple function
["lambda", ["x"], ["*", "x", "x"]]
// Result: <function: x -> x * x>

// Multi-parameter function
["lambda", ["a", "b"], ["+", "a", "b"]]
// Result: <function: (a, b) -> a + b>

// Function with closure
["do",
  ["def", "multiplier", 10],
  ["lambda", ["x"], ["*", "x", "multiplier"]]]
// Result: <function: x -> x * 10> (captures multiplier=10)

// Higher-order function
["lambda", ["f", "x"], ["f", ["f", "x"]]]
// Result: <function: (f, x) -> f(f(x))>
```

### Conditional Evaluation - `if`

Provides conditional branching with lazy evaluation of branches.

```json
["if", condition_expression, then_expression, else_expression]
```

**Evaluation Rules:**
1. Evaluate `condition_expression`
2. If truthy, evaluate and return `then_expression`
3. If falsy, evaluate and return `else_expression`
4. Only one branch is evaluated (lazy evaluation)

**Examples:**

```json
// Basic conditional
["if", [">", "x", 0], "positive", "non-positive"]

// Nested conditionals
["if", ["=", "status", "admin"],
  "full_access",
  ["if", ["=", "status", "user"], "limited_access", "no_access"]]

// With side effects (only one branch executes)
["if", "debug_mode",
  ["host", "log", "Debug information"],
  ["host", "log", "Production mode"]]
```

### Local Bindings - `let`

Creates temporary, local variable bindings for use within a single expression. This is a cornerstone of functional programming as it avoids mutating the parent environment.

```json
["let", [["var1", val1_expr], ["var2", val2_expr]], body_expr]
```

**Evaluation Rules:**
1. Create a new, temporary environment that extends the current one.
2. Evaluate all `val_expr`s in the original environment.
3. Bind the results to the `var` names in the new temporary environment.
4. Evaluate `body_expr` in the new environment.
5. Return the result of `body_expr`. The temporary environment is then discarded.

**Example:**
```json
// Calculate area of a circle without polluting the environment
["let", [["pi", 3.14159], ["r", 10]],
  ["*", "pi", ["*", "r", "r"]]]
// Result: 314.159 (pi and r are not defined afterwards)
```

### Error Handling - `try`

Provides a mechanism to catch and handle errors that occur during evaluation.

```json
["try", body_expression, handler_expression]
```

**Evaluation Rules:**
1. Evaluate `body_expression`.
2. If evaluation succeeds, its result is the result of the `try` expression. The `handler_expression` is not evaluated.
3. If an error occurs during the evaluation of `body_expression`, the `handler_expression` is evaluated. The handler should be a function that accepts the error object as its argument. The result of the handler becomes the result of the entire `try` expression.

**Example:**
```json
// Safe file reading with a fallback default
["try",
  ["host", "file/read", "/app/config.json"],
  ["lambda", ["err"],
    ["do",
      ["host", "log/warn", ["str-concat", "Config not found, using default: ", ["get", "err", "message"]]],
      { "default_setting": true }
    ]
  ]
]
```

### Sequential Evaluation - `do`

Evaluates multiple expressions in sequence and returns the result of the final expression.

While JSL encourages a functional style using `let` and function composition, `do` is provided as a pragmatic tool for imperative-style sequencing, especially when dealing with multiple side-effects.

> **Design Note: Why is there no `for` or `while` loop?**
>
> JSL intentionally omits traditional `for` or `while` loop special forms. This is a core design decision to encourage a functional approach to collection processing. Instead of imperative looping, you should use the powerful higher-order functions provided in the prelude:
> - **`map`**: To transform each element in a list.
> - **`filter`**: To select elements from a list.
> - **`reduce`**: To aggregate a list into a single value.
> - **`for_each`**: To perform a side-effect for each element in a list.
>
> These functions are safer, more declarative, and more composable than manual loops.

### Quotation - `quote` and `@`

Prevents evaluation of expressions, returning them as literal data.

```json
["quote", expression]
["@", expression]  // Shorthand syntax
```

There  is also a syntactic sugar for quoting simple expressions:
  
```json
["quote", "hello"]  // Result: "hello"
"@hello"// Result: "hello" (same as above)
```
It is only useful for simple values, as it does not allow for complex expressions, such as:
`["@", ["+", 1, 2]]`.

**Evaluation Rules:**
1. Do NOT evaluate the argument
2. Return the argument as literal data
3. Preserves structure without interpretation

**Examples:**

```json
// Quote simple values
["quote", "hello"]     // Result: "hello"
["@", "hello"]         // Result: "hello" (same as above)

// Quote expressions
["quote", ["+", 1, 2]]  // Result: ["+", 1, 2] (not 3)
["@", ["+", 1, 2]]      // Result: ["+", 1, 2]

// Quote for data structure creation
["@", {"name": "Alice", "age": 30}]
// Result: {"name": "Alice", "age": 30}

// Compare quoted vs unquoted
["def", "expr", ["@", ["+", "x", "y"]]]  // Store expression as data
["def", "result", ["+", "x", "y"]]       // Store computed result
```

### Host Interaction - `host`

Provides controlled interaction with the host environment through JHIP.

```json
["host", command_id_expression, arg1_expression, ...]
```

**Evaluation Rules:**
1. Evaluate `command_id_expression` to get command identifier
2. Evaluate all argument expressions
3. Send JHIP request to host with command and arguments
4. Return host response

**Examples:**

```json
// File operations
["host", "file/read", "/path/to/file.txt"]
["host", "file/write", "/path/to/output.txt", "content"]

// System commands
["host", "system/exec", "ls", ["-la"]]

// Network requests
["host", "http/get", "https://api.example.com/data"]

// Time operations
["host", "time/now"]
["host", "time/format", "2023-12-01T10:30:00Z", "ISO"]
```

## Special Form Properties

### Argument Evaluation Control

Unlike regular functions, special forms control when and if their arguments are evaluated:

| Special Form | Evaluation Pattern |
|--------------|-------------------|
| `def` | Evaluate value, don't evaluate variable name |
| `lambda` | Don't evaluate parameters or body |
| `if` | Evaluate condition, then only one branch |
| `let` | Evaluate bindings, then body in new scope |
| `try` | Evaluate body, then handler only on error |
| `do` | Evaluate all arguments in sequence |
| `quote`/`@` | Don't evaluate argument at all |
| `host` | Evaluate all arguments |

### Environment Interaction

Special forms interact with the environment in specific ways:

```json
// def modifies environment
["do",
  ["def", "x", 10],        // Adds x=10 to environment
  ["def", "y", ["*", "x", 2]], // Uses x from environment, adds y=20
  ["+", "x", "y"]]         // Uses both x and y: result 30

// lambda captures environment
["do",
  ["def", "base", 100],
  ["def", "adder", ["lambda", ["n"], ["+", "n", "base"]]],
  ["adder", 23]]           // Result: 123 (uses captured base=100)
```

## Meta-Programming with Special Forms

### Code Generation

```json
// Generate conditional code
["def", "make_comparator", 
  ["lambda", ["op"], 
    ["@", ["lambda", ["a", "b"], ["op", "a", "b"]]]]]

// Usage
["def", "greater_than", ["make_comparator", ">"]]
["greater_than", 5, 3]  // Result: true
```

### Dynamic Function Creation

```json
// Create functions with varying parameter counts
["def", "make_n_ary_function",
  ["lambda", ["params", "body"],
    ["list", "@lambda", "params", "body"]]]

["def", "triple_add", 
  ["make_n_ary_function", 
    ["@", ["a", "b", "c"]], 
    ["@", ["+", ["+", "a", "b"], "c"]]]]
```

### Macro-like Patterns

```json
// Define a "when" macro-like construct
["def", "when",
  ["lambda", ["condition", "action"],
    ["if", "condition", "action", null]]]

// Usage
["when", [">", "temperature", 30], 
  ["host", "log", "@It's hot outside!"]]
```

## Advanced Special Form Usage

### Combining Special Forms

```json
// Complex initialization pattern
["do",
  ["def", "config", ["host", "file/read", "config.json"]],
  ["def", "database", 
    ["if", ["get", "config", "use_database"],
      ["host", "db/connect", ["get", "config", "db_url"]],
      null]],
  ["def", "processor",
    ["lambda", ["data"],
      ["if", "database",
        ["host", "db/store", "database", "data"],
        ["host", "log", "@No database configured"]]]],
  "processor"]
```

### Error Handling Patterns

```json
// Safe evaluation with fallback
["def", "safe_eval",
  ["lambda", ["expr", "fallback"],
    ["if", ["try", "expr"],
      "expr",
      "fallback"]]]

// Conditional resource acquisition
["def", "with_resource",
  ["lambda", ["resource_id", "action"],
    ["do",
      ["def", "resource", ["host", "resource/acquire", "resource_id"]],
      ["if", "resource",
        ["do",
          ["def", "result", ["action", "resource"]],
          ["host", "resource/release", "resource"],
          "result"],
        null]]]]
```

## Special Forms vs Functions

### Key Differences

| Aspect | Special Forms | Functions |
|--------|---------------|-----------|
| **Argument Evaluation** | Controlled by form | All arguments evaluated |
| **Environment Access** | Can modify environment | Read-only environment access |
| **Evaluation Order** | Form-specific rules | Standard left-to-right |
| **Meta-Programming** | Enable code generation | Operate on values only |
| **Syntax Extension** | Can create new syntax | Cannot extend syntax |

### When to Use Each

**Use Special Forms for:**
- Control flow (`if`, `do`)
- Variable binding (`def`, `let`)
- Function creation (`lambda`)
- Meta-programming (`quote`)
- Host interaction (`host`)
- Error handling (`try`)

**Use Functions for:**
- Data transformation
- Mathematical operations
- String processing
- Collection manipulation
- Business logic
- JSON object construction (using JSL's first-class object support)

## Implementation Notes

### Evaluation Context

Special forms are evaluated in the context of JSL's evaluator, which maintains:

1. **Environment Stack**: For variable resolution and binding
2. **Continuation Stack**: For function calls and returns
3. **Host Interface**: For JHIP command execution
4. **Error Handling**: For exception propagation

### Performance Considerations

- **`def`**: O(1) environment binding
- **`let`**: O(1) local binding
- **`try`**: O(n) body evaluation, O(m) handler evaluation on error
- **`lambda`**: O(1) closure creation, O(e) environment capture
- **`if`**: O(1) branch selection, avoids evaluating unused branch  
- **`do`**: O(n) sequential evaluation
- **`quote`**: O(1) literal return
- **`host`**: O(h) depends on host operation complexity

Special forms are the foundation of JSL's expressiveness, providing the essential building blocks for all higher-level language constructs while maintaining the language's homoiconic JSON-based structure.

## Special Form Details

### `host`

The `host` special form is the gateway for all side effects and interactions with the host system.

-   **Syntax**: `["host", command_expr, arg1_expr, ...]`
-   **Evaluation**: All arguments are evaluated. The results are packaged into a JHIP request and yielded to the host runtime.

## JSON Objects as First-Class Citizens

JSL provides powerful support for JSON object construction through its first-class object syntax. Objects in JSL:

- Are always treated as data structures (never function calls)
- Use normal JSL evaluation rules for both keys and values
- Require keys to evaluate to strings
- Support dynamic construction with variables and expressions

For example:
```json
["do",
  ["def", "name", "@Alice"],
  ["def", "age", 30],
  {"@greeting": ["str-concat", "@Hello ", "name"],
   "@info": {"@name": "name", "@age": "age"}}
]
```

For more details, see **[JSON Objects as First-Class Citizens](./objects.md)**.

