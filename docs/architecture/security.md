# Security Model

## Overview

JSL's security model is built on the principle of **effect reification** and **capability restriction**. Unlike traditional languages where security is layered on top, JSL's design makes security an intrinsic property of the language itself.

## Core Security Principles

-   **No Arbitrary Code Execution:** JSL code is data. This eliminates entire classes of vulnerabilities like buffer overflows and direct system calls.
-   **Effect Reification:** All side effects are represented as data (e.g., `["host", "file/read", ...]`). This makes them auditable, controllable, and transparent before execution.
-   **Host Authority:** The host environment has complete control over what operations are permitted.

## JSL's Layered Security Model

JSL provides two complementary models for managing security and side effects.

### Level 1: Dispatcher-Based Security (The Standard Model)

This is the most direct security model. The host system implements a **Host Command Dispatcher** that is the ultimate gatekeeper for all side effects. It is simple to understand and makes all side effects syntactically obvious.

### Level 2: Capability-Based Security (The Advanced Model)

This is a more advanced model for high-security applications. It uses the **Environment Algebra** and closures to create sandboxes that can restrict access to the `["host", ...]` special form itself, providing a deeper layer of defense.

## The Runtime Boundary

JSL code always executes within the confines of the JSL runtime, which is itself controlled by the host system. All interactions with the outside world must cross this boundary through the JHIP protocol, giving the host the final say.

```
┌─────────────────────────────────────┐
│             Host System             │
│  ┌───────────────────────────────┐  │
│  │        JSL Runtime            │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │     User JSL Code       │  │  │
│  │  │                         │  │  │
│  │  │  All computation here   │  │  │
│  │  │  is safe and contained  │  │  │
│  │  └─────────────────────────┘  │  │
│  │                               │  │  
│  │  Effects must go through JHIP │  │
│  └───────────────────────────────┘  │
│                                     │
│  Host controls all external access  │
└─────────────────────────────────────┘
```

## Security Best Practices

### For Host Implementations

#### 1. Enforce Strict Resource Limits (The "Gas" Model)

Untrusted code can easily attempt to cause a Denial of Service. The host runtime **must** enforce resource limits.

The most straightforward way to do this is to wrap every JSL evaluation in a **strict timeout**. This is the host's primary defense against infinite loops and other denial-of-service attacks.

For more granular control, a host can implement a **"gas" model**, similar to those used in blockchain systems.

-   **How it works:** The host assigns a "gas cost" to every JSL operation (e.g., `+` costs 1 gas, `map` costs 5 gas). A program is started with a finite amount of gas, which is consumed on each operation. If the gas runs out, execution halts.
-   **Benefits:** This provides a predictable execution cost that is independent of machine speed.

At a minimum, hosts should enforce simple timeouts and memory caps.

##### Design Note: Why Gas is a Host-Level Concern

A natural question is why a "gas" model is not a mandatory, built-in part of the JSL language specification. This is a deliberate architectural decision based on JSL's core design philosophy.

*   **To Maximize Simplicity and Portability:** The primary goal of the JSL core is to be a simple, elegant, and easily embeddable evaluation engine. Forcing a complex gas accounting system into the language specification would dramatically increase the implementation burden. This would make it much harder to create compliant runtimes in different languages, undermining the goal of portability.

*   **To Maintain Flexibility:** Different host environments have vastly different needs. A web server might manage resources via per-request timeouts, while a blockchain requires a strict, deterministic gas model. By defining gas as a host-level *best practice* rather than a language *requirement*, JSL remains flexible enough to be integrated naturally into any of these contexts without imposing a one-size-fits-all solution.

Keeping resource management at the host level preserves the simplicity of the core language while still providing a clear and robust pattern for building secure, production-ready systems.

#### 2. Implement the Principle of Least Capability

When designing host commands, always expose the most specific, narrowly-scoped capability possible. Avoid creating general-purpose "escape hatches."

A good example is a specific, auditable capability for reading a config file:
```json
["def", "config", ["host", "file/read", "/app/data/config.json"]]
```

A dangerous, overly broad capability would be:
```json
["def", "config", ["host", "shell", "cat /app/data/config.json"]]
```
A specific command like `file/read` can be easily secured and audited by the host dispatcher. A `shell` command is a black box that subverts JSL's security model.

#### 3. Maintain Detailed Audit Logs

Because all side effects are reified as data, the host can create a perfect audit trail. Every `["host", ...]` request should be logged with a timestamp, the source of the code, the full request, and the outcome. This is invaluable for security analysis and incident response.

### For JSL Code Developers

#### 1. Never Trust Input

Just as in any other language, you must treat all data coming from an external source as untrusted.

This example shows a function that expects a number for a calculation. It validates the input's type before using it.
```json
["def", "calculate",
  ["lambda", ["input"],
    ["if", ["is_num", "input"],
      ["*", "input", 10],
      ["error", "InvalidInput", "Expected a number"]
    ]
  ]
]
```
Always validate the type and structure of data before using it in your logic.

#### 2. Handle Errors Gracefully

Host commands can fail for many reasons. Robust JSL code should anticipate these failures using the `try` special form.

This example attempts to read a configuration file, but returns a default value if it fails, logging the error as a warning.
```json
["try",
  ["host", "file/read", "/app/config.json"],
  ["lambda", ["err"],
    ["do",
      ["host", "log/warn", ["@", "Config not found, using default: ", ["get", "err", "message"]]],
      { "default_setting": true }
    ]
  ]
]
```
This prevents unexpected host errors from crashing your entire program.
