# Stack Evaluator API Reference

The stack evaluator module (`jsl.stack_evaluator`) provides a stack-based virtual machine for executing JSL programs compiled to JPN (JSL Postfix Notation).

## Overview

The stack evaluator offers an alternative execution model to the recursive evaluator:
- **Linear execution** of postfix instructions
- **Natural resumption** support for distributed computing
- **Efficient resource tracking** with step counting
- **Dict-based closures** for JSON serialization

## Classes

### `StackEvaluator`

The main stack-based evaluator class:

::: jsl.stack_evaluator.StackEvaluator
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

### `StackState`

Represents the state of the stack machine for resumption:

::: jsl.stack_evaluator.StackState
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

## Usage Examples

### Basic Evaluation

```python
from jsl.stack_evaluator import StackEvaluator
from jsl.compiler import compile_to_postfix

# Create evaluator
evaluator = StackEvaluator()

# Compile S-expression to JPN
expr = ["+", 1, 2, 3]
jpn = compile_to_postfix(expr)  # [1, 2, 3, 3, "+"]

# Evaluate
result = evaluator.eval(jpn)
print(result)  # Output: 6
```

### Resumable Execution

```python
from jsl.stack_evaluator import StackEvaluator
from jsl.compiler import compile_to_postfix

evaluator = StackEvaluator()

# Compile a complex expression
expr = ["*", ["+", 10, 20], ["-", 100, 50]]
jpn = compile_to_postfix(expr)

# Execute with step limit
result, state = evaluator.eval_partial(jpn, max_steps=3)

if state:  # Execution paused
    print(f"Paused at PC: {state.pc}")
    print(f"Stack: {state.stack}")
    
    # Resume execution
    final_result, _ = evaluator.eval_partial(jpn, state=state)
    print(f"Result: {final_result}")  # Output: 1500
```

### Working with Closures

```python
from jsl.stack_evaluator import StackEvaluator
from jsl.compiler import compile_to_postfix

evaluator = StackEvaluator()

# Define a function
program = [
    "do",
    ["def", "square", ["lambda", ["x"], ["*", "x", "x"]]],
    ["square", 5]
]

jpn = compile_to_postfix(program)
result = evaluator.eval(jpn)
print(result)  # Output: 25

# The closure is stored as a dict
closure = evaluator.env.get("square")
print(closure["type"])    # "closure"
print(closure["params"])  # ["x"]
print(closure["body"])    # ["*", "x", "x"]
```

## JPN Instruction Set

The stack evaluator processes these instruction types:

### Values
- **Literals**: Numbers, strings, booleans, null, lists, dicts push themselves
- **Variables**: String identifiers trigger environment lookup

### Operators
- **N-ary operators**: Preceded by arity count (e.g., `3, "+"` for 3-argument addition)
- **Built-in functions**: Called like operators with arity

### Special Forms
- **`Opcode.SPECIAL_FORM`**: Marks special form instructions
- **`Opcode.JUMP`**: Conditional/unconditional jumps
- **`Opcode.JUMP_IF_FALSE`**: Jump if top of stack is false
- **`Opcode.LAMBDA`**: Create closure from body and params

## Stack Machine Architecture

### Execution Model

1. **Program Counter (PC)**: Points to current instruction
2. **Operand Stack**: Holds intermediate values
3. **Environment**: Variable bindings (dict-based)
4. **Call Stack**: For function calls (managed internally)

### Instruction Processing

```python
# Simplified execution loop
while pc < len(program):
    instruction = program[pc]
    
    if isinstance(instruction, (int, float, str, bool, type(None))):
        stack.append(instruction)
    elif instruction in operators:
        arity = program[pc - 1]
        args = [stack.pop() for _ in range(arity)]
        result = operators[instruction](*reversed(args))
        stack.append(result)
    
    pc += 1
```

## Differences from Recursive Evaluator

| Feature | Recursive Evaluator | Stack Evaluator |
|---------|-------------------|-----------------|
| Execution | Tree walking | Linear instruction stream |
| Closures | `Closure` objects | Dict representations |
| Resumption | Difficult | Natural with `StackState` |
| Performance | Good for small programs | Better for large programs |
| Debugging | Natural call stack | Requires PC tracking |

## Integration with JSLRunner

The `JSLRunner` can use either evaluator:

```python
from jsl.runner import JSLRunner

# Use stack evaluator (default)
runner_stack = JSLRunner(use_recursive_evaluator=False)

# Use recursive evaluator
runner_recursive = JSLRunner(use_recursive_evaluator=True)

# Both produce identical results
result1 = runner_stack.execute(["+", 1, 2, 3])
result2 = runner_recursive.execute(["+", 1, 2, 3])
assert result1 == result2  # True
```