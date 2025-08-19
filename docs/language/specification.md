# JSL Language Specification v1.0

## 1. Introduction

JSL (JSON Serializable Language) is a functional programming language where all programs and data are representable as valid JSON. The language has two representations:

1. **Source Language (S-expressions)**: Human-readable JSON arrays
2. **Target Language (JPN - JSL Postfix Notation)**: Stack-based format for execution

## 2. Formal Grammar

### 2.1 Source Language (S-expressions)

```bnf
<expr> ::= <literal>
         | <variable>
         | <list-expr>

<literal> ::= <number> | <boolean> | <null> | <string-literal>

<number> ::= JSON number
<boolean> ::= true | false
<null> ::= null
<string-literal> ::= "@" <string>  ; String starting with @ is literal

<variable> ::= <string>  ; String without @ prefix

<list-expr> ::= "[" <operator> <expr>* "]"

<operator> ::= <string>

<string> ::= JSON string
```

### 2.2 Target Language (JPN - JSL Postfix Notation)

```bnf
<jpn-program> ::= <instruction>*

<instruction> ::= <literal>
                | <variable>
                | <arity> <operator>

<arity> ::= non-negative integer
<operator> ::= <string>
```

**Key Design Decision**: JPN always encodes arity before the operator as two consecutive elements `[arity, operator]`. This provides:
- JSON compatibility (no tuples, only arrays)
- Consistent parsing (always look ahead for operator after seeing integer)
- Efficient execution (know exactly how many values to pop)
- Support for identity elements (0-arity operations)

**Note on Further Compilation**: The JPN representation could be compiled to raw bytecode (e.g., `[PUSH_INT, 2, ADD]` or `[0x12, 0x02, 0x20]`), but JSL deliberately maintains JSON compatibility for network transparency, debuggability, and universal portability. See [Performance Philosophy](PERFORMANCE_PHILOSOPHY.md) for rationale.

## 3. Compilation Rules

The compilation from S-expressions to JPN follows these rules:

### 3.1 Literals

```
compile(n) = [n]           where n is number/boolean/null
compile("@s") = ["@s"]     where s is a string
```

### 3.2 Variables

```
compile("x") = ["x"]       where x doesn't start with @
```

### 3.3 List Expressions

```
compile([op, e₁, ..., eₙ]) = compile(e₁) ++ ... ++ compile(eₙ) ++ [n, op]

where:
  n is the arity (number of arguments)
  ++ denotes list concatenation
```

### 3.4 Special Cases

```
compile([]) = [0, "__empty_list__"]
```

### 3.5 Examples

```
compile(['+', 2, 3])        = [2, 3, 2, '+']
compile(['+'])              = [0, '+']
compile(['*', 2, 3, 4])     = [2, 3, 4, 3, '*']
compile(['list', 1, 2, 3])  = [1, 2, 3, 3, 'list']
```

## 4. Abstract Machine

The JSL abstract machine is a stack-based architecture with the following components:

### 4.1 Machine State

```
State = {
  stack: Value[],        // Value stack
  pc: Int,              // Program counter
  code: Instruction[],  // Postfix instructions
  env: Map<String, Value>, // Environment for variables
  resources: ResourceBudget  // Optional resource limits
}
```

### 4.2 Operational Semantics

The machine executes according to these transition rules:

#### Literal Push
```
⟨S, pc, code[pc] = v, E⟩ → ⟨S·v, pc+1, code, E⟩
  where v is a literal value
```

#### Variable Lookup
```
⟨S, pc, code[pc] = x, E⟩ → ⟨S·E(x), pc+1, code, E⟩
  where x is a variable name and E(x) is defined
```

#### Arity-Operator Pair
```
⟨S·vₙ·...·v₁, pc, code[pc] = n, code[pc+1] = op, E⟩ → ⟨S·op(v₁,...,vₙ), pc+2, code, E⟩
  where n is the arity and op is the operator
```

#### Termination
```
⟨[v], pc, code⟩ → v
  where pc ≥ |code|
```

### 4.3 Notation

- `S·v` denotes pushing value v onto stack S
- `E(x)` denotes looking up variable x in environment E
- `|code|` denotes the length of the code array

## 5. Built-in Operators

### 5.1 Arithmetic Operators

| Operator | Arity | Semantics | Example |
|----------|-------|-----------|---------|
| `+` | 0 | Sum identity: 0 | `[+]` → 0 |
| `+` | 1 | Identity | `[+, 5]` → 5 |
| `+` | 2 | Addition | `[+, 2, 3]` → 5 |
| `+` | n | Sum | `[+, 1, 2, 3]` → 6 |
| `-` | 1 | Negation | `[-, 5]` → -5 |
| `-` | 2 | Subtraction | `[-, 10, 3]` → 7 |
| `*` | 0 | Product identity: 1 | `[*]` → 1 |
| `*` | 2 | Multiplication | `[*, 3, 4]` → 12 |
| `*` | n | Product | `[*, 2, 3, 4]` → 24 |
| `/` | 2 | Division | `[/, 10, 2]` → 5 |
| `%` | 2 | Modulo | `[%, 10, 3]` → 1 |

### 5.2 Comparison Operators

| Operator | Arity | Semantics |
|----------|-------|-----------|
| `=` | 2 | Equality |
| `!=` | 2 | Inequality |
| `<` | 2 | Less than |
| `>` | 2 | Greater than |
| `<=` | 2 | Less or equal |
| `>=` | 2 | Greater or equal |

### 5.3 Logical Operators

| Operator | Arity | Semantics |
|----------|-------|-----------|
| `not` | 1 | Logical negation |
| `and` | 2 | Logical AND |
| `or` | 2 | Logical OR |

### 5.4 List Operators

| Operator | Arity | Semantics | Example |
|----------|-------|-----------|---------|
| `list` | n | Create list | `[list, 1, 2, 3]` → [1,2,3] |
| `cons` | 2 | Prepend element | `[cons, 1, [2, 3]]` → [1,2,3] |
| `first` | 1 | Get first element | `[first, [1, 2]]` → 1 |
| `rest` | 1 | Get tail | `[rest, [1, 2, 3]]` → [2,3] |
| `append` | 2 | Append element | `[append, [1, 2], 3]` → [1,2,3] |
| `length` | 1 | List length | `[length, [1, 2]]` → 2 |

## 6. Special Forms

Special forms have unique evaluation rules and are not compiled to postfix in the current implementation:

### 6.1 Conditional
```
[if, condition, then-expr, else-expr]
```
Evaluates `condition`, then evaluates either `then-expr` or `else-expr`.

### 6.2 Let Binding
```
[let, [var, value], body]
```
Evaluates `value`, binds it to `var`, then evaluates `body` in extended environment.

### 6.3 Lambda
```
[lambda, [param₁, ..., paramₙ], body]
```
Creates a closure capturing current environment.

### 6.4 Definition
```
[def, var, value]
```
Evaluates `value` and binds it to `var` in current environment.

### 6.5 Sequencing
```
[do, expr₁, ..., exprₙ]
```
Evaluates expressions in sequence, returns last value.

### 6.6 Quote
```
[quote, expr] or [@, expr]
```
Returns `expr` without evaluation.

## 7. Type System

JSL is dynamically typed with the following value types:

```
Value = Number
      | Boolean
      | Null
      | String
      | List<Value>
      | Closure
      | Dict<String, Value>
```

## 8. Memory Model

### 8.1 Environment Chain
Environments form a linked chain for lexical scoping:
```
Env = {
  bindings: Map<String, Value>,
  parent: Env | null
}
```

### 8.2 Closure Representation
```
Closure = {
  params: String[],
  body: Expr,
  env: Env
}
```

## 9. Resource Management

The abstract machine can enforce resource limits:

```
ResourceBudget = {
  gas: Int,           // Computational steps
  memory: Int,        // Memory usage
  time_limit: Time,   // Wall-clock time
  collection_limit: Int  // Max collection size
}
```

Each instruction consumes gas:
- Literals: 1 gas
- Variable lookup: 2 gas
- Binary operation: 3 gas
- Function call: 10 gas

## 10. Serialization

All JSL values must be JSON-serializable:

### 10.1 Primitive Serialization
```
serialize(n: Number) = n
serialize(b: Boolean) = b
serialize(null) = null
serialize(s: String) = s
```

### 10.2 Compound Serialization
```
serialize([v₁, ..., vₙ]) = [serialize(v₁), ..., serialize(vₙ)]
serialize({k₁: v₁, ..., kₙ: vₙ}) = {k₁: serialize(v₁), ..., kₙ: serialize(vₙ)}
```

### 10.3 Closure Serialization
```
serialize(Closure{params, body, env}) = {
  "type": "closure",
  "params": params,
  "body": serialize(body),
  "env": serialize_env(env)
}
```

## 11. Decompilation

The decompilation from postfix to S-expressions follows these rules:

### 11.1 Stack-Based Decompilation Algorithm

```
decompile(postfix):
  stack = []
  for instruction in postfix:
    if instruction is literal or variable:
      stack.push(instruction)
    elif instruction is (op, arity):
      args = []
      for i in 1..arity:
        args.prepend(stack.pop())
      stack.push([op] + args)
    elif instruction is binary_op:
      right = stack.pop()
      left = stack.pop()
      stack.push([op, left, right])
  return stack[0]
```

## 12. Formal Properties

### 12.1 Compilation Correctness
For any valid S-expression `e` and environment `E`:
```
eval(e, E) = exec(compile(e), E)
```

### 12.2 Roundtrip Property
For any valid S-expression `e`:
```
decompile(compile(e)) ≡ e
```
Where ≡ denotes structural equivalence.

### 12.3 Serialization Safety
For any JSL value `v`:
```
deserialize(serialize(v)) = v
```

### 12.4 Resumption Safety
For any partial execution state `S`:
```
exec_partial(code, S) = exec_complete(code)
```
When given sufficient resources.

## 13. Examples

### 13.1 Arithmetic Expression
Source:
```json
["*", ["+", 2, 3], ["-", 10, 6]]
```

Postfix:
```json
[2, 3, "+", 10, 6, "-", "*"]
```

Execution trace:
```
[]          | 2 3 + 10 6 - *  ; Initial
[2]         | 3 + 10 6 - *    ; Push 2
[2,3]       | + 10 6 - *      ; Push 3
[5]         | 10 6 - *        ; Apply +
[5,10]      | 6 - *           ; Push 10
[5,10,6]    | - *             ; Push 6
[5,4]       | *               ; Apply -
[20]        |                 ; Apply *
```

### 13.2 Variable Expression
Source:
```json
["+", "x", ["*", "y", 2]]
```

Postfix (with environment `{x: 10, y: 3}`):
```json
["x", "y", 2, "*", "+"]
```

Execution:
```
[]          | x y 2 * +  ; Initial
[10]        | y 2 * +    ; Lookup x
[10,3]      | 2 * +      ; Lookup y
[10,3,2]    | * +        ; Push 2
[10,6]      | +          ; Apply *
[16]        |            ; Apply +
```

## 14. Implementation Notes

1. **Tail Call Optimization**: Not currently implemented
2. **Lazy Evaluation**: Not supported (strict evaluation)
3. **Type Checking**: Dynamic only
4. **Garbage Collection**: Relies on host language (Python)
5. **Concurrency**: Not supported

## 15. Future Extensions

1. **Pattern Matching**: Destructuring in let and lambda
2. **Module System**: Namespace management
3. **Type Annotations**: Optional static typing
4. **Continuations**: First-class continuations for control flow
5. **Parallel Execution**: Parallel evaluation of independent expressions

---

*This specification defines JSL v1.0. The language is designed for network-native computation with complete serializability.*