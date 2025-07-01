# Quick Start

This guide will get you running JSL programs in minutes. JSL programs are valid JSON that can be executed directly.

## Your First JSL Program

Create a file called `hello.json`:

```json
["print", "Hello, World!"]
```

Run it:

```bash
python -m jsl hello.json
```

Output:
```
Hello, World!
```

## Basic Arithmetic

JSL uses prefix notation for all operations:

```json
["+", 1, 2, 3]
```

Result: `6`

More complex expressions:

```json
["*", ["+", 2, 3], ["-", 10, 6]]
```

Result: `20` (equivalent to `(2 + 3) * (10 - 6)`)

## Variables and Functions

Define variables using `def`:

```json
[
  "do",
  ["def", "x", 42],
  ["print", "x is:", "x"]
]
```

Define functions using `lambda`:

```json
[
  "do",
  ["def", "square", ["lambda", ["n"], ["*", "n", "n"]]],
  ["square", 5]
]
```

Result: `25`

## Working with Lists

Create and manipulate lists:

```json
[
  "do",
  ["def", "numbers", ["list", 1, 2, 3, 4, 5]],
  ["def", "doubled", ["map", ["lambda", ["x"], ["*", "x", 2]], "numbers"]],
  ["print", "Original:", "numbers"],
  ["print", "Doubled:", "doubled"]
]
```

Output:
```
Original: [1, 2, 3, 4, 5]
Doubled: [2, 4, 6, 8, 10]
```

## Conditional Logic

Use `if` for conditional expressions:

```json
[
  "do",
  ["def", "age", 25],
  ["if", [">=", "age", 18],
    ["print", "Adult"],
    ["print", "Minor"]]
]
```

## Higher-Order Functions

JSL excels at functional programming:

```json
[
  "do",
  ["def", "numbers", ["list", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
  ["def", "is-even", ["lambda", ["n"], ["=", ["mod", "n", 2], 0]]],
  ["def", "evens", ["filter", "is-even", "numbers"]],
  ["def", "sum", ["reduce", "+", "evens"]],
  ["print", "Even numbers:", "evens"],
  ["print", "Sum of evens:", "sum"]
]
```

Output:
```
Even numbers: [2, 4, 6, 8, 10]
Sum of evens: 30
```

## JSON Templates

Use `template` for dynamic JSON generation:

```json
[
  "do",
  ["def", "name", "Alice"],
  ["def", "age", 30],
  ["template", {
    "user": {"$": "name"},
    "profile": {
      "age": {"$": "age"},
      "adult": {"$": [">=", "age", 18]}
    }
  }]
]
```

Result:
```json
{
  "user": "Alice",
  "profile": {
    "age": 30,
    "adult": true
  }
}
```

## Running Programs

### Command Line

```bash
# Run from file
python -m jsl program.json

# Run from stdin
echo '["print", "Hello"]' | python -m jsl

# Interactive REPL
python -m jsl --repl
```

### Web Service

Start the JSL web service:

```bash
python -m jsl --service
```

Then send HTTP requests:

```bash
curl -X POST http://localhost:8000/eval \
  -H "Content-Type: application/json" \
  -d '["print", "Hello from API!"]'
```

### Python Integration

```python
import jsl

# Evaluate JSL expressions
result = jsl.eval_expr(["+", 1, 2, 3])
print(result)  # 6

# Serialize and deserialize closures
func = jsl.eval_expr(["lambda", ["x"], ["*", "x", 2]])
json_str = jsl.to_json(func)
restored_func = jsl.from_json(json_str)

# Use the restored function
result = jsl.eval_expr(["apply", restored_func, [5]])
print(result)  # 10
```

## Common Patterns

### Fibonacci Sequence

```json
[
  "do",
  ["def", "fib", 
   ["lambda", ["n"],
    ["if", ["<=", "n", 1],
     "n",
     ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]],
  ["map", "fib", ["list", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
]
```

### Data Processing Pipeline

```json
[
  "do",
  ["def", "data", [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "SF"},
    {"name": "Charlie", "age": 35, "city": "NYC"}
  ]],
  ["def", "adults-in-nyc", 
   ["filter", 
    ["lambda", ["person"], 
     ["and", 
      [">=", ["get", "person", "age"], 18],
      ["=", ["get", "person", "city"], "NYC"]]],
    "data"]],
  ["map", ["lambda", ["p"], ["get", "p", "name"]], "adults-in-nyc"]
]
```

Result: `["Alice", "Charlie"]`

## Next Steps

- **[Basic Examples](examples.md)** - More complete examples
- **[Language Guide](../language/overview.md)** - Complete syntax reference
- **[Tutorials](../tutorials/first-program.md)** - Step-by-step learning
