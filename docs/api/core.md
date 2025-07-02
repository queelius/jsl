# Core Module API Reference

The core module (`jsl.core`) provides the fundamental data structures and environment management for JSL.

## Classes

### `Env`

The environment class manages variable bindings and scope chains.

::: jsl.core.Env
    handler: python
    options:
      show_root_heading: yes
      show_source: yes
      
### `Closure`

Represents a user-defined function with captured lexical environment.

::: jsl.core.Closure
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

## Global State

### `prelude`

The global prelude environment containing all built-in functions.

```python
from jsl.core import prelude

# Access built-in functions
plus_func = prelude.get("+")
map_func = prelude.get("map")
```

## Environment Management

The core module handles environment chaining and variable resolution:

```python
from jsl.core import Env

# Create a new environment
env = Env({"x": 10, "y": 20})

# Create child environment  
child_env = env.extend({"z": 30})

# Variable resolution follows the chain
print(child_env.get("x"))  # 10 (from parent)
print(child_env.get("z"))  # 30 (from child)
```

## Closure Creation

Closures capture their defining environment:

```python
from jsl.core import Closure, Env

# Create environment
env = Env({"multiplier": 3})

# Create closure that captures the environment
closure = Closure(
    params=["x"],
    body=["*", "multiplier", "x"],
    env=env
)

# The closure remembers the 'multiplier' value
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

# Core Data Structures

## Overview

The `jsl.core` module provides the fundamental data structures that represent the state of a JSL program: `Env` for environments and `Closure` for functions. These are the building blocks used by the **[Evaluator](./evaluator.md)** and managed by the **[JSLRunner](./runner.md)**.

## `Env`

The `Env` class implements the JSL environment, a dictionary-like object that maps variable names to values and links to a parent environment to form a scope chain.

### Key Concepts

-   **Scope Chain:** When looking up a variable, if it's not found in the current `Env`, the search continues up to its parent, and so on, until the root `prelude` is reached.
-   **Immutability:** Methods like `extend` create a *new* child environment rather than modifying the parent, preserving functional purity.

```python
from jsl.core import Env

# Create a new environment
env = Env({"x": 10, "y": 20})

# Create a child environment that inherits from the parent
child_env = env.extend({"z": 30})

# Variable resolution follows the chain
# print(child_env.get("x")) -> 10 (from parent)
# print(child_env.get("z")) -> 30 (from child)
```

## `Closure`

The `Closure` class represents a JSL function. It packages the function's code (parameters and body) with a reference to the environment in which it was defined. This "closing over" of the environment is what allows lexical scoping to work.

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
```

## `prelude`

A global, read-only instance of `Env` that contains all the JSL built-in functions (e.g., `+`, `map`, `get`). It serves as the ultimate parent of all other environments.
