# Changelog

All notable changes to JSL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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