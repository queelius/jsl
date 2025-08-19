# JSL TODO List

## Immediate Fixes
- [ ] Fix the last failing test in test_runner.py related to lambda functions
- [ ] Add regex matching support (`str-matches` function)
- [ ] Add fuzzy string matching support

## JSON Manipulation Features (High Priority)
Based on dotsuite patterns, JSL needs better JSON manipulation:

### Path Navigation
- [ ] Implement `get-path` for deep path access (e.g., `user.address.city`)
- [ ] Implement `set-path` for deep path modification
- [ ] Implement `has-path` to check if deep path exists
- [ ] Add safe navigation operators (`get-safe`, `get-default`)
- [ ] Support array indexing in paths (e.g., `items[0].price`)
- [ ] Support wildcard paths (e.g., `users.*.email`)

### Query-Based Operations
- [ ] Implement `where` operator for declarative filtering
- [ ] Add query expression evaluation (=, !=, >, <, contains, matches)
- [ ] Support compound queries with and/or/not
- [ ] Add `find-first` to get first matching element
- [ ] Add `count-where` to count matching elements

### Object Transformation
- [ ] Implement `transform` operator for pipeline transformations
- [ ] Add `assign` operation (add/update fields)
- [ ] Add `pick` operation (select specific fields)
- [ ] Add `omit` operation (remove specific fields)
- [ ] Add `rename` operation (rename fields)
- [ ] Add `default` operation (set defaults for missing fields)

### Collection Enhancements
- [ ] Implement `group-by` for grouping collections
- [ ] Implement `index-by` for converting to keyed objects
- [ ] Implement `pluck` for extracting single field from collection
- [ ] Implement `unique` for getting unique values
- [ ] Implement `flatten` for flattening nested arrays
- [ ] Implement `zip` for combining arrays

## Architecture Improvements

### Evaluator Unification
- [ ] Consider whether stack evaluator should use Closure and Env classes
- [ ] Unify closure representation between evaluators
- [ ] Create shared test utilities for both evaluators

### Performance
- [ ] Optimize object evaluation in stack evaluator
- [ ] Add benchmarking suite
- [ ] Profile and optimize hot paths
- [ ] Consider JIT compilation for frequently used functions

### Resource Management
- [ ] Implement memory limits for stack evaluator
- [ ] Add timeout support for both evaluators
- [ ] Implement better resource exhaustion messages
- [ ] Add resource usage statistics

## Language Features

### Control Flow
- [ ] Add `switch/case` expression
- [ ] Add `loop` construct with break/continue
- [ ] Add `for` loop over collections
- [ ] Add pattern matching

### Error Handling
- [ ] Improve error messages with line/column information
- [ ] Add stack traces for debugging
- [ ] Implement error recovery mechanisms
- [ ] Add validation functions

### Type System (Optional)
- [ ] Add optional type annotations
- [ ] Implement type checking
- [ ] Add type inference
- [ ] Create type declaration syntax

## Standard Library Expansion

### Math Functions
- [ ] Add trigonometric functions (sin, cos, tan, etc.)
- [ ] Add statistical functions (mean, median, stddev)
- [ ] Add random number generation
- [ ] Add matrix operations

### Date/Time
- [ ] Add date/time parsing
- [ ] Add date arithmetic
- [ ] Add formatting functions
- [ ] Add timezone support

### Crypto
- [ ] Add hashing functions (SHA, MD5, etc.)
- [ ] Add encoding/decoding (base64, hex)
- [ ] Add UUID generation
- [ ] Consider encryption support

## Tooling

### Development Tools
- [ ] Create Language Server Protocol (LSP) implementation
- [ ] Add syntax highlighting for editors
- [ ] Create debugger interface
- [ ] Add profiler tools

### Documentation
- [ ] Complete API documentation
- [ ] Add more tutorials
- [ ] Create cookbook with common patterns
- [ ] Add performance guide

### Testing
- [ ] Increase test coverage to 100%
- [ ] Add property-based testing
- [ ] Create integration test suite
- [ ] Add performance regression tests

## Network & Distribution

### Serialization
- [ ] Optimize serialization format
- [ ] Add compression support
- [ ] Implement incremental serialization
- [ ] Add versioning support

### Distribution
- [ ] Implement distributed evaluation
- [ ] Add remote procedure calls
- [ ] Create clustering support
- [ ] Implement work stealing

## Security

### Sandboxing
- [ ] Implement capability-based security
- [ ] Add permission system for host functions
- [ ] Create security audit tools
- [ ] Add code signing support

### Validation
- [ ] Add input validation framework
- [ ] Implement schema validation
- [ ] Add sanitization functions
- [ ] Create security linting

## Ecosystem

### Package Management
- [ ] Design module system
- [ ] Create package repository
- [ ] Implement dependency resolution
- [ ] Add versioning support

### Interoperability
- [ ] Add JavaScript interop
- [ ] Add Python interop beyond host functions
- [ ] Create REST API framework
- [ ] Add GraphQL support

## Long-term Vision

### Compilation
- [ ] Create WASM target
- [ ] Implement native compilation
- [ ] Add JVM bytecode generation
- [ ] Create LLVM backend

### Optimization
- [ ] Implement tail call optimization
- [ ] Add constant folding
- [ ] Implement dead code elimination
- [ ] Add inlining optimization

## Current Priorities

1. **Fix remaining test** - Get to 100% passing tests
2. **JSON manipulation features** - Essential for a JSON-native language
3. **Documentation** - Improve onboarding and adoption
4. **Performance** - Ensure scalability
5. **Tooling** - Better developer experience

## Notes

- The recursive evaluator is the reference implementation
- Stack evaluator needs to maintain behavioral parity
- All features must remain JSON-serializable
- Network transmission is a first-class concern
- Security through capability restriction is fundamental