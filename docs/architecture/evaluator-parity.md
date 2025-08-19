# Evaluator Parity: Dual Implementation Architecture

This document describes JSL's dual evaluator architecture and the comprehensive work done to ensure both evaluators have identical semantics.

## Overview

JSL implements two evaluators with different execution strategies but identical language semantics:

1. **Recursive Evaluator** - Traditional tree-walking interpreter
2. **Stack Evaluator** - Compiles to postfix notation for stack-based execution

## Why Two Evaluators?

### Recursive Evaluator
- **Purpose**: Reference implementation and development
- **Benefits**:
  - Simple, traditional tree-walking approach
  - Natural recursion for nested expressions  
  - Easy to understand and debug
  - Good for development and testing
- **Implementation**: Uses `Closure` class objects

### Stack Evaluator  
- **Purpose**: Production implementation with advanced features
- **Benefits**:
  - Compiles to JPN (JSL Postfix Notation)
  - **Resumable execution** (can pause/restore state)
  - **Network-native** (all state is JSON-serializable)
  - No call stack depth limitations
  - Better for distributed systems
- **Implementation**: Uses dict closures (JSON-serializable)

## Parity Achievement

### Test Coverage
- **168 unified tests** - Each test runs against both evaluators
- **100% pass rate** - Identical inputs produce identical outputs
- **30 runner integration tests** - All pass with both evaluators

### Language Features

#### Core Operations
- ✅ Arithmetic: `+`, `-`, `*`, `/`, `%` with proper identity elements
- ✅ Comparison: `=`, `!=`, `<`, `>`, `<=`, `>=`  
- ✅ Logical: `and`, `or`, `not` with proper identity elements
- ✅ Lists: `list`, `cons`, `first`, `rest`, `length`, `append`

#### Special Forms
- ✅ `if` - Conditional evaluation
- ✅ `let` - Local bindings (standardized format: `["let", [[bindings]], body]`)
- ✅ `lambda` - Function creation
- ✅ `def` - Global definitions
- ✅ `do` - Sequential evaluation
- ✅ `quote` / `@` - Prevent evaluation
- ✅ `try` - Error handling
- ✅ `host` - Side effects

#### Advanced Features
- ✅ Function application: `[["lambda", ["x"], body], arg]`
- ✅ Recursive functions (fibonacci, factorial, etc.)
- ✅ Higher-order functions (map, filter, reduce)
- ✅ Closures with proper lexical scoping
- ✅ Error handling with try/catch

## Implementation Details

### Function Application Design

When the first element of a list is itself an expression (not just a string), it's evaluated to get a function:

```json
[["lambda", ["x"], ["*", "x", 2]], 5]
```

The compiler detects this pattern and generates an `__apply__` operation:
```
[5, <lambda-closure>, 1, "__apply__"]
```

### Closure Representations

**Recursive Evaluator:**
```python
Closure(params=["x"], body=["*", "x", 2], env=Env(...))
```

**Stack Evaluator:**
```json
{
  "type": "closure",
  "params": ["x"],
  "body": ["*", "x", 2],
  "env": {...}
}
```

### Identity Elements

Operations return mathematically correct identity elements for 0-arity calls:

| Operation | 0-arity Result | Rationale |
|-----------|---------------|-----------|
| `(+)` | 0 | Addition identity |
| `(*)` | 1 | Multiplication identity |
| `(-)` | 0 | Consistent with addition |
| `(and)` | true | All of empty set |
| `(or)` | false | Any of empty set |
| `(min)` | +∞ | Upper bound |
| `(max)` | -∞ | Lower bound |

### N-ary Subtraction

Subtraction follows left-associative semantics:
- `(-)` → 0 (identity)
- `(- x)` → -x (negation)
- `(- a b c)` → ((a - b) - c) (left-associative)

## Testing Strategy

### Unified Test Suite

The `tests/test_unified_evaluators.py` file contains comprehensive tests that run against both evaluators:

```python
@pytest.fixture(params=[
    RecursiveEvaluatorAdapter(),
    StackEvaluatorAdapter(),
    RunnerAdapter(use_recursive=True),
    RunnerAdapter(use_recursive=False),
])
def evaluator(request):
    return request.param
```

Each test is automatically run 4 times to ensure consistency across all execution paths.

### Test Categories

1. **Literals** - Numbers, booleans, null, strings
2. **Arithmetic** - All operations with various arities
3. **Comparison** - All comparison operators
4. **Logical** - Boolean operations
5. **Lists** - Creation and manipulation
6. **Special Forms** - All language constructs
7. **Variables** - Definition and lookup
8. **Complex Expressions** - Recursive functions, nested expressions
9. **Edge Cases** - Empty expressions, deeply nested structures

## Runner Integration

The `JSLRunner` class provides a unified interface that works seamlessly with either evaluator:

```python
# Use recursive evaluator
runner = JSLRunner(use_recursive_evaluator=True)

# Use stack evaluator (default)
runner = JSLRunner(use_recursive_evaluator=False)

# Both produce identical results
result = runner.execute(["fibonacci", 10])
```

### Environment Management

Both evaluators properly handle:
- Environment extension for lexical scoping
- Context managers for isolated execution
- Variable definition and lookup
- Host command dispatch

## Benefits of Dual Implementation

1. **Validation** - Cross-checking ensures correctness
2. **Flexibility** - Choose evaluator based on needs
3. **Documentation** - Recursive serves as readable specification
4. **Innovation** - Stack evaluator adds advanced features without breaking compatibility
5. **Testing** - Natural A/B testing of implementations

## Future Work

While parity is complete, the stack evaluator can add features impossible with recursive evaluation:

- Execution state serialization
- Network distribution of computation
- Time-sliced execution
- Pauseable/resumable workflows
- Checkpoint/restore capabilities

## Conclusion

JSL's dual evaluator architecture provides both simplicity and power while maintaining complete semantic consistency. The comprehensive test suite ensures that any program will produce identical results regardless of which evaluator is used, giving users confidence to choose the evaluator that best fits their needs.