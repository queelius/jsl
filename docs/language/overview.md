# JSL Language Overview

## What is JSL?

JSL (JSON Serializable Language) is a powerful, functional programming language where every program is valid JSON. This unique design makes it perfect for network transmission, distributed computing, and safe, sandboxed execution.

JSL is built on three core principles:
1.  **Homoiconic**: Code and data share the same structure (JSON). This means you can build and manipulate code as easily as you handle data.
2.  **Functional**: With features like immutability, first-class functions, and a rich library of higher-order functions, JSL encourages a clean, declarative style.
3.  **Serializable**: Every JSL value, including functions with their environments, can be perfectly serialized to a string, sent across a network, and safely executed on a remote machine.

## A Taste of JSL

Because JSL is JSON, operations use a simple prefix notation inside an array. This expression adds three numbers:
```json
["+", 1, 2, 3]
```
The evaluator understands that the first element, `"+"`, is a function to be applied to the rest of the elements, resulting in `6`.

## The Two Modes of JSL

JSL has a single, consistent evaluation model where:

### Core Evaluation Rules

1. **Strings without `@`**: Variable lookups (e.g., `"x"` looks up the value of x)
2. **Strings with `@`**: Literal strings (e.g., `"@hello"` is the string "hello")
3. **Arrays**: Function calls in prefix notation (e.g., `["+", 1, 2]`)
4. **Objects**: Data structures with evaluated keys and values
5. **Other values**: Self-evaluating (numbers, booleans, null)

### JSON Object Construction

JSL treats JSON objects as first-class data structures. Unlike arrays (which are interpreted as S-expressions), objects are always data structures, never function calls. This makes them perfect for constructing pure JSON output:

```json
["do",
  ["def", "user", "@Alice"],
  ["def", "role", "@admin"],
  {"@name": "user", "@role": "role"}
]
// Result: {"name": "Alice", "role": "admin"}
```

> For a complete guide, see **[JSON Objects as First-Class Citizens](./objects.md)**.

## Key Language Features

-   **Special Forms**: A small set of core keywords like `if`, `def`, and `lambda` provide the foundation for control flow and variable bindings. See the **[Special Forms Guide](./special-forms.md)**.
-   **Rich Prelude**: A comprehensive standard library of functions for math, logic, and data manipulation is available everywhere. See the **[Prelude Reference](./prelude.md)**.
-   **Lexical Scoping**: JSL uses lexical scoping, meaning functions (closures) capture the environment where they are defined, not where they are called. This provides a robust and predictable module system.
-   **Host Interaction**: JSL interacts with the host system through a single, explicit special form, `["host", ...]`, making all side effects transparent and auditable.

## A Complete Example

This example defines and calls a recursive factorial function, showcasing variable and function definition (`def`, `lambda`), conditional logic (`if`), and a sequence of operations (`do`).

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
The result of evaluating this expression is `120`.

## Where to Go Next

-   **[JSL Syntax and Semantics](./semantics.md)**: The definitive guide to writing and understanding core JSL.
-   **[JSON Objects](./objects.md)**: Learn how to generate dynamic JSON objects.
-   **[Special Forms](./special-forms.md)**: A detailed reference for all core language constructs.
-   **[Prelude Functions](./prelude.md)**: A complete catalog of all built-in functions
