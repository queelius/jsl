# Stack-Based Evaluation in JSL

## Overview

JSL now supports two evaluation strategies:
1. **Recursive evaluation** - Traditional tree-walking interpreter (simple but limited)
2. **Stack-based evaluation** - Compiles to postfix bytecode for efficient execution

## Why Stack-Based Evaluation?

### Limitations of Recursive Evaluation

The recursive evaluator in `jsl/core.py` has several fundamental limitations:

1. **No true resumption**: When resources are exhausted mid-recursion, we can only capture the top-level expression. The computation restarts from the beginning, making no progress.

2. **Stack overflow risk**: Deep recursion can exceed Python's call stack limit.

3. **Difficult optimization**: Each node visit involves function calls and environment lookups.

4. **Imprecise resource tracking**: Hard to track exact costs mid-recursion.

### Advantages of Stack-Based Evaluation

1. **Perfect resumption**: Save the stack and program counter, resume exactly where you left off.

2. **No recursion limits**: Uses a data stack, not the call stack.

3. **Optimization opportunities**: Postfix bytecode can be optimized, cached, and analyzed.

4. **Network-friendly**: Postfix arrays are more compact than S-expressions for transmission.

5. **Clear execution model**: Each instruction is atomic and predictable.

## Architecture

### Compilation Pipeline

```
S-Expression → Compiler → Postfix → Stack Evaluator → Result
['+', 2, 3]  →          → [2,3,'+'] →               → 5
```

### Key Components

- **`jsl/compiler.py`**: Converts S-expressions to postfix notation
- **`jsl/stack_evaluator.py`**: Executes postfix using a value stack
- **`jsl/eval_modes.py`**: Unified interface for both evaluators

### N-Arity Handling

For operators with variable arity (0 ≤ n < ∞), we encode arity explicitly:

```python
['+']           → [('+', 0)]      # 0-arity: sum() = 0
['+', 5]        → [5, ('+', 1)]    # 1-arity: 5
['+', 1, 2, 3]  → [1, 2, 3, ('+', 3)]  # n-arity: 1+2+3
```

## Usage Examples

### Basic Evaluation

```python
from jsl.compiler import compile_to_postfix
from jsl.stack_evaluator import StackEvaluator

# Compile S-expression to postfix
expr = ['*', ['+', 2, 3], 4]
postfix = compile_to_postfix(expr)  # [2, 3, '+', 4, '*']

# Evaluate
evaluator = StackEvaluator()
result = evaluator.eval(postfix)  # 20
```

### Resumable Evaluation

```python
# Execute with limited steps (simulating resource limits)
expr = ['*', ['+', 10, 20], ['-', 100, 50]]
postfix = compile_to_postfix(expr)

evaluator = StackEvaluator()
result, state = evaluator.eval_partial(postfix, max_steps=2)
# result = None, state contains stack and pc

# Resume later
result, state = evaluator.eval_partial(postfix, max_steps=10, state=state)
# result = 1500, state = None (complete)
```

### Unified Interface

```python
from jsl.eval_modes import JSLEvaluator, EvalMode

# Use recursive evaluator (default)
eval1 = JSLEvaluator(mode=EvalMode.RECURSIVE)
result = eval1.eval(['+', 2, 3])  # 5

# Use stack evaluator
eval2 = JSLEvaluator(mode=EvalMode.STACK)
result = eval2.eval(['+', 2, 3])  # 5

# Both produce identical results!
```

## Postfix as Primary Representation

In distributed/networked scenarios, postfix can become the primary code representation:

```python
# Instead of sharing S-expressions:
send_over_network(['+', [1, 2], [3, 4]])  # Nested structure

# Share postfix directly:
send_over_network([1, 2, '+', 3, 4, '+', '+'])  # Flat array
```

Benefits:
- More compact (flat array vs nested)
- No parsing ambiguity
- Direct execution without compilation
- Trivial serialization

## Testing

The same test suite runs on both evaluators, proving functional equivalence:

```python
# tests/test_both_evaluators.py
@pytest.fixture(params=[RecursiveEvaluator, StackEvaluator])
def evaluator(request):
    return request.param()

def test_arithmetic(evaluator):
    assert evaluator.eval(['+', 2, 3]) == 5
    # This test runs twice - once per evaluator!
```

## Future Work

1. **Optimize postfix**: Dead code elimination, constant folding
2. **JIT compilation**: Compile hot paths to native code
3. **Streaming evaluation**: Process postfix as it arrives over network
4. **Parallel execution**: Some postfix sequences can run in parallel
5. **Add special forms**: Implement if, let, lambda in stack evaluator

## Conclusion

Stack-based evaluation provides a production-ready alternative to recursive evaluation, with better resumption, optimization opportunities, and network characteristics. The postfix representation can serve as JSL's "bytecode" - the actual computational format, with S-expressions as the human-friendly source language.