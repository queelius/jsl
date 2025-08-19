# Compiler API Reference

The compiler module (`jsl.compiler`) transforms JSL S-expressions into JPN (JSL Postfix Notation) for execution by the stack evaluator.

## Overview

The compiler performs several transformations:
- **Infix to postfix** conversion for operators
- **Special form** compilation with control flow
- **Arity tracking** for n-ary operations
- **Optimization** of common patterns

## Functions

### `compile_to_postfix`

The main compilation function:

::: jsl.compiler.compile_to_postfix
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

### `decompile_from_postfix`

Reconstructs S-expressions from JPN (for debugging):

::: jsl.compiler.decompile_from_postfix
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

## Compilation Examples

### Simple Expressions

```python
from jsl.compiler import compile_to_postfix

# Arithmetic
expr = ["+", 1, 2, 3]
jpn = compile_to_postfix(expr)
print(jpn)  # [1, 2, 3, 3, "+"]

# Nested expressions
expr = ["*", ["+", 2, 3], 4]
jpn = compile_to_postfix(expr)
print(jpn)  # [2, 3, 2, "+", 4, 2, "*"]
```

### Special Forms

```python
from jsl.compiler import compile_to_postfix
from jsl.stack_special_forms import Opcode

# If expression
expr = ["if", ["=", "x", 5], "yes", "no"]
jpn = compile_to_postfix(expr)
# Result includes jump instructions for control flow

# Lambda expression
expr = ["lambda", ["x", "y"], ["+", "x", "y"]]
jpn = compile_to_postfix(expr)
# Result: [["x", "y"], ["+", "x", "y"], Opcode.SPECIAL_FORM, "lambda"]
```

### Function Calls

```python
from jsl.compiler import compile_to_postfix

# Simple function call
expr = ["square", 5]
jpn = compile_to_postfix(expr)
print(jpn)  # [5, 1, "square"]

# Multiple arguments
expr = ["add", 1, 2, 3]
jpn = compile_to_postfix(expr)
print(jpn)  # [1, 2, 3, 3, "add"]
```

## JPN Format

### Instruction Types

1. **Literals**: Push themselves onto stack
   ```python
   42           # Push number
   "hello"      # Push string
   True         # Push boolean
   None         # Push null
   ```

2. **Operators with Arity**: Arity precedes operator
   ```python
   [1, 2, 3, 3, "+"]     # Add 3 numbers
   [5, 1, "square"]      # Call square with 1 argument
   ```

3. **Special Forms**: Use `Opcode.SPECIAL_FORM` marker
   ```python
   [condition, Opcode.SPECIAL_FORM, "if", ...]
   [params, body, Opcode.SPECIAL_FORM, "lambda"]
   ```

4. **Control Flow**: Jump instructions
   ```python
   [Opcode.JUMP_IF_FALSE, offset]  # Conditional jump
   [Opcode.JUMP, offset]           # Unconditional jump
   ```

### Compilation Rules

| S-Expression | JPN Output | Notes |
|-------------|------------|-------|
| `42` | `[42]` | Literals compile to themselves |
| `"x"` | `["x"]` | Variables compile to strings |
| `["+", 1, 2]` | `[1, 2, 2, "+"]` | Args, arity, operator |
| `["if", c, t, f]` | Complex with jumps | Control flow compilation |
| `["lambda", params, body]` | `[params, body, Opcode.SPECIAL_FORM, "lambda"]` | Closure creation |

## Decompilation

For debugging, JPN can be decompiled back to S-expressions:

```python
from jsl.compiler import compile_to_postfix, decompile_from_postfix

# Original expression
original = ["*", ["+", 1, 2], 3]

# Compile to JPN
jpn = compile_to_postfix(original)
print(jpn)  # [1, 2, 2, "+", 3, 2, "*"]

# Decompile back
reconstructed = decompile_from_postfix(jpn)
print(reconstructed)  # ["*", ["+", 1, 2], 3]

assert original == reconstructed  # True (for most expressions)
```

## Advanced Topics

### Optimization Opportunities

The compiler could optimize common patterns:
- **Constant folding**: Evaluate constant expressions at compile time
- **Dead code elimination**: Remove unreachable code after `if`
- **Tail call optimization**: Convert tail calls to jumps

### Custom Operators

Adding new operators requires:
1. Add to prelude with known arity
2. Compiler automatically handles them
3. No special compilation logic needed

```python
# In prelude
def custom_op(a, b, c):
    return a + b * c

# Register in prelude
prelude["my-op"] = custom_op

# Automatically compiles correctly
expr = ["my-op", 1, 2, 3]
jpn = compile_to_postfix(expr)  # [1, 2, 3, 3, "my-op"]
```

## Integration with Stack Evaluator

```python
from jsl.compiler import compile_to_postfix
from jsl.stack_evaluator import StackEvaluator

# Compile and execute
expr = ["do",
    ["def", "x", 10],
    ["*", "x", 2]
]

jpn = compile_to_postfix(expr)
evaluator = StackEvaluator()
result = evaluator.eval(jpn)
print(result)  # 20
```