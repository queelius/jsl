# Design Philosophy

## The Problem with Traditional Code Mobility

Modern distributed systems require seamless code mobility - the ability to send executable code across network boundaries, store it in databases, and reconstruct it in different runtime environments. Traditional approaches face fundamental challenges:

### 1. Serialization Complexity
Most languages require complex serialization frameworks (pickle, protobuf, etc.) that are brittle, version-dependent, and often insecure.

### 2. Runtime Dependencies
Serialized code often depends on specific runtime versions, libraries, or execution contexts that may not be available on the receiving end.

### 3. Security Vulnerabilities
Deserializing code often requires executing arbitrary instructions, creating attack vectors.

### 4. Platform Lock-in
Serialization formats are often language-specific, preventing cross-platform code sharing.

## The JSL Solution

JSL solves these problems by making JSON the native representation of both data AND code. This creates several powerful properties that enable truly network-native programming.

## Theoretical Foundations

### Homoiconicity
Like classic Lisps, JSL code and data share the same representation. However, unlike S-expressions, JSL uses JSON - a universally supported, standardized format with existing tooling and security properties.

**Key Benefits:**
- No parsing ambiguity - JSON has a precise, standardized grammar
- Universal tooling support - every language and platform can handle JSON
- Network transparency - valid JSON travels safely across all network protocols
- Human readability - code can be inspected and modified with standard text tools

### Closure Serializability
The most challenging aspect of code mobility is handling closures (functions that capture their lexical environment). JSL solves this through a sophisticated three-layer architecture:

**1. Prelude Layer** (Non-serializable)
- Contains built-in functions (+, map, filter, etc.)
- Provides computational foundation
- Never transmitted over the wire
- Reconstructed fresh in each runtime

**2. User Layer** (Serializable)  
- Contains user-defined functions and data
- Captures lexical environments
- Safely serializable to JSON
- Transmitted and reconstructed precisely

**3. Wire Layer** (JSON Representation)
- Pure JSON representation of user code
- Contains no executable primitives
- Safe for network transmission
- Platform and language agnostic

**Environment Reconstruction Algorithm:**
When a closure is reconstructed:
1. Deserialize user bindings from JSON
2. Create fresh prelude environment
3. Chain user environment to prelude
4. Restore lexical scoping relationships

This ensures closures always have access to both their captured variables and built-in functions, regardless of where they're reconstructed.

### Wire-Format Transparency
Every JSL value can be serialized to JSON and reconstructed identically in any compliant runtime. This enables:

- **Database storage** of executable code with ACID properties
- **HTTP transmission** of functions using standard web infrastructure  
- **Cross-language interoperability** through JSON's universal support
- **Audit trails** of code execution with complete reproducibility
- **Version control** of code using standard JSON diff/merge tools

## Practical Applications

### 1. Distributed Computing
Send computations to where data resides rather than moving data to computations:

```json
// Send this function to a database or remote service
["lambda", ["data"], 
  ["filter", 
    ["lambda", ["record"], ["=", ["get", "record", "status"], "active"]], 
    "data"]]
```

### 2. Edge Computing  
Deploy and update logic on edge devices dynamically:

```json
// Push new business logic to IoT devices
["lambda", ["sensor_reading"],
  ["if", [">", "sensor_reading", 75],
    ["send-alert", "High temperature detected"],
    ["log", "Normal reading:", "sensor_reading"]]]
```

### 3. Database Functions
Store and execute business logic directly in databases:

```sql
-- Store JSL function in database
INSERT INTO business_rules (name, logic) VALUES (
  'pricing_calculator',
  '["lambda", ["item", "customer"], 
     ["*", ["get", "item", "base_price"], 
          ["get-discount-rate", "customer"]]]'
);

-- Execute stored logic
SELECT eval_jsl(logic, item_data, customer_data) 
FROM business_rules WHERE name = 'pricing_calculator';
```

### 4. Microservices
Share functional components across service boundaries:

```json
// Common validation function used by multiple services
{
  "validate_email": ["lambda", ["email"],
    ["and", 
      ["contains?", "email", "@"],
      [">", ["str-length", "email"], 5]]],
  "validate_user": ["lambda", ["user"],
    ["and",
      ["validate_email", ["get", "user", "email"]],
      [">", ["str-length", ["get", "user", "name"]], 2]]]
}
```

### 5. Code as Configuration
Express complex configurations as executable code:

```json
// Configuration that adapts based on environment
{
  "database_config": ["template", {
    "host": {"$": ["if", ["=", "env", "prod"], "prod-db.com", "localhost"]},
    "pool_size": {"$": ["if", ["=", "env", "prod"], 20, 5]},
    "timeout": {"$": ["*", ["get-cpu-count"], 1000]}
  }]
}
```

### 6. Live Programming
Update running systems by transmitting new code:

```json
// Hot-swap business logic without restarting services
{
  "event": "update_handler",
  "handler": ["lambda", ["request"],
    ["do",
      ["log", "Processing request:", ["get", "request", "id"]],
      ["validate-input", "request"],
      ["process-business-logic", "request"],
      ["send-response", "request"]]]
}
```

## Security Model

JSL's security model is based on **capability restriction** rather than code signing or sandboxing:

### Transmitted Code is Always Safe
- Contains only JSON data structures
- No executable primitives or system calls
- Cannot access unauthorized resources
- Deterministic evaluation (no hidden side effects)

### Capabilities Come from Environment
- All dangerous operations (I/O, system calls) come from the prelude
- Receiving environment controls what capabilities are available
- Can customize prelude to provide only safe operations
- Host can audit and approve all available operations

### Example: Sandboxed Environment

```python
# Create restricted prelude for user-submitted code
safe_prelude = {
    # Math operations: OK
    "+": lambda *args: sum(args),
    "*": lambda *args: math.prod(args),
    
    # String operations: OK  
    "str-concat": lambda *args: ''.join(str(arg) for arg in args),
    
    # File I/O: BLOCKED
    # "read-file": <-- not included
    # "write-file": <-- not included
    
    # Network: BLOCKED
    # "http-get": <-- not included
}

# User code can only use provided capabilities
user_code = ["str-concat", "Result: ", ["+", 2, 3]]
result = eval_with_prelude(user_code, safe_prelude)  # "Result: 5"
```

This model makes JSL suitable for scenarios where traditional code mobility would be too dangerous, such as:
- User-submitted code execution
- Cross-tenant execution in multi-tenant systems  
- Code execution in untrusted environments
- Automated code generation and execution

## Implementation Architecture

The JSL runtime consists of three layers:

### 1. Prelude Layer
Non-serializable built-in functions (+, map, get, etc.) that form the computational foundation

### 2. User Layer
Serializable functions and data defined by user programs

### 3. Wire Layer
JSON representation that can be transmitted and reconstructed

This separation ensures that transmitted code is always safe (contains no executable primitives) while remaining fully functional when reconstructed with a compatible prelude.

## Security Model

JSL's security model is based on capability restriction:

- **Transmitted code cannot contain arbitrary executable primitives**
- **All capabilities come from the receiving environment's prelude**
- **The prelude can be customized to provide only safe operations**
- **Code execution is deterministic and sandboxable**

This makes JSL suitable for scenarios where traditional code mobility would be too dangerous, such as user-submitted code or cross-tenant execution.

## SICP-Inspired Design

JSL follows the elegant principles outlined in "Structure and Interpretation of Computer Programs":

### Simplicity
Everything is built from a small set of primitives (atoms, lists, functions)

### Composability
Complex operations are created by combining simple ones

### Abstraction
Higher-level concepts are built on lower-level foundations

### Uniformity
A consistent evaluation model applies throughout the language

### Extensibility
New capabilities are added through composition, not special cases

This approach creates a language that is both theoretically elegant and practically useful for distributed computing scenarios.
