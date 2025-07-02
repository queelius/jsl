# Fluent Python API

## Overview

The JSL Fluent Python API provides a Pythonic way to **build** JSL expressions. It is designed for developers who want to leverage JSL's power within a Python environment, combining Python's scripting capabilities with JSL's safe, functional, and serializable core.

The Fluent API does not execute code; it constructs the JSL data structures (lists and dictionaries) that you can then pass to an execution engine like the **[JSLRunner](./runner.md)**.

## Core Concepts

1.  **Pythonic Expression Building**: Construct complex JSL expressions using method chaining and operator overloading.
2.  **Immutability**: Every operation on a fluent object returns a new object representing a new JSL expression.
3.  **Lazy Construction**: Expressions are built as Python objects; they are not evaluated until passed to a runner.

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
print(runner.execute(expr_v)) # Output: 30
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
print(runner.execute(pipeline)) # Output: [6, 8, 10, 12]
```
