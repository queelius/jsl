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
