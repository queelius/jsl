# Runtime Architecture

## Overview

The JSL ecosystem is designed as a layered architecture that separates concerns and ensures both security and portability. Understanding these layers is crucial for implementing JSL systems and reasoning about code execution.

## Architecture Layers

The JSL runtime can be conceptualized in six distinct layers:

### 1. Wire Layer (JSON)

The universal representation for JSL programs, data, and serialized closures. This is what gets transmitted over networks or stored in databases.

**Characteristics:**
- Standard JSON format
- Universal compatibility
- Human-readable
- Version-independent
- Platform-agnostic

### 2. JSL Runtime/Interpreter

The core execution engine that processes JSL code:

#### Parser
- Converts JSON into internal JSL abstract syntax
- Validates JSON structure against JSL grammar
- Handles syntax errors and malformed input

#### Evaluator
- Executes JSL code based on language semantics
- Handles special forms (`def`, `lambda`, `if`, `do`, `host`, etc.)
- Manages function applications and argument evaluation
- Implements lexical scoping rules

#### Environment Manager
- Manages lexical environments and scope resolution
- Handles variable binding and lookup
- Maintains environment chains for closures
- Supports environment serialization/deserialization

### 3. Prelude Layer

A foundational environment provided by the host runtime containing built-in functions and constants.

**Key Properties:**
- Contains essential computational primitives (arithmetic, logic, list operations)
- Not serialized with user code
- Expected to be available in any compliant JSL runtime
- Can be customized or extended by host implementations
- Serves as the computational foundation for user programs

**Examples:**
- Arithmetic operations: `+`, `-`, `*`, `/`
- Comparison operators: `<`, `>`, `<=`, `>=`, `=`
- List operations: `map`, `filter`, `reduce`
- Type predicates: `null?`, `number?`, `string?`

### 4. User Code Layer

JSL programs and libraries written by developers. These are fully serializable and portable.

**Characteristics:**
- Complete JSON serializability
- Closure capture and reconstruction
- Cross-runtime portability
- Environment independence (beyond prelude)

### 5. Host Interaction Layer (JHIP)

When a JSL program evaluates a `["host", ...]` form, it generates a JHIP (JSL Host Interaction Protocol) request. This layer manages the interface between pure JSL computation and external effects.

**Key Features:**
- Effect reification as data structures
- Request-response protocol
- Host authority over permitted operations
- Audit trail capability
- Security boundary

### 6. Host Environment

The runtime system that executes JSL code, manages resources, and enforces security policies.

**Responsibilities:**
- JSL interpreter hosting
- JHIP request processing
- Resource management
- Security policy enforcement
- Capability provisioning

## Serialization Architecture

A critical aspect of JSL's runtime architecture is its serialization system:

### Closure Serialization

JSL `Closure` objects store:
- Function parameters
- Function body
- Captured lexical environment (only user-defined variables)

**Serialization Process:**
1. Identify free variables in closure body
2. Extract relevant bindings from lexical environment
3. Serialize environment chain (user bindings only)
4. Exclude prelude bindings (reconstructed at runtime)

### Environment Serialization

Environments (`Env` objects) are serialized as:
- Dictionary of name-to-value mappings
- Parent environment reference (if applicable)
- Only user-defined bindings included

**Reconstruction Process:**
1. Recreate environment hierarchy
2. Restore user-defined bindings
3. Link to appropriate prelude environment
4. Validate binding completeness

## Security Model

JSL's architecture provides security through multiple layers:

### Capability Restriction
- All side effects must go through JHIP
- Host controls available operations
- Fine-grained permission model

### Code Safety
- No native code execution
- JSON-based representation prevents code injection
- Deterministic evaluation (in pure subset)

### Effect Reification
- Side effects are described as data
- Host can inspect, audit, or modify requests
- Clear separation between computation and effects

### Sandboxing
- JSL programs run within interpreter bounds
- No direct system access
- Host-mediated resource access only

## Implementation Considerations

### Performance
- JSON parsing overhead
- Environment lookup chains
- Closure reconstruction costs
- JHIP communication latency

### Memory Management
- Environment retention for closures
- Garbage collection of unused environments
- Serialization memory overhead

### Error Handling
- JSON parsing errors
- Runtime evaluation errors
- JHIP communication failures
- Host capability denials

## Deployment Patterns

### Distributed Computing
```
Client Runtime -> JSON Code -> Remote Runtime -> Results
```

### Database Functions
```
Application -> Stored JSL -> Database -> Executed Results
```

### Microservice Communication
```
Service A -> JSL Function -> Service B -> Response
```

### Edge Computing
```
Central Control -> JSL Logic -> Edge Devices -> Local Execution
```

This layered architecture ensures JSL maintains its core properties of safety, portability, and network-nativity while providing the flexibility needed for diverse deployment scenarios.
