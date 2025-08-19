# Core Module API Reference

The core module (`jsl.core`) provides the fundamental data structures, evaluator, and environment management for JSL.

## Overview

The `jsl.core` module provides the fundamental data structures that represent the state of a JSL program: `Env` for environments and `Closure` for functions. These are the building blocks used by the **[Evaluator](./evaluator.md)** and managed by the **[JSLRunner](./runner.md)**.

## Classes

### `Env`

The environment class manages variable bindings and scope chains.

::: jsl.core.Env
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

#### Key Concepts

-   **Scope Chain:** When looking up a variable, if it's not found in the current `Env`, the search continues up to its parent, and so on, until the root `prelude` is reached.
-   **Immutability:** Methods like `extend` create a *new* child environment rather than modifying the parent, preserving functional purity.

```python
from jsl.core import Env

# Create a new environment
env = Env({"x": 10, "y": 20})

# Create a child environment that inherits from the parent
child_env = env.extend({"z": 30})

# Variable resolution follows the chain
print(child_env.get("x"))  # 10 (from parent)
print(child_env.get("z"))  # 30 (from child)
```
      
### `Closure`

Represents a user-defined function with captured lexical environment.

::: jsl.core.Closure
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

Closures capture their defining environment:

```python
from jsl.core import Closure, Env

# Create an environment that the closure will capture
env = Env({"multiplier": 3})

# Create a closure that captures the 'multiplier' variable from its environment
closure = Closure(
    params=["x"],
    body=["*", "multiplier", "x"],
    env=env
)

# The closure remembers the 'multiplier' value
```

### `Evaluator`

The main JSL expression evaluator:

::: jsl.core.Evaluator
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

### `HostDispatcher`

Manages host interactions for side effects:

::: jsl.core.HostDispatcher
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

## Resource Management

### `ResourceBudget`

::: jsl.core.ResourceBudget
    handler: python
    options:
      show_root_heading: yes
      show_source: no

### `ResourceLimits`

::: jsl.core.ResourceLimits
    handler: python
    options:
      show_root_heading: yes
      show_source: no

### `GasCost`

::: jsl.core.GasCost
    handler: python
    options:
      show_root_heading: yes
      show_source: no

## Error Types

### `JSLError`

::: jsl.core.JSLError
    handler: python
    options:
      show_root_heading: yes
      show_source: no

### `SymbolNotFoundError`

::: jsl.core.SymbolNotFoundError
    handler: python
    options:
      show_root_heading: yes
      show_source: no

### `JSLTypeError`

::: jsl.core.JSLTypeError
    handler: python
    options:
      show_root_heading: yes
      show_source: no

## Global State

### `prelude`

The global prelude environment containing all built-in functions. A global, read-only instance of `Env` that contains all the JSL built-in functions (e.g., `+`, `map`, `get`). It serves as the ultimate parent of all other environments.

```python
from jsl.core import prelude

# Access built-in functions
plus_func = prelude.get("+")
map_func = prelude.get("map")
```

## Implementation Details

### Environment Chains

JSL uses environment chains for variable resolution:

1. **Current Environment**: Look for variable in current scope
2. **Parent Environment**: If not found, check parent scope  
3. **Continue Chain**: Repeat until variable found or chain ends
4. **Prelude Access**: All chains eventually reach the global prelude

### Closure Serialization

Closures are designed for safe serialization:

- **Parameters**: Always serializable (list of strings)
- **Body**: Always serializable (JSON expression)
- **Environment**: Only user-defined bindings are serialized
- **Prelude**: Built-in functions are reconstructed, not serialized

This ensures transmitted closures are safe and can be reconstructed in any compatible JSL runtime.

## Type Definitions

The module defines the following type aliases for clarity:

```python
from typing import Union, List, Dict, Any

JSLValue = Union[None, bool, int, float, str, List[Any], Dict[str, Any], Closure]
JSLExpression = Union[JSLValue, List[Any], Dict[str, Any]]
```

## Usage Examples

### Basic Evaluation

```python
from jsl.core import Evaluator, Env
from jsl.prelude import make_prelude

# Create evaluator and environment
evaluator = Evaluator()
env = make_prelude()

# Evaluate an expression
result = evaluator.eval(["+", 1, 2, 3], env)
print(result)  # Output: 6
```

### Working with Closures

```python
from jsl.core import Evaluator, Env
from jsl.prelude import make_prelude

evaluator = Evaluator()
env = make_prelude()

# Define a function
evaluator.eval(["def", "square", ["lambda", ["x"], ["*", "x", "x"]]], env)

# Call the function
result = evaluator.eval(["square", 5], env)
print(result)  # Output: 25
```

### Resource-Limited Execution

```python
from jsl.core import Evaluator, ResourceBudget, ResourceLimits

# Create evaluator with resource limits
limits = ResourceLimits(max_steps=1000, max_gas=10000)
budget = ResourceBudget(limits=limits)
evaluator = Evaluator(resource_budget=budget)

# Execute with resource tracking
result = evaluator.eval(expensive_computation, env)
print(f"Gas used: {budget.gas_used}")
print(f"Steps taken: {budget.steps_taken}")
```