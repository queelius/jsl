# Changelog

All notable changes to JSL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-12-19

### Added
- **Immutable Prelude Environments**
  - Prelude environments are now immutable and cannot be modified with `define()`
  - Prevents accidental modification of the foundation environment
  - Ensures prelude can be safely shared across multiple evaluation contexts

- **Environment Management Improvements**
  - Automatic extension of prelude in JSLRunner for modifiable base environment
  - Consistent environment handling between recursive and stack evaluators
  - Both evaluators now accept environment parameter in `eval()` method

- **Environment Equality and Deep Copy**
  - Added `__eq__` method to Env class for structural equality checking
  - Added `deepcopy()` method for Env and Closure classes
  - Prelude versioning system with ID generation for compatibility checking
  - Content-addressable hashing for environments with cycle detection

- **Serialization Enhancements**
  - Improved cycle handling in deserialization
  - Ensured closures always have an environment (never None)
  - Better reconstruction of environments with circular references

### Changed
- **Breaking: Prelude Immutability**
  - `Env.define()` now raises JSLError when called on prelude environments
  - Must use `extend()` to create a modifiable child environment
  - All test code updated to use `prelude.extend({})` pattern

- **Stack Evaluator Refactoring**
  - Transitioned from dict-based to Env/Closure class representation
  - Unified environment handling with recursive evaluator
  - Removed special case handling and None checks for closure.env

### Fixed
- Deserializer properly restores Closure environment references
- Stack evaluator resumption with user-defined environment
- Environment equality comparison with callable functions in prelude
- Deep copy semantics for environments and closures

### Internal
- Removed empty test files and unused resource_wrapped.py
- Cleaned up debug test files from root directory
- Updated CLAUDE.md documentation to reflect current architecture

## [0.2.0] - 2024-01-19

### Added
- **Query and Transformation Operations**
  - `where` special form for declarative filtering with environment-aware conditions
  - `transform` special form for data transformation pipelines
  - Transform operators: `assign`, `pick`, `omit`, `rename`, `default`, `apply`
  - `group-by` function for grouping collections by key functions
  - `pluck` function for extracting fields from collections
  - `index-by` function for converting lists to keyed objects

- **String and Pattern Matching**
  - `str-matches` for regex pattern matching
  - `str-replace` for regex-based string replacement
  - `str-find-all` for finding all pattern matches
  - `contains` and `matches` operators for use in conditions

- **JSON Path Navigation**
  - `get-path` for deep path access (e.g., "user.address.city")
  - `set-path` for setting values at deep paths
  - `has-path` for checking path existence
  - Support for wildcards and array indices in paths

- **Integration Placeholders**
  - FastAPI integration for REST API service
  - Model Context Protocol (MCP) for AI/LLM integration
  - Jupyter notebook integration
  - VS Code extension placeholder
  - Docker and Kubernetes integration guides

### Changed
- Refactored `where` and `transform` from prelude functions to special forms
- Both now use the core JSL evaluator with extended environments
- Field names are available as symbols during evaluation
- Improved consistency in operator semantics

### Fixed
- Lambda closure evaluation in stack evaluator
- Closure representation handling in `def` special form
- Test compatibility with refactored special forms

## [0.1.0] - 2024-01-15

### Initial Release
- Core JSL interpreter with S-expression evaluation
- Dual evaluator architecture (recursive and stack-based)
- JSON serialization/deserialization of programs and closures
- Resource management system (gas metering, time limits, memory bounds)
- Comprehensive prelude with arithmetic, logic, string, and list operations
- Host interaction protocol (JHIP) for controlled side effects
- CLI with REPL support
- Test suite with high coverage