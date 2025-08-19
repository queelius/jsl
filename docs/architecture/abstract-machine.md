# JSL Abstract Machine Specification

## 1. Overview

The JSL Abstract Machine is a stack-based virtual machine designed to execute JSL postfix bytecode. It provides a simple, resumable, and network-friendly execution model.

## 2. Machine Architecture

### 2.1 Components

The abstract machine consists of:

```
Machine M = ⟨S, E, C, D, R⟩
```

Where:
- **S** (Stack): Value stack for operands and results
- **E** (Environment): Variable bindings
- **C** (Code): Array of instructions (postfix)
- **D** (Dump): Saved states for function calls (future)
- **R** (Resources): Resource budget and consumption

### 2.2 Value Domain

```
Value v ::= n           (number)
         | b           (boolean)
         | null        (null)
         | s           (string)
         | [v₁,...,vₙ] (list)
         | {k:v,...}   (dictionary)
         | ⟨λ,p,b,E⟩   (closure)
```

### 2.3 Instruction Set

```
Instruction i ::= v              (push value)
                | x              (push variable)
                | op             (binary operator)
                | (op, n)        (n-ary operator)
                | MARK           (stack marker)
                | CALL n         (function call)
                | RET            (return)
```

## 3. Operational Semantics

### 3.1 Basic Transitions

#### Value Push
```
    v is a literal value
─────────────────────────────
⟨S, E, v·C, D, R⟩ → ⟨v·S, E, C, D, R'⟩
```
Where R' = R with gas decremented by 1.

#### Variable Lookup
```
    x ∈ dom(E)    E(x) = v
─────────────────────────────
⟨S, E, x·C, D, R⟩ → ⟨v·S, E, C, D, R'⟩
```
Where R' = R with gas decremented by 2.

#### Binary Operation
```
    ⊕ is a binary operator
─────────────────────────────────────
⟨v₂·v₁·S, E, ⊕·C, D, R⟩ → ⟨(v₁⊕v₂)·S, E, C, D, R'⟩
```
Where R' = R with gas decremented by 3.

#### N-ary Operation
```
    ⊕ is an n-ary operator    |S| ≥ n
─────────────────────────────────────────────
⟨vₙ·...·v₁·S, E, (⊕,n)·C, D, R⟩ → ⟨⊕(v₁,...,vₙ)·S, E, C, D, R'⟩
```
Where R' = R with gas decremented by (3 + n).

### 3.2 Control Flow (Future Extension)

#### Function Call
```
    v = ⟨λ,p₁...pₙ,b,E'⟩    |S| ≥ n
─────────────────────────────────────────────
⟨vₙ·...·v₁·v·S, E, CALL n·C, D, R⟩ → 
⟨[], E'[p₁↦v₁,...,pₙ↦vₙ], b, (S,E,C)·D, R'⟩
```

#### Return
```
    D = (S',E',C')·D'
─────────────────────────────
⟨v·S, E, RET·C, D, R⟩ → ⟨v·S', E', C', D', R⟩
```

### 3.3 Error States

#### Stack Underflow
```
    |S| < n    (⊕,n) requires n arguments
─────────────────────────────────────────
⟨S, E, (⊕,n)·C, D, R⟩ → ERROR: Stack underflow
```

#### Undefined Variable
```
    x ∉ dom(E)
─────────────────────────────
⟨S, E, x·C, D, R⟩ → ERROR: Undefined variable x
```

#### Resource Exhaustion
```
    R.gas ≤ 0
─────────────────────────────
⟨S, E, C, D, R⟩ → PAUSE: ⟨S, E, C, D, R⟩
```

## 4. Execution Algorithm

### 4.1 Basic Execution Loop

```python
def execute(code, env, resources):
    S = []  # Stack
    C = code  # Code pointer
    E = env  # Environment
    R = resources  # Resources
    
    while C:
        if R and R.gas <= 0:
            return PAUSE(S, E, C, R)
        
        instr = C[0]
        C = C[1:]
        
        if is_value(instr):
            S = [instr] + S
            R.gas -= 1
            
        elif is_variable(instr):
            if instr in E:
                S = [E[instr]] + S
                R.gas -= 2
            else:
                return ERROR(f"Undefined: {instr}")
                
        elif is_binary_op(instr):
            if len(S) < 2:
                return ERROR("Stack underflow")
            v2, v1 = S[0], S[1]
            S = [apply_binary(instr, v1, v2)] + S[2:]
            R.gas -= 3
            
        elif is_nary_op(instr):
            op, n = instr
            if len(S) < n:
                return ERROR("Stack underflow")
            args = S[:n]
            S = [apply_nary(op, args)] + S[n:]
            R.gas -= (3 + n)
    
    if len(S) == 1:
        return S[0]
    else:
        return ERROR(f"Invalid final stack: {S}")
```

### 4.2 Resumable Execution

```python
def execute_resumable(state_or_code, env=None):
    if is_saved_state(state_or_code):
        S, E, C, R = restore_state(state_or_code)
    else:
        S = []
        E = env or {}
        C = state_or_code
        R = default_resources()
    
    result = execute_step(S, E, C, R)
    
    if is_pause(result):
        return None, save_state(result)
    else:
        return result, None
```

## 5. Resource Model

### 5.1 Gas Costs

| Operation | Gas Cost | Rationale |
|-----------|----------|-----------|
| Push literal | 1 | Minimal cost |
| Variable lookup | 2 | Environment search |
| Binary operation | 3 | Computation |
| N-ary operation | 3+n | Scales with arguments |
| Function call | 10 | Context switch |
| List creation | 1+n | Allocation |
| Dictionary creation | 1+2n | Key-value pairs |

### 5.2 Memory Limits

```
MemoryLimit = {
    max_stack_depth: 10000,
    max_collection_size: 1000000,
    max_string_length: 1000000,
    max_env_depth: 1000
}
```

### 5.3 Time Limits

```python
def check_time_limit(start_time, limit):
    if time.now() - start_time > limit:
        raise TimeExhausted()
```

## 6. Optimization Opportunities

### 6.1 Instruction Fusion

Combine common patterns:
```
[2, 3, +] → [PUSH_ADD, 2, 3]
[x, y, *] → [MUL_VARS, x, y]
```

### 6.2 Constant Folding

Pre-compute constant expressions:
```
[2, 3, +, 4, *] → [20]  ; Computed at compile time
```

### 6.3 Stack Caching

Keep top stack values in registers:
```
TOS (Top of Stack) → Register 0
TOS-1 → Register 1
```

### 6.4 Environment Optimization

Cache frequently accessed variables:
```
E_cache = LRU_cache(size=32)
```

## 7. Implementation Strategies

### 7.1 Direct Threading

```c
typedef void (*instruction_fn)(Machine*);

instruction_fn dispatch_table[] = {
    [OP_PUSH] = do_push,
    [OP_ADD] = do_add,
    [OP_MUL] = do_mul,
    // ...
};

void execute(Machine* m) {
    while (m->pc < m->code_len) {
        dispatch_table[m->code[m->pc++]](m);
    }
}
```

### 7.2 Computed Goto (GCC)

```c
void* dispatch_table[] = {
    &&do_push,
    &&do_add,
    &&do_mul,
    // ...
};

#define DISPATCH() goto *dispatch_table[code[pc++]]

execute:
    DISPATCH();
    
do_push:
    stack[++sp] = code[pc++];
    DISPATCH();
    
do_add:
    sp--;
    stack[sp] += stack[sp+1];
    DISPATCH();
```

### 7.3 JIT Compilation

```python
def jit_compile(postfix):
    """Compile postfix to native code."""
    native_code = []
    
    for instr in postfix:
        if isinstance(instr, int):
            native_code.append(f"PUSH_IMM {instr}")
        elif instr == '+':
            native_code.append("POP_ADD")
        # ...
    
    return assemble(native_code)
```

## 8. Debugging Support

### 8.1 Stack Trace

```
Stack trace at pc=42:
  [0] main: [+, x, [*, y, 2]]
  [1] *: [*, y, 2]
  Stack: [10, 3, 2]
  Next: *
```

### 8.2 Breakpoints

```python
breakpoints = {15, 27, 42}  # Instruction addresses

def execute_debug(code, env):
    for pc, instr in enumerate(code):
        if pc in breakpoints:
            debug_prompt(stack, env, code, pc)
        execute_instruction(instr)
```

### 8.3 State Inspection

```python
def inspect_state(machine):
    return {
        'stack': machine.stack,
        'env': machine.env,
        'pc': machine.pc,
        'gas_used': machine.initial_gas - machine.gas,
        'next_instruction': machine.code[machine.pc]
    }
```

## 9. Comparison with Other VMs

| Feature | JSL VM | JVM | Python VM | Lua VM |
|---------|--------|-----|-----------|--------|
| Model | Stack | Stack | Stack | Register |
| Bytecode | JSON | Binary | Binary | Binary |
| Resumable | Yes | No | No | Yes (coroutines) |
| Serializable | Yes | No | Partial | No |
| Types | Dynamic | Static | Dynamic | Dynamic |
| GC | Host | Yes | Yes | Yes |

## 10. Performance Characteristics

### 10.1 Time Complexity

| Operation | Complexity |
|-----------|------------|
| Push | O(1) |
| Pop | O(1) |
| Binary op | O(1) |
| Variable lookup | O(log n) average |
| List creation | O(n) |
| Function call | O(1) |

### 10.2 Space Complexity

| Structure | Complexity |
|-----------|------------|
| Stack | O(n) expressions |
| Environment | O(m) variables |
| Code | O(k) instructions |
| Total | O(n + m + k) |

## 11. Security Considerations

### 11.1 Resource Isolation

Each execution has isolated resources:
```python
resources = ResourceBudget(
    gas=10000,
    memory=1_000_000,
    time_limit=1.0
)
```

### 11.2 Capability Security

No ambient authority - all effects through capabilities:
```python
capabilities = {
    'file_read': FileReadCapability('/allowed/path'),
    'network': NetworkCapability(['allowed.host'])
}
```

### 11.3 Sandboxing

```python
def sandbox_execute(untrusted_code):
    sandbox = Sandbox(
        max_stack=1000,
        max_time=1.0,
        no_host_access=True
    )
    return sandbox.execute(untrusted_code)
```

## 12. Example Execution Traces

### 12.1 Simple Arithmetic

Code: `[2, 3, +, 4, *]`

```
Step | Stack | Code        | Action
-----|-------|-------------|--------
0    | []    | 2 3 + 4 *   | Initial
1    | [2]   | 3 + 4 *     | Push 2
2    | [2,3] | + 4 *       | Push 3
3    | [5]   | 4 *         | Add
4    | [5,4] | *           | Push 4
5    | [20]  | ε           | Multiply
```

### 12.2 With Variables

Code: `[x, y, +]` with env `{x: 10, y: 20}`

```
Step | Stack    | Code  | Action
-----|----------|-------|----------
0    | []       | x y + | Initial
1    | [10]     | y +   | Lookup x
2    | [10,20]  | +     | Lookup y
3    | [30]     | ε     | Add
```

## 13. Future Directions

1. **Tail Call Optimization**: Reuse stack frames
2. **Lazy Evaluation**: Thunks and promises
3. **Parallel Execution**: Multiple stacks
4. **Native Code Generation**: LLVM backend
5. **Persistent Data Structures**: Immutable collections

---

*This specification defines the JSL Abstract Machine v1.0, providing a formal foundation for JSL execution.*