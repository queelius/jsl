# Runner API

## Overview

The JSL Runner API provides the core execution engine for JSL programs, handling evaluation, environment management, and host interaction coordination.

## Core Classes

::: jsl.runner
    options:
      show_root_heading: false
      show_source: true
      members:
        - JSLRunner
        - ExecutionContext
        - JSLRuntimeError
        - JSLSyntaxError

## Usage Examples

### Basic Program Execution

```python
from jsl.runner import JSLRunner

# Create runner instance
runner = JSLRunner()

# Execute simple expression
result = runner.execute(["+", 1, 2])
print(result)  # Output: 3

# Execute with variables
runner.define("x", 10)
result = runner.execute(["*", "x", 2])
print(result)  # Output: 20
```

### Environment Management

```python
# Create isolated environment
with runner.new_environment() as env:
    env.define("temp_var", 42)
    result = env.execute(["*", "temp_var", 2])
    print(result)  # Output: 84
# temp_var is no longer accessible
```

### Closure Execution

```python
# Define function
runner.execute(["def", "square", ["lambda", ["x"], ["*", "x", "x"]]])

# Call function
result = runner.execute(["square", 5])
print(result)  # Output: 25

# Access function object
square_fn = runner.get_variable("square")
print(square_fn.params)  # Output: ["x"]
print(square_fn.body)    # Output: ["*", "x", "x"]
```

### Host Interaction

```python
from jsl.runner import JSLRunner
from jsl.jhip import FileHandler

# Configure with host handlers
runner = JSLRunner()
runner.add_host_handler("file", FileHandler())

# Execute host interaction
result = runner.execute(["host", "file/read", "/tmp/data.txt"])
```

### Error Handling

```python
try:
    result = runner.execute(["undefined_function", 1, 2])
except JSLRuntimeError as e:
    print(f"Runtime error: {e}")
except JSLSyntaxError as e:
    print(f"Syntax error: {e}")
```

## Configuration Options

### Runner Configuration

```python
config = {
    "max_recursion_depth": 1000,
    "max_steps": 10000,  # Limit evaluation steps (None for unlimited)
    "enable_debugging": True,
    "timeout_seconds": 30,
    "memory_limit_mb": 512
}

runner = JSLRunner(config=config)
```

### Security Settings

```python
# Restrict to specific host commands
security_config = {
    "allowed_host_commands": ["file/read", "time/now"]
}
runner = JSLRunner(security=security_config)

# Sandbox mode - blocks all host commands unless explicitly allowed
sandbox_config = {
    "sandbox_mode": True,
    "allowed_host_commands": ["safe_operation"]  # Only this is allowed
}
sandbox_runner = JSLRunner(security=sandbox_config)

# Complete sandbox - no host operations
strict_sandbox = JSLRunner(security={"sandbox_mode": True})
```

## Step Limiting and Resumption

JSL supports limiting the number of evaluation steps to prevent DOS attacks and enable fair resource allocation in distributed environments:

```python
# Create runner with step limit
runner = JSLRunner(config={"max_steps": 1000})

try:
    result = runner.execute(complex_expression)
except JSLRuntimeError as e:
    if "Step limit exceeded" in str(e):
        # Can resume with additional steps
        if hasattr(e, 'remaining_expr'):
            result = runner.resume(
                e.remaining_expr, 
                e.env, 
                additional_steps=500
            )
```

This enables:

- **DOS Prevention**: Limits computation to prevent infinite loops
- **Fair Resource Allocation**: In multi-tenant environments
- **Pauseable Computation**: Serialize and resume long-running tasks
- **Step Accounting**: Track resource usage per user/request

## Performance Monitoring

```python
# Enable performance tracking
runner.enable_profiling()

# Execute expressions
runner.execute('["*", 10, 20]')  # Parse from JSON
runner.execute(["+", 1, 2, 3])   # Direct expression

# Get performance metrics
stats = runner.get_performance_stats()
print(f"Total time: {stats['total_time_ms']}ms")
print(f"Parse time: {stats.get('parse_time_ms', 0)}ms")
print(f"Eval time: {stats['eval_time_ms']}ms")
print(f"Call count: {stats['call_count']}")
print(f"Errors: {stats.get('error_count', 0)}")

# Reset stats
runner.reset_performance_stats()

# Disable profiling
runner.disable_profiling()
```
