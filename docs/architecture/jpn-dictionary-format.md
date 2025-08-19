# JPN Dictionary Format Design

## Overview

This document defines the proper JPN (JSL Postfix Notation) format for dictionaries/objects in JSL. Currently, the compiler at `/home/spinoza/github/repos/jsl/jsl/compiler.py` handles dictionaries by pushing them as literal values, but this doesn't align with the postfix evaluation model and lacks the composability that other JSL constructs provide.

## Current State Analysis

### How JSL Currently Handles Dictionaries

1. **S-expression format**: Dictionaries are JSON objects with `@` prefixed string literals
   ```json
   {"@name": "@Alice", "@age": 30}
   ```

2. **Current compilation**: The compiler simply pushes dictionary literals as-is
   ```python
   elif isinstance(e, dict):
       # Dictionary literal - encode specially
       # For now, just push as-is (needs more thought for proper JPN)
       result.append(e)
   ```

3. **Stack evaluator**: Handles dictionaries as literals, consuming gas but not decomposing them
   ```python
   elif isinstance(instr, dict):
       # Push dict literal
       self._consume_gas(GasCost.DICT_CREATE + len(instr) * GasCost.DICT_PER_ITEM, "dict literal")
       stack.append(instr)
   ```

### Problems with Current Approach

1. **Inconsistent with postfix model**: Other constructs are decomposed into operations, but dictionaries remain monolithic
2. **No composability**: Cannot construct dictionaries dynamically in JPN without escaping to S-expressions
3. **Evaluation limitations**: Keys and values in dictionary literals must be pre-evaluated in S-expression form
4. **No intermediate representation**: Cannot pause/resume dictionary construction in partial evaluation

## Proposed JPN Dictionary Format

### Design Principles

1. **Consistency**: Dictionary operations should follow the same arity-then-operator pattern as other JPN operations
2. **Composability**: Should enable dynamic dictionary construction from stack values
3. **JSON compatibility**: Result must remain valid JSON for network transmission
4. **Stack-friendly**: Should work naturally with the stack evaluation model

### Core Dictionary Operations

#### 1. Dictionary Creation: `dict`

**Purpose**: Create a dictionary from key-value pairs on the stack

**S-expression equivalent**: 
```json
["dict", "key1", "value1", "key2", "value2"]
```

**JPN format**:
```json
["@key1", "value1", "@key2", "value2", 4, "dict"]
```

**Stack behavior**:
- Pops `arity` items from stack (must be even number)
- Pairs them as key-value (key1, value1, key2, value2, ...)
- Creates dictionary `{"key1": "value1", "key2": "value2"}`
- Pushes result dictionary onto stack

**Gas cost**: `GasCost.DICT_CREATE + (arity/2) * GasCost.DICT_PER_ITEM`

#### 2. Empty Dictionary: `dict-empty`

**Purpose**: Create an empty dictionary

**S-expression equivalent**:
```json
["dict-empty"]
```

**JPN format**:
```json
[0, "dict-empty"]
```

**Stack behavior**:
- Takes no arguments
- Pushes empty dictionary `{}` onto stack

### Dictionary Access Operations

These operations already exist in the prelude and work with both evaluators:

#### 3. Get Value: `get`
- **S-expr**: `["get", dict_expr, "key", default_value?]`
- **JPN**: `[dict_expr_jpn..., "@key", default_value?, arity, "get"]`

#### 4. Set Value: `set` 
- **S-expr**: `["set", dict_expr, "key", new_value]`
- **JPN**: `[dict_expr_jpn..., "@key", new_value, 3, "set"]`

#### 5. Check Key: `has`
- **S-expr**: `["has", dict_expr, "key"]`
- **JPN**: `[dict_expr_jpn..., "@key", 2, "has"]`

#### 6. Get Keys: `keys`
- **S-expr**: `["keys", dict_expr]`
- **JPN**: `[dict_expr_jpn..., 1, "keys"]`

#### 7. Get Values: `values`
- **S-expr**: `["values", dict_expr]`
- **JPN**: `[dict_expr_jpn..., 1, "values"]`

#### 8. Merge Dictionaries: `merge`
- **S-expr**: `["merge", dict1, dict2, dict3, ...]`
- **JPN**: `[dict1_jpn..., dict2_jpn..., dict3_jpn..., arity, "merge"]`

## Implementation Examples

### Example 1: Simple Dictionary Creation

**S-expression**:
```json
["dict", "@name", "@Alice", "@age", 30]
```

**JPN compilation**:
```json
["@name", "@Alice", 30, 4, "dict"]
```

**Stack trace**:
```
Initial: []
Push "@name": ["@name"]
Push "@Alice": ["@name", "@Alice"] 
Push 30: ["@name", "@Alice", 30]
Push 4: ["@name", "@Alice", 30, 4]
Execute "dict": [{"name": "Alice", "age": 30}]
```

### Example 2: Nested Dictionary with Dynamic Values

**S-expression**:
```json
["dict", 
  "@user", ["dict", "@name", "@Alice", "@age", 30],
  "@timestamp", ["+", 1000, 500]
]
```

**JPN compilation**:
```json
[
  "@user", 
  "@name", "@Alice", 30, 4, "dict",
  "@timestamp", 
  1000, 500, 2, "+",
  4, "dict"
]
```

**Stack trace**:
```
Push "@user": ["@user"]
Push "@name": ["@user", "@name"]
Push "@Alice": ["@user", "@name", "@Alice"]
Push 30: ["@user", "@name", "@Alice", 30]
Push 4: ["@user", "@name", "@Alice", 30, 4]
Execute "dict": ["@user", {"name": "Alice", "age": 30}]
Push "@timestamp": ["@user", {"name": "Alice", "age": 30}, "@timestamp"]
Push 1000: ["@user", {"name": "Alice", "age": 30}, "@timestamp", 1000]
Push 500: ["@user", {"name": "Alice", "age": 30}, "@timestamp", 1000, 500]
Push 2: ["@user", {"name": "Alice", "age": 30}, "@timestamp", 1000, 500, 2]
Execute "+": ["@user", {"name": "Alice", "age": 30}, "@timestamp", 1500]
Push 4: ["@user", {"name": "Alice", "age": 30}, "@timestamp", 1500, 4]
Execute "dict": [{"user": {"name": "Alice", "age": 30}, "timestamp": 1500}]
```

### Example 3: Dictionary Literals in Current Format

**Current S-expression literal**:
```json
{"@name": "@Alice", "@age": 30}
```

**Should compile to**:
```json
["@name", "@Alice", "@age", 30, 4, "dict"]
```

This maintains compatibility while providing the composability benefits of JPN.

## Migration Strategy

### Phase 1: Add Dictionary Operations to Stack Evaluator

1. Add `dict` and `dict-empty` operations to `StackEvaluator._setup_builtins()`
2. Update gas costs to handle these operations
3. Add comprehensive tests for the new operations

### Phase 2: Update Compiler

1. Modify `compile_to_postfix()` to handle dictionary literals by converting them to `dict` operations
2. Update `decompile_from_postfix()` to handle the new operations
3. Ensure round-trip compilation works correctly

### Phase 3: Update Prelude (if needed)

1. Add `dict` and `dict-empty` to prelude operations if they need to be available in S-expression form
2. Ensure all existing dictionary operations work with both evaluation modes

### Phase 4: Update Documentation and Examples

1. Update documentation to show JPN dictionary format
2. Provide migration examples for existing code
3. Update tutorials to demonstrate dictionary construction patterns

## Key Design Decisions and Rationale

### 1. Arity-First Convention

**Decision**: Use the established `[args..., arity, operator]` pattern for `dict` operation.

**Rationale**: 
- Maintains consistency with other JPN operations
- Enables the stack evaluator to know how many arguments to consume
- Supports variable-arity dictionary construction

### 2. Even Arity Requirement

**Decision**: The `dict` operation requires an even number of arguments (pairs of key-value).

**Rationale**:
- Dictionaries naturally require key-value pairs
- Provides clear error semantics for malformed input
- Simplifies implementation logic

### 3. String Key Requirement

**Decision**: Keys must be strings (enforced at evaluation time, not compilation time).

**Rationale**:
- Maintains JSON compatibility
- Consistent with JSL's current dictionary semantics
- Allows for dynamic key generation while preserving type safety

### 4. Separate Empty Dictionary Operation

**Decision**: Provide `dict-empty` as a separate zero-arity operation rather than allowing `[0, "dict"]`.

**Rationale**:
- Clearer semantics (empty dict vs. malformed dict)
- Follows pattern of other JSL operations like `list` vs empty list
- Enables specific gas costs for empty dictionary creation

### 5. Backward Compatibility

**Decision**: Convert existing dictionary literals to JPN format during compilation.

**Rationale**:
- Preserves existing JSL code
- Provides gradual migration path
- Maintains the same evaluation semantics

## Error Handling

### Invalid Arity
```json
["@key1", "value1", "@incomplete", 3, "dict"]  // Odd number of args
```
**Error**: "Dictionary requires even number of arguments for key-value pairs"

### Non-String Keys
```json
[123, "value1", "@key2", "value2", 4, "dict"]  // Numeric key
```
**Error**: "Dictionary key must be string, got number: 123"

### Stack Underflow
```json
[2, "dict"]  // Not enough values on stack
```
**Error**: "Stack underflow: dict needs 2 args, have 0"

## Performance Considerations

### Gas Costs
- **dict**: `GasCost.DICT_CREATE + (arity/2) * GasCost.DICT_PER_ITEM`
- **dict-empty**: `GasCost.DICT_CREATE`

### Memory Tracking
- Dictionary size is tracked for resource budgets
- Each key-value pair contributes to memory usage calculations

### Optimization Opportunities
1. **Pre-allocation**: Could pre-allocate dictionary size if known
2. **Literal optimization**: Simple literals could be optimized to avoid stack operations
3. **Common patterns**: Frequent dictionary patterns could be cached

## Testing Strategy

### Unit Tests Required

1. **Basic Operations**:
   - Create empty dictionary
   - Create dictionary with multiple key-value pairs
   - Verify correct gas consumption

2. **Error Cases**:
   - Odd number of arguments
   - Non-string keys
   - Stack underflow scenarios

3. **Integration Tests**:
   - Nested dictionaries
   - Dynamic key/value computation
   - Round-trip compilation/decompilation

4. **Compatibility Tests**:
   - Existing dictionary literal code still works
   - Both evaluators produce identical results
   - Serialization/deserialization works correctly

5. **Performance Tests**:
   - Large dictionaries
   - Deep nesting
   - Resource budget compliance

## Future Extensions

### Potential Enhancements

1. **Pattern Matching**: Dictionary destructuring in let bindings
2. **Computed Keys**: Support for computed key expressions in literals
3. **Dictionary Comprehensions**: Map-like operations for dictionary construction
4. **Immutable Updates**: Efficient nested dictionary updates

### Considerations for Network Usage

1. **Bandwidth**: JPN format may be more verbose than current literals for simple cases
2. **Caching**: Common dictionary patterns could be cached to reduce transmission size
3. **Compression**: Dictionary operations could be optimized for common network patterns

## Conclusion

This design provides a consistent, composable approach to dictionary handling in JPN while maintaining backward compatibility with existing JSL code. The postfix representation enables:

- **Resumable evaluation**: Dictionary construction can be paused and resumed
- **Dynamic composition**: Dictionaries can be built from computed values
- **Resource tracking**: Fine-grained gas and memory accounting
- **Network efficiency**: Structured representation suitable for distributed execution

The implementation should be straightforward given the existing infrastructure, and the migration path provides a smooth transition for existing JSL programs.