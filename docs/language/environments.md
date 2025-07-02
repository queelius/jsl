# Environments and Execution Contexts

## Overview: The Scope Chain

Environments are a fundamental concept in JSL, forming the backbone of its lexical scoping, security model, and module system. An environment is a data structure that maps variable names to their values. Every JSL expression is evaluated within an environment.

When looking up a variable, the JSL runtime first checks the current environment. If the variable is not found, it proceeds to check the parent environment, and so on, creating a "scope chain." This process continues until it reaches the root environment, which is the **[Prelude](./prelude.md)**. The prelude provides all the built-in functions and is implicitly the ultimate parent of all user-defined environments.

## The Algebra of Environments

This algebra provides the foundation for JSL's **Level 2 (Advanced) Capability-Based Security Model**. While the standard security model relies on the host dispatcher to authorize requests (see [Security Model](../architecture/security.md)), the environment algebra allows a trusted orchestrator to provision sandboxed execution contexts that cannot even *attempt* to call unauthorized host commands.

By using operators like `remove` to withhold the raw `["host", ...]` capability and `layer` to provide safe, pre-defined wrapper functions, a host can enforce security at the language level, before a request ever reaches the dispatcher.

For a complete discussion of the layered security model, see the [Security Model](../architecture/security.md) documentation.

These operations are typically exposed to trusted code (e.g., via the Fluent Python API or a special host configuration) and are essential for creating custom execution contexts. They take one or more environment hashes as input and produce a **new** environment hash as output, never modifying the original environments.

### `layer` (Union / Additive Merge)

The `layer` operation creates a new environment by combining the bindings from one or more existing environments on top of a shared parent.

*   **Syntax:** `["layer", parent_env_hash, env_hash_1, env_hash_2, ...]`
*   **Use Case:** Module composition. You can load multiple modules (each represented by an environment) and `layer` them together to create a single, unified API scope for your application.
*   **Conflict Resolution:** If multiple source environments define a binding with the same name, the one from the last environment in the argument list ("last-write-wins") is used.

### `remove` (Subtraction / Capability Reduction)

The `remove` operation creates a new, less-privileged environment by removing specified bindings.

*   **Syntax:** `["remove", env_hash, "key_to_remove_1", "key_to_remove_2", ...]`
*   **Use Case:** Sandboxing and security. If you have a powerful `file_system` module, you can use `remove` to create a "read-only" version of it for untrusted code by removing the `write` and `delete` bindings.

### `intersect` (Intersection of Capabilities)

The `intersect` operation creates a new environment containing only the bindings whose names exist in *all* of the provided environments.

*   **Syntax:** `["intersect", env_hash_1, env_hash_2, ...]`
*   **Use Case:** Enforcing an API interface. You can `intersect` two versions of a module to create an environment that is guaranteed to only contain the functions common to both, making your code more robust against API changes.

### `difference` (Exclusive Capabilities)

The `difference` operation creates a new environment containing only the bindings from a base environment whose names do *not* exist in another.

*   **Syntax:** `["difference", base_env_hash, env_to_subtract_hash]`
*   **Use Case:** Introspection and tooling. This can be used to identify new or deprecated features between two versions of a module.

## Environments and Serialization

While the concept of environments is part of the language specification, their representation for transport and storage is an architectural detail. For more information on how environments are serialized using content-addressable hashing, see [Code and Data Serialization](../architecture/serialization.md).