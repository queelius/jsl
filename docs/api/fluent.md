# Fluent Python API

## Overview

The JSL Fluent Python API provides a Pythonic way to **build** JSL expressions. It is designed for developers who want to leverage JSL's power within a Python environment, combining Python's scripting capabilities with JSL's safe, functional, and serializable core.

The Fluent API does not execute code; it constructs the JSL data structures (lists and dictionaries) that you can then pass to an execution engine like the **[JSLRunner](./runner.md)**.

### Key Design Principles

1. **Clear Separation of Concerns**: The Fluent API builds expressions, JSLRunner executes them
2. **Immutability**: Every operation returns a new expression object
3. **Type Safety**: Explicit methods for creating literals vs variables
4. **Pythonic Interface**: Uses operator overloading and method chaining for natural syntax

## Core Concepts

1. **Pythonic Expression Building**: Construct complex JSL expressions using method chaining and operator overloading.
2. **Immutability**: Every operation on a fluent object returns a new object representing a new JSL expression.
3. **Lazy Construction**: Expressions are built as Python objects; they are not evaluated until passed to a runner.

## Getting Started: `E` and `V`

The two fundamental building blocks are `E` (Expression builder) and `V` (Variable builder).

```python
from jsl.fluent import E, V
import jsl

# Use the Expression builder E for function calls
expr_e = E.add(1, 2, 3)
# Represents the JSL: ["+", 1, 2, 3]

# Use the Variable builder V for variable references
expr_v = V.x + V.y
# Represents the JSL: ["+", "x", "y"]

# Use the JSLRunner to execute the expression
runner = jsl.JSLRunner()
runner.define("x", 10)
runner.define("y", 20)
print(runner.execute(expr_v.to_jsl())) # Output: 30
```

## String Literals vs Variables

JSL distinguishes between string literals and variable names. The Fluent API provides explicit methods to handle this:

```python
from jsl.fluent import E, V, literal

# Variable reference (will lookup "name" in environment)
var_ref = V.name
# Represents: "name"

# String literal (the actual string "hello")
str_lit = E.string("hello")
# Represents: "@hello"

# Alternative using literal() function
str_lit2 = literal("hello")
# Also represents: "@hello"

# In expressions
greeting = E.str_concat(E.string("Hello "), V.name)
# Represents: ["str-concat", "@Hello ", "name"]

# The runner distinguishes between them
runner = jsl.JSLRunner()
runner.define("name", "World")
print(runner.execute(greeting.to_jsl()))  # Output: "Hello World"
```

## Method Chaining and Pipelines

For linear sequences of operations, the fluent API supports method chaining, creating a clean, readable pipeline.

```python
from jsl.fluent import E, V
import jsl

# Define a pipeline using method chaining
pipeline = E.list(1, 2, 3, 4, 5, 6).map(
    E.lambda_("n", V.n * 2)
).filter(
    E.lambda_("n", V.n > 5)
)

# The `pipeline` object now represents a complex, nested JSL expression.
# Pass it to a runner to execute it.
runner = jsl.JSLRunner()
print(runner.execute(pipeline.to_jsl())) # Output: [6, 8, 10, 12]
```

## Complex Expressions

The Fluent API supports building arbitrarily complex JSL expressions:

```python
from jsl.fluent import E, V

# Conditional with let binding
expr = E.let(
    {"threshold": 10},
    E.if_(
        V.value > V.threshold,
        E.string("high"),
        E.string("low")
    )
)

# Nested function definitions
calculator = E.do(
    E.def_("add", E.lambda_(["a", "b"], V.a + V.b)),
    E.def_("multiply", E.lambda_(["a", "b"], V.a * V.b)),
    E.def_("calculate", E.lambda_(["x", "y"],
        E.if_(
            V.operation == E.string("add"),
            E.add(V.x, V.y),
            E.multiply(V.x, V.y)
        )
    ))
)
```

## API Reference

### Expression Builder (`E`)

The expression builder provides methods for all JSL functions:

- **Arithmetic**: `add()`, `subtract()`, `multiply()`, `divide()`
- **Comparison**: `equals()`, `less_than()`, `greater_than()`
- **Logic**: `if_()`, `and_()`, `or_()`, `not_()`
- **Data**: `list()`, `object()`, `string()`, `quote()`
- **Functions**: `lambda_()`, `def_()`, `let()`, `do()`
- **Collections**: `map()`, `filter()`, `reduce()`, `get()`
- **Strings**: `str_concat()`, `str_split()`, `str_upper()`, `str_lower()`
- **Host**: `host()` for host interactions

### Variable Builder (`V`)

Access variables using attribute syntax:

```python
V.variable_name  # Simple variable
V["complex-name"]  # Variables with special characters
```

### Utility Functions

- `literal(value)`: Create a literal value (string, list, or dict)
- `var(name)`: Create a variable reference
- `expr(jsl)`: Wrap existing JSL in fluent interface
- `pipeline(initial)`: Create a pipeline for chaining operations

## Integration with JSLRunner

The Fluent API is designed to work seamlessly with JSLRunner:

```python
from jsl.fluent import E, V
from jsl.runner import JSLRunner

# Create runner with security settings
runner = JSLRunner(security={"sandbox_mode": True})

# Build complex expression with Fluent API
expr = E.let(
    {"data": E.list(1, 2, 3, 4, 5)},
    V.data.map(E.lambda_("x", V.x * V.x)).reduce(
        E.lambda_(["acc", "x"], V.acc + V.x),
        0
    )
)

# Execute the expression
result = runner.execute(expr.to_jsl())
print(result)  # Output: 55 (sum of squares)
```

## Best Practices

1. **Use `E.string()` or `literal()` for string literals**, not raw strings
2. **Use `V` for variable references**, not quoted strings
3. **Call `.to_jsl()` when passing to JSLRunner**
4. **Leverage method chaining** for readable pipelines
5. **Use explicit methods** like `E.if_()` over dynamic `E.if()`

