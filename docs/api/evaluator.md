# Evaluator API Reference

The core module (`jsl.core`) contains the main evaluation engine for JSL expressions.

## Main Evaluator Class

### Evaluator

The main evaluator class for JSL expressions.

::: jsl.core.Evaluator
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

## Overview

The evaluator implements JSL's core evaluation semantics:

- **Expressions**: Everything in JSL is an expression that evaluates to a value
- **Environments**: Lexical scoping with nested environment chains  
- **Host Commands**: Bidirectional communication with the host system
- **Tail Call Optimization**: Efficient recursion handling

## Evaluation Rules

### Literals

- **Numbers**: `42`, `3.14` evaluate to themselves
- **Strings**: `"@hello"` evaluates to the literal string `"hello"`
- **Booleans**: `true`, `false` evaluate to themselves
- **null**: `null` evaluates to itself

### Variables

Variable references are resolved through the environment chain:

```json
["let", {"x": 42}, "x"]
```

### Special Forms

- **`let`**: Creates local bindings
- **`def`**: Defines variables in the current environment
- **`lambda`**: Creates function closures
- **`if`**: Conditional evaluation
- **`do`**: Sequential execution
- **`quote`**: Prevents evaluation
- **`host`**: Executes host commands

### Function Calls

Regular function calls use list syntax:

```json
["func", "arg1", "arg2"]
```

Where `func` evaluates to a callable (function or closure).

### Objects

Objects are evaluated by evaluating all key-value pairs:

```json
{"key": "value", "computed": ["add", 1, 2]}
```

Keys must evaluate to strings, values can be any JSL expression.

## Error Handling

The evaluator provides detailed error information including:

- Expression context
- Environment state
- Call stack trace
- Host command failures

## Security

The evaluator includes security measures:

- **Sandboxing**: Host commands are controlled by the dispatcher
- **Resource Limits**: Evaluation depth and memory usage controls
- **Safe Evaluation**: No access to Python internals by default

## Usage Examples

### Basic Evaluation

```python
from jsl.core import Evaluator, Env

evaluator = Evaluator()
env = Env()

# Evaluate a simple expression
result = evaluator.eval(["+", 1, 2], env)
print(result)  # 3
```

### With Variables

```python
# Define a variable
evaluator.eval(["def", "x", 42], env)

# Use the variable
result = evaluator.eval(["*", "x", 2], env)
print(result)  # 84
```

### Function Definition and Call

```python
# Define a function
evaluator.eval(["def", "square", ["lambda", ["x"], ["*", "x", "x"]]], env)

# Call the function
result = evaluator.eval(["square", 5], env)
print(result)  # 25
```

### Host Commands

```python
from jsl.core import HostDispatcher

# Create a dispatcher with custom commands
dispatcher = HostDispatcher()
dispatcher.register("print", lambda args: print(*args))

evaluator = Evaluator(host_dispatcher=dispatcher)

# Execute a host command
evaluator.eval(["host", "print", "@Hello, World!"], env)
```

## Performance Considerations

### Tail Call Optimization

The evaluator optimizes tail calls to prevent stack overflow in recursive functions.

### Memory Management

- Environments use reference counting
- Closures are garbage collected when no longer referenced
- Host commands can implement resource limits

### Caching

- Function closures cache their compiled form
- Environment lookups are optimized for common patterns
- Object evaluation caches key-value pairs when possible