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
        - Environment

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
    "enable_debugging": True,
    "timeout_seconds": 30,
    "memory_limit_mb": 512
}

runner = JSLRunner(config=config)
```

### Security Settings

```python
security_config = {
    "allowed_host_commands": ["file/read", "time/now"],
    "sandbox_mode": True,
    "restrict_network": True
}

runner = JSLRunner(security=security_config)
```

## Performance Monitoring

```python
# Enable performance tracking
runner.enable_profiling()

# Execute code
result = runner.execute(complex_expression)

# Get performance metrics
stats = runner.get_performance_stats()
print(f"Execution time: {stats['execution_time_ms']}ms")
print(f"Memory used: {stats['memory_used_mb']}MB")
```