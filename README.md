# JSL: JSON Serializable Language

## Introduction

JSL (JSON Serializable Language) is a Lisp-like functional programming language designed from the ground up with network-nativity and JSON serializability as core tenets. In an era of distributed systems and microservices, JSL aims to provide a robust, secure, and transparent way to transmit, store, and execute code across diverse environments. By treating JSON as the canonical representation for both data and code, JSL addresses common challenges in code mobility, runtime dependencies, and cross-platform interoperability.

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

## Key Features

- **Universal JSON Representation:** Simplifies storage, transmission, and interoperability.
- **Portable Code:** JSL programs and closures can be executed in any compliant JSL runtime.
- **Secure by Design:** The host environment controls access to sensitive operations. Transmitted code itself does not carry executable native instructions.
- **Inspectable and Auditable:** Since code and effect requests are data (JSON), they can be easily logged, inspected, and audited.
- **Extensible Prelude:** Core functionalities are provided by a "prelude" environment, which can be customized or extended by the host.

## Architecture Overview

The JSL ecosystem can be conceptualized in layers:

1. **Wire Layer (JSON):** The universal representation for JSL programs, data, and serialized closures. This is what gets transmitted over networks or stored in databases.
2. **JSL Runtime/Interpreter:**
  
   - **Parser:** Converts JSON into internal JSL abstract syntax.
   - **Evaluator:** Executes JSL code based on its semantics. This includes handling special forms (`def`, `lambda`, `if`, `do`, `host`, etc.) and function applications.
   - **Environment Manager:** Manages lexical environments and scope resolution.

3. **Prelude Layer:** A foundational environment provided by the host runtime. It contains built-in functions and constants (e.g., arithmetic operations, list manipulation functions). The prelude itself is not serialized with user code, as its elements are not typically JSL values but rather a part of the host's runtime environment.
4. **User Code Layer:** JSL programs and libraries written by developers. These are fully serializable.
5. **Host Interaction Layer (JHIP):** When a JSL program evaluates a `["host", ...]` form, it generates a JHIP request. The host system processes this request and returns a JHIP response. See [JHIP.md](JHIP.md) for details. These are not part of the JSL core but are essential for interaction with the host environment and external systems and can be used to facilitate side effects like I/O operations, network requests, etc. These could have been included in the prelude, as prelude functions, as the prelude is not serialized with user code either, but the prelude provides a set of built-in functions that are expected to be available in any host environment implementing the JSL runtime, while JHIP is a protocol for interaction with the host environment that may vary between implementations.
6. **Host Environment:** The runtime that executes JSL code, manages resources, and enforces security policies. It interprets JHIP requests and provides the necessary capabilities for side-effecting operations.

## Serialization in JSL

A critical aspect of JSL is its ability to serialize program state, especially closures.

- **Closures:** A JSL `Closure` object (representing a `lambda`) stores its parameters, body, and a reference to its captured lexical environment. When serialized, the environment only includes user-defined variables relevant to the closure (free variables). Built-in functions from the prelude are not serialized with the closure but are expected to be available in the target runtime's prelude.
- **Environments:** Environments (`Env` objects) are dictionaries that map names to values, with a potential link to a parent environment for lexical scoping. Serialization handles these chains, ensuring that only necessary user-defined bindings are included.

The `to_json` and `from_json` (or equivalent) functions in a JSL implementation are responsible for converting JSL values, including closures and their environments, to and from their JSON representation, handling potential circular references and ensuring that prelude bindings are correctly re-established upon deserialization.

## Security Model

JSL's security model is primarily based on capability restriction and effect reification:

- **No Arbitrary Code Execution:** JSL code itself is data. It doesn't compile to native machine code that can perform arbitrary system calls.
- **Host-Controlled Capabilities:** All interactions with the external world (file I/O, network requests, etc.) must go through the `["host", ...]` mechanism. The host environment has full control over which commands are permitted and how they are executed.
- **Sandboxing:** JSL programs run within the confines of the JSL interpreter and the capabilities granted by the host.
- **Inspectable Effects:** Because side-effect requests are JSON data, they can be audited, logged, or even transformed by the host before execution.

## Use Cases

JSL's design makes it suitable for a variety of applications:

- **Distributed Computing:** Safely send computations to where the data resides.
- **Edge Computing:** Dynamically deploy and update logic on edge devices.
- **Serverless Functions / FaaS:** Represent functions as JSON, simplifying deployment and management.
- **Workflow Automation:** Define complex workflows as JSL programs.
- **Code as Configuration:** Use JSL to define dynamic and executable configurations.
- **Microservice Communication:** Share functional components or request executable logic between services.
- **Database Stored Procedures:** Store and execute application logic within a database in a portable format.
- **Plugin Systems:** Allow users to extend applications with sandboxed, serializable plugins.

## JSL Host Interaction Protocol (JHIP)

For JSL programs to interact with their host environment (e.g., to perform I/O or other side-effecting operations), JSL uses the JSL Host Interaction Protocol (JHIP). JHIP defines how JSL requests these operations as JSON messages and how the host responds.

For detailed information, please see [JHIP.md](JHIP.md).