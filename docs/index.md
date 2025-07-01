# JSL - JSON Serializable Language

## A Network-Native Functional Programming Language

JSL is a Lisp-like functional programming language designed from the ground up for network transmission and distributed computing. Unlike traditional languages that treat serialization as an afterthought, JSL makes wire-format compatibility a first-class design principle.

In an era of distributed systems and microservices, JSL addresses common challenges in code mobility, runtime dependencies, and cross-platform interoperability by treating JSON as the canonical representation for both data and code.

## Key Features

- **🔄 Network-Native**: Every JSL program is valid JSON that can be transmitted over networks
- **🔒 Secure by Design**: Host environment controls all capabilities and side effects
- **📦 Closure Serializability**: Functions with captured environments can be serialized and reconstructed
- **🎯 Homoiconic**: Code and data share the same JSON representation
- **⚡ Deterministic**: Core language evaluation is predictable and reproducible
- **🔧 Extensible**: Built-in prelude provides practical functionality

## Core Design Principles

JSL is built upon fundamental principles that guide every aspect of its design:

- **JSON as Code and Data**: All JSL programs and data structures are representable as standard JSON. This ensures universal parsing, generation, and compatibility with a vast ecosystem of tools and platforms.
- **Network-Native**: The language is designed for seamless transmission over networks. Its serialization format is inherently web-friendly and requires no complex marshalling/unmarshalling beyond standard JSON processing.
- **Serializable Closures**: JSL provides a mechanism for serializing closures, including their lexical environments (user-defined bindings), allowing functions to be truly mobile.
- **Effect Reification**: Side-effects are not executed directly within the core language evaluation but are described as data structures, allowing host environments to control, audit, or modify them.
- **Deterministic Evaluation**: The core JSL evaluation (excluding host interactions) is deterministic, facilitating testing, debugging, and predictable behavior.
- **Security through Capability Restriction**: The host environment governs the capabilities available to JSL programs, particularly for side-effecting operations.

## Quick Example

```json
// Define and call a factorial function
[
  "do",
  ["def", "factorial", 
   ["lambda", ["n"], 
    ["if", ["<=", "n", 1], 
     1, 
     ["*", "n", ["factorial", ["-", "n", 1]]]]]],
  ["factorial", 5]
]
// → 120
```

This JSL program:

1. **Is valid JSON** - can be stored, transmitted, and parsed by any JSON-compliant system
2. **Defines a function** - creates a recursive factorial function
3. **Captures closures** - the function can be serialized with its environment
4. **Produces a result** - evaluates to 120

## Theoretical Foundations

JSL draws inspiration from several key concepts in computer science and programming language theory:

- **Homoiconicity**: Like Lisp, JSL code and data share the same structural representation. However, JSL uses JSON arrays and objects instead of S-expressions, leveraging JSON's widespread adoption and strict schema.
- **Lexical Scoping and Closures**: JSL employs lexical scoping. Functions (`lambda` forms) can capture variables from their surrounding lexical environments, forming closures. The serialization mechanism is designed to preserve these captured environments.
- **Functional Programming**: JSL encourages a functional programming style, emphasizing immutability, first-class functions, and expressions over statements.
- **Separation of Pure Computation and Effects**: The core JSL interpreter deals with pure computation. Interactions with the external world (I/O, system calls) are managed via the JSL Host Interaction Protocol (JHIP), where effects are requested as data.

## Why JSL?

### The Problem with Traditional Code Mobility

Modern distributed systems need to move code between services, store executable logic in databases, and update running systems dynamically. Traditional approaches face fundamental limitations:

- **Serialization brittleness** - Complex frameworks that break across versions
- **Runtime dependencies** - Code tied to specific environments and libraries  
- **Security vulnerabilities** - Deserializing arbitrary code creates attack vectors
- **Platform lock-in** - Language-specific formats prevent interoperability

### The JSL Solution

JSL solves these problems by making JSON the native representation for both code and data:

- **Universal compatibility** - Works with any system that supports JSON
- **Intrinsic safety** - Transmitted code contains no executable primitives
- **Runtime independence** - Compatible prelude provides computational foundation
- **Cross-platform** - Language-agnostic JSON representation

## Use Cases

JSL's design makes it suitable for a variety of applications:

- **Distributed Computing**: Send computations to where data resides, reducing network overhead and improving performance
- **Edge Computing**: Deploy and update logic on edge devices dynamically without full redeployment
- **Serverless Functions / FaaS**: Represent functions as JSON, simplifying deployment and management
- **Database Functions**: Store and execute business logic directly in databases in a portable format  
- **Microservice Communication**: Share functional components across service boundaries with guaranteed compatibility
- **Code as Configuration**: Express complex configurations as executable programs that can be validated and tested
- **Workflow Automation**: Define complex workflows as JSL programs that can be stored, versioned, and executed anywhere
- **Plugin Systems**: Allow users to extend applications with sandboxed, serializable plugins
- **Live Programming**: Update running systems by transmitting new code without service interruption

## Getting Started

1. **[Installation](getting-started/installation.md)** - Set up JSL in your environment
2. **[Quick Start](getting-started/quickstart.md)** - Your first JSL program
3. **[Language Guide](language/overview.md)** - Learn the syntax and semantics
4. **[Tutorials](tutorials/first-program.md)** - Step-by-step examples

## Architecture Overview

JSL consists of three layers:

1. **Prelude Layer** - Non-serializable built-in functions that form the computational foundation
2. **User Layer** - Serializable functions and data defined by user programs  
3. **Wire Layer** - JSON representation for transmission and storage

This separation ensures transmitted code is always safe while remaining fully functional when reconstructed with a compatible prelude.

## Learn More

- **[Design Philosophy](architecture/philosophy.md)** - Theoretical foundations and principles
- **[AST Specification](language/ast.md)** - Formal language syntax definition
- **[JHIP Protocol](jhip/protocol.md)** - Host interaction for side effects
- **[API Reference](api/core.md)** - Complete function documentation
