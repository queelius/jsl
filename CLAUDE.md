# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JSL (JSON Serializable Language) is a network-native functional programming language where all programs and data are representable as standard JSON. It's a Lisp-like language designed for distributed computing with serializable closures and capability-based security.

## Development Commands

### Setup and Environment
```bash
make setup                    # Create venv and install dependencies
source .venv/bin/activate     # Activate virtual environment
make install-dev             # Install development dependencies
```

### Testing
```bash
make test                     # Run all tests with coverage
make test-only               # Run tests without coverage
make test-file TEST_FILE=tests/test_core.py::TestEvaluator::test_lambda  # Run specific test
```

### Running JSL Code
```bash
jsl --repl                   # Interactive REPL
jsl --eval '["+", 1, 2, 3]' # Evaluate expression
jsl program.jsl             # Run JSL file
make examples               # Run example programs
```

### Documentation
```bash
make docs                    # Build and serve docs locally (http://localhost:8000)
make docs-build             # Build documentation only
```

### Step Limiting (Network-Native Feature)
JSL includes step limiting for safe distributed execution:
```python
runner = JSLRunner(config={"max_steps": 1000})
```
- Prevents DOS attacks and infinite loops
- Enables pauseable/resumable computation
- Supports fair resource allocation
- See `examples/step_accounting.py` for network usage patterns

## Architecture Overview

### Core Module Structure
- `jsl/core.py` - Core interpreter (Env, Closure, Evaluator, HostDispatcher)
- `jsl/prelude.py` - Built-in functions (arithmetic, logic, collections)
- `jsl/runner.py` - High-level execution API
- `jsl/serialization.py` - JSON serialization/deserialization
- `jsl/fluent.py` - Fluent API for building JSL expressions
- `jsl/cli.py` - Command-line interface and REPL

### JSL Language Syntax

JSL code is JSON arrays where the first element is the operator:
- Function call: `["+", 1, 2, 3]`
- Lambda: `["lambda", ["x", "y"], ["+", "x", "y"]]`
- Let binding: `["let", ["x", 5], ["*", "x", 2]]`
- Conditional: `["if", ["=", "x", 0], "zero", "non-zero"]`

### Special Forms
These forms have special evaluation rules and are handled directly by the evaluator:
- `if` - Conditional evaluation
- `let` - Local variable binding
- `lambda` - Function creation
- `def` - Global variable definition
- `do` - Sequential evaluation
- `quote` / `@` - Prevent evaluation
- `try` - Error handling
- `host` - Host interaction
- `where` - Collection filtering (extends environment with item fields)
- `transform` - Data transformation (extends environment with item fields)

### String Conventions
- `"variable"` - Variable lookup
- `"@literal"` - Literal string value (@ prefix makes it a string literal)
- `"@/path"` - File paths in host interactions

### CRITICAL: Quoting and String Literal Semantics
**This is a common source of confusion - pay careful attention:**

1. **In regular JSL expressions:**
   - `"foo"` = symbol lookup (looks for variable named foo)
   - `"@foo"` = string literal "foo"

2. **The Quote Operator `["@", ...]` and Its Effects:**
   - The quote operator returns its argument WITHOUT evaluating it as JSL code
   - The quoted data is passed as-is to functions that interpret it
   
   **Example: Quote usage**
   ```json
   ["@", ["+", 1, 2]]  // Returns the list ["+", 1, 2] without evaluating it
   ```

3. **Special Forms (where, transform) - NOW WORK WITHOUT QUOTING:**
   
   **Where is now a special form:**
   - `["where", "products", [">", "price", 50]]`
   - No quoting needed - the condition is evaluated in an extended environment
   - The environment includes all fields from each item being filtered
   - Field access: `"price"` directly accesses the field (it's in the environment)
   - Root item access: `"$"` refers to the entire item for nested access
   
   **Example:**
   ```json
   ["where", "orders", ["=", ["get-path", "$", "@customer.vip"], true]]
   ```
   - `"$"` = the current order object
   - `["get-path", "$", "@customer.vip"]` = accesses order.customer.vip

4. **Transform is also a special form:**
   - `["transform", "data", ["pick", "@name", "@email"]]`
   - No quoting needed for the operation
   - The operation is evaluated with item fields in the environment
   - Operations like `pick`, `omit`, `assign` are evaluated in context
   
   **Example:**
   ```json
   ["transform", "users", 
     ["assign", "@fullName", ["str-concat", "firstName", "@", "lastName"]]]
   ```
   - `"firstName"` and `"lastName"` are field lookups (from environment)
   - `"@fullName"` is the literal string "fullName" (new field name)

5. **Common patterns:**
   - Field access in where/transform: `"fieldName"` (direct lookup)
   - String literals for field names: `"@fieldName"` 
   - Access entire item: `"$"`
   - Nested field access: `["get-path", "$", "@path.to.field"]`

6. **Key insight:**
   - `where` and `transform` are special forms that extend the environment
   - They make item fields available as variables during evaluation
   - This eliminates the need for quoting in most cases
   - The `$` binding provides access to the entire item when needed

### Effect System (JHIP)
All side effects go through the host dispatcher:
```json
["host", "@file/read", "@/path/to/file.txt"]
["host", "@print", "@Hello World"]
```

### Key Classes and Patterns

1. **Evaluator.eval()** - Main evaluation entry point, handles all JSL forms
2. **Env** - Immutable environment with lexical scoping via `extend()` and `lookup()`
3. **Closure** - Serializable function objects with captured environments
4. **HostDispatcher** - Manages capability-based host interactions

### Testing Approach

Tests are organized by module:
- `tests/test_core.py` - Core interpreter tests
- `tests/test_serialization.py` - Serialization/deserialization tests
- `tests/test_fluent.py` - Fluent API tests
- `tests/test_runner.py` - Runner module tests
- `tests/test_cli.py` - CLI tests

Use pytest fixtures and parametrized tests extensively. When adding new features, ensure tests cover both positive cases and error conditions.

### Common Development Tasks

When implementing new built-in functions:
1. Add to `jsl/prelude.py` in the appropriate section
2. Add corresponding tests to `tests/test_core.py`
3. Update documentation if user-facing

When modifying the evaluator:
1. Core evaluation logic is in `jsl/core.py:Evaluator.eval()`
2. Special forms (if, let, lambda, etc.) are handled as separate cases
3. Ensure serialization still works after changes

### Important Notes

- The language is purely functional at its core - all mutation happens through the host
- Closures only serialize user-defined bindings, not prelude functions
- The JSON representation must remain valid for network transmission
- Effect reification means side effects are data, not executed directly
- Use `make test-file` for rapid iteration on specific tests during development