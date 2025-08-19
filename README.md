# JSL - JSON Serializable Language

**A Network-Native Functional Programming Language**

JSL is a Lisp-like functional programming language designed from the ground up for network transmission and distributed computing. Unlike traditional languages that treat serialization as an afterthought, JSL makes wire-format compatibility a first-class design principle.

## 📊 Version 0.2.0 Highlights

- **Dual Evaluation Engines**: Both recursive and stack-based evaluators for different performance and resumption characteristics
- **JPN (JSL Postfix Notation)**: Compiled stack-based bytecode format for efficient execution
- **Query & Transform Operations**: Powerful declarative data manipulation with `where` and `transform` special forms
- **Resource Management**: Comprehensive gas/step metering for safe distributed execution
- **Path Navigation**: Deep JSON/object access with `get-path`, `set-path`, and `has-path`
- **Regex Support**: Pattern matching with `str-matches`, `str-replace`, and `str-find-all`
- **Group By**: Collection grouping and aggregation operations

## 🚀 Quick Start

### Installation

```bash
pip install jsl-lang
```

### Your First JSL Program

JSL supports both JSON array syntax and more readable Lisp-style syntax:

```python
from jsl import JSLRunner

runner = JSLRunner()

# JSON array syntax (network-native format)
result = runner.execute('["+", 1, 2, 3]')
print(result)  # Output: 6

# Lisp-style syntax (human-friendly)
result = runner.execute('(+ 1 2 3)')
print(result)  # Output: 6

# Define and call a function
program = '''
(do
  (def square (lambda (x) (* x x)))
  (square 5))
'''
result = runner.execute(program)
print(result)  # Output: 25

# Query and transform data
runner.execute('(def data [@
  {"name": "Alice", "age": 30, "role": "admin"}
  {"name": "Bob", "age": 25, "role": "user"}
])')

# Filter with where
admins = runner.execute('(where data (= role "admin"))')
print(admins)  # [{"name": "Alice", "age": 30, "role": "admin"}]

# Transform with pick
names = runner.execute('(transform data (pick "@name"))')
print(names)  # [{"name": "Alice"}, {"name": "Bob"}]
```

### Command Line Interface

```bash
# Start interactive REPL
jsl --repl

# Evaluate an expression
jsl --eval '["+", 1, 2, 3]'

# Run a JSL file
jsl program.jsl
```

## Core Design Principles

JSL is built upon the following fundamental principles:

- **JSON as Code and Data:** All JSL programs and data structures are representable as standard JSON. This ensures universal parsing, generation, and compatibility with a vast ecosystem of tools and platforms.
- **Network-Native:** The language is designed for seamless transmission over networks. Its serialization format is inherently web-friendly and requires no complex marshalling/unmarshalling beyond standard JSON processing.
- **Serializable Closures:** JSL provides a mechanism for serializing closures, including their lexical environments (user-defined bindings), allowing functions to be truly mobile.
- **Effect Reification:** Side-effects are not executed directly within the core language evaluation but are described as data structures (see [JHIP.md](JHIP.md)), allowing host environments to control, audit, or modify them.
- **Deterministic Evaluation (Core Language):** The core JSL evaluation (excluding host interactions) is deterministic, facilitating testing, debugging, and predictable behavior.
- **Security through Capability Restriction:** The host environment governs the capabilities available to JSL programs, particularly for side-effecting operations.

## Theoretical Foundations

JSL draws inspiration from several key concepts in computer science and programming language theory:

- **Homoiconicity:** Like Lisp, JSL code and data share the same structural representation. However, JSL uses JSON arrays and objects instead of S-expressions, leveraging JSON's widespread adoption and strict schema.
- **Lexical Scoping and Closures:** JSL employs lexical scoping. Functions (`lambda` forms) can capture variables from their surrounding lexical environments, forming closures. The serialization mechanism is designed to preserve these captured environments.
- **Functional Programming:** JSL encourages a functional programming style, emphasizing immutability, first-class functions, and expressions over statements.
- **Separation of Pure Computation and Effects:** The core JSL interpreter deals with pure computation. Interactions with the external world (I/O, system calls) are managed via the JSL Host Interaction Protocol ([JHIP.md](JHIP.md)), where effects are requested as data.

## Syntax Options

JSL offers two syntactic representations that compile to the same internal format:

### JSON Array Syntax (Network-Native)
```json
["do",
  ["def", "factorial", 
    ["lambda", ["n"],
      ["if", ["<=", "n", 1],
        1,
        ["*", "n", ["factorial", ["-", "n", 1]]]]]],
  ["factorial", 5]]
```

### Lisp-Style Syntax (Human-Friendly)
```lisp
(do
  (def factorial 
    (lambda (n)
      (if (<= n 1)
        1
        (* n (factorial (- n 1))))))
  (factorial 5))
```

Both syntaxes support:
- **String literals:** `"@hello"` becomes `"hello"`
- **Quote operator:** `[@` or `(@` prevents evaluation
- **Field references:** In `where`/`transform`, fields automatically bind

## Key Features

- **Universal JSON Representation:** Simplifies storage, transmission, and interoperability
- **Dual Evaluation Engines:** Choose between recursive (simpler) or stack-based (resumable) execution
- **Resumable Computation:** Pause execution at any point and resume later, even on different machines
- **Resource Management:** Built-in gas metering and step limiting for safe distributed execution
- **Portable Code:** JSL programs and closures can be executed in any compliant JSL runtime
- **Secure by Design:** Host environment controls all capabilities; no arbitrary code execution
- **Inspectable and Auditable:** Code and effects are data (JSON), easily logged and analyzed
- **Powerful Query Operations:** Built-in `where` and `transform` for declarative data manipulation
- **Serializable Closures:** Functions with captured environments can be transmitted over networks
- **Extensible Prelude:** Core functions can be customized or extended by the host

## Architecture Overview

JSL features a sophisticated multi-layer architecture with dual evaluation engines:

### Evaluation Engines

JSL provides two complementary evaluation strategies:

1. **Recursive Evaluator:** Traditional tree-walking interpreter with direct AST evaluation
   - Natural implementation of language semantics
   - Excellent for development and debugging
   - Direct closure representation with `Closure` objects

2. **Stack-Based Evaluator:** Compiles to JPN (JSL Postfix Notation) bytecode
   - Efficient resumable execution for distributed computing
   - Natural step/gas metering for resource control
   - Dict-based closure representation for JSON serialization
   - Enables pause/resume across network boundaries

### System Layers

1. **Wire Layer (JSON):** The universal representation for JSL programs, data, and serialized closures. This is what gets transmitted over networks or stored in databases.

2. **Compilation Layer:**
   - **Parser:** Converts JSON/Lisp syntax into internal JSL abstract syntax
   - **Compiler:** Transforms S-expressions to JPN (postfix notation) for stack evaluation
   - **Decompiler:** Reconstructs S-expressions from JPN for debugging

3. **JSL Runtime/Interpreter:**
   - **Evaluator:** Executes JSL code (recursive or stack-based)
   - **Special Forms:** Core language constructs (`def`, `lambda`, `if`, `do`, `where`, `transform`, etc.)
   - **Environment Manager:** Manages lexical environments and scope resolution
   - **Resource Manager:** Tracks gas/step consumption for safe execution

4. **Prelude Layer:** A foundational environment provided by the host runtime containing:
   - Arithmetic operations (`+`, `-`, `*`, `/`, etc.)
   - List manipulation (`cons`, `first`, `rest`, `map`, `filter`, etc.)
   - String operations (`str-concat`, `str-matches`, `str-replace`, etc.)
   - JSON/object operations (`get`, `get-path`, `set-path`, etc.)
   - Query operations (`pluck`, `index-by`, `group-by`, etc.)

5. **User Code Layer:** JSL programs and libraries written by developers. These are fully serializable.

6. **Host Interaction Layer (JHIP):** When a JSL program evaluates a `["host", ...]` form, it generates a JHIP request for side effects. See [JHIP.md](JHIP.md) for details.

7. **Host Environment:** The runtime that executes JSL code, manages resources, and enforces security policies.

## Serialization in JSL

A critical aspect of JSL is its ability to serialize program state, especially closures. JSL uses a content-addressable serialization format that elegantly handles circular references and ensures efficient storage of complex object graphs.

- **Closures:** A JSL `Closure` object (representing a `lambda`) stores its parameters, body, and a reference to its captured lexical environment. When serialized using content-addressable storage, closures are assigned deterministic hashes and stored in an object table with references.
- **Environments:** Environments (`Env` objects) contain variable bindings and capture lexical scope. Only user-defined bindings are serialized (not prelude functions), and environments are also stored in the content-addressable object table.
- **Circular References:** The content-addressable approach naturally handles circular references by using hash-based object references instead of direct embedding.

Simple values (primitives, basic arrays/objects) serialize directly to JSON, while complex values containing closures use the content-addressable format with `__cas_version__`, `root`, and `objects` fields. This ensures maximum compatibility and efficiency across different use cases.

## Security Model

JSL's security model is primarily based on capability restriction and effect reification:

- **No Arbitrary Code Execution:** JSL code itself is data. It doesn't compile to native machine code that can perform arbitrary system calls.
- **Host-Controlled Capabilities:** All interactions with the external world (file I/O, network requests, etc.) must go through the `["host", ...]` mechanism. The host environment has full control over which commands are permitted and how they are executed.
- **Sandboxing:** JSL programs run within the confines of the JSL interpreter and the capabilities granted by the host.
- **Inspectable Effects:** Because side-effect requests are JSON data, they can be audited, logged, or even transformed by the host before execution.

## Query and Transform Operations

JSL provides powerful declarative operations for data manipulation:

### Where (Filtering)
Filter collections based on conditions with automatic field binding:

```jsl
; Filter users by role
(where users (= role "admin"))

; Complex conditions
(where products (and (> price 100) (= category "electronics")))
```

### Transform (Data Shaping)
Reshape data with operations like `pick`, `omit`, and `assign`:

```jsl
; Pick specific fields
(transform users (pick "name" "email"))

; Add computed field
(transform products (assign "discounted" (* price 0.9)))

; Remove sensitive fields
(transform users (omit "password" "ssn"))
```

### Composition
Operations naturally compose for complex data pipelines:

```jsl
(pluck 
  (transform 
    (where products (> price 50))
    (pick "name" "price"))
  "name")
```

## Resource Management

JSL includes comprehensive resource management for safe distributed execution:

- **Gas Metering:** Track computational cost of operations
- **Step Limiting:** Bound execution steps to prevent infinite loops
- **Resumable Execution:** Pause and resume computation across network boundaries
- **Fair Scheduling:** Allocate resources fairly among concurrent programs

```python
from jsl import JSLRunner

# Execute with resource limits
runner = JSLRunner(config={
    "max_steps": 1000,
    "max_gas": 10000
})

# Execution pauses if limits exceeded
result, state = runner.execute_partial(program)
if state:  # Computation paused
    # Can resume later, possibly on different machine
    final_result = runner.resume(state)
```

## Use Cases

JSL's design makes it suitable for a variety of applications:

- **Distributed Computing:** Safely send computations to where the data resides with resumable execution
- **Data Processing Pipelines:** Build complex ETL workflows with query/transform operations
- **Edge Computing:** Dynamically deploy and update logic on edge devices with resource limits
- **Serverless Functions / FaaS:** Represent functions as JSON with automatic gas metering
- **API Query Languages:** Provide safe, expressive query capabilities for REST/GraphQL APIs
- **Workflow Automation:** Define complex workflows as JSL programs with step-by-step execution
- **Code as Configuration:** Use JSL to define dynamic and executable configurations
- **Microservice Communication:** Share functional components or request executable logic between services
- **Database Stored Procedures:** Store and execute application logic within a database in a portable format
- **Plugin Systems:** Allow users to extend applications with sandboxed, resource-limited plugins
- **Smart Contracts:** Build verifiable computations with deterministic evaluation and gas metering

## JPN (JSL Postfix Notation)

JPN is JSL's compiled bytecode format, designed for efficient stack-based evaluation:

### Compilation Example

```python
from jsl.compiler import compile_to_postfix

# S-expression
expr = ["*", ["+", 2, 3], 4]

# Compiles to postfix
jpn = compile_to_postfix(expr)
# Result: [2, 3, "+", 4, "*"]

# Complex example with special forms
expr = ["if", ["=", "x", 5], "yes", "no"]
jpn = compile_to_postfix(expr)
# Result includes special opcodes for control flow
```

### Benefits of JPN

1. **Linear Execution:** No tree traversal, just sequential instruction processing
2. **Natural Resumption:** Stack state captures exact execution point
3. **Efficient Serialization:** Flat array structure vs nested trees
4. **Cache-Friendly:** Sequential memory access patterns
5. **Simple VM:** Stack machine requires minimal interpreter complexity

### Stack Evaluator Features

```python
from jsl.stack_evaluator import StackEvaluator

evaluator = StackEvaluator()

# Partial evaluation with step limits
result, state = evaluator.eval_partial(jpn, max_steps=100)

if state:  # Execution paused
    # State includes: program counter, stack, environment
    # Can be serialized and sent over network
    serialized_state = state.to_dict()
    
    # Resume on same or different machine
    final_result = evaluator.eval_partial(jpn, state=state)
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
make test-file TEST_FILE=tests/test_core.py

# Run with coverage
make test-coverage
```

### Testing Strategy

JSL uses comprehensive testing including:
- **Unified evaluator tests:** Ensure both evaluators produce identical results
- **Property-based testing:** Verify invariants across random inputs
- **Resource limit testing:** Validate gas metering and step limiting
- **Serialization round-trips:** Ensure programs survive network transmission

### Building Documentation

```bash
# Build and serve documentation locally
make docs  # Available at http://localhost:8000

# Build only
make docs-build
```

## JSL Host Interaction Protocol (JHIP)

For JSL programs to interact with their host environment (e.g., to perform I/O or other side-effecting operations), JSL uses the JSL Host Interaction Protocol (JHIP). JHIP defines how JSL requests these operations as JSON messages and how the host responds.

For detailed information, please see [JHIP.md](JHIP.md).

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

JSL is released under the MIT License. See [LICENSE](LICENSE) for details.