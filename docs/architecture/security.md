# Security Model

## Overview

JSL's security model is built on the principle of **effect reification** and **capability restriction**. Unlike traditional languages where security is layered on top, JSL's design makes security an intrinsic property of the language itself.

## Core Security Principles

### 1. No Arbitrary Code Execution

JSL code is data, not executable machine instructions. This fundamental property eliminates entire classes of security vulnerabilities:

- **No buffer overflows**: JSON parsing has well-defined bounds
- **No code injection**: Code structure is validated against JSON schema
- **No direct system calls**: All system interaction is mediated
- **No memory corruption**: Interpreter manages all memory access

### 2. Effect Reification

All side effects are represented as data structures rather than executed directly:

```json
// Instead of executing: fs.writeFile("/etc/passwd", "malicious")
// JSL represents the intent as data:
["host", "file/write", "/etc/passwd", "content"]
```

**Benefits:**
- **Auditable**: All effects can be logged and inspected
- **Controllable**: Host can deny, modify, or sandbox effects
- **Transparent**: Effect intentions are visible before execution
- **Reversible**: Effects can be undone or compensated

### 3. Host Authority

The host environment has complete control over what operations are permitted:

- **Capability-based**: Only explicitly granted capabilities are available
- **Deny by default**: Unknown operations are rejected
- **Fine-grained**: Permissions can be specific to resources or operations
- **Context-aware**: Permissions can vary based on code source or runtime context

## Security Boundaries

### Runtime Boundary

JSL code executes within the confines of the JSL interpreter:

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

### Network Boundary

Code transmitted over networks is inherently safe:

- **JSON format**: Standard, well-understood parsing
- **No executable content**: Code requires interpreter to run
- **Validation**: Structure can be validated before execution
- **Sandboxing**: Execution environment is controlled

### Storage Boundary

Stored JSL code poses no security risks:

- **Inert data**: Code is data until explicitly executed
- **Version independence**: JSON structure is stable
- **Inspection**: Code can be analyzed without execution
- **Transformation**: Code can be modified safely

## Threat Model

### Threats JSL Prevents

1. **Code Injection Attacks**
   - JSON structure prevents arbitrary code construction
   - Host validates all external inputs

2. **Privilege Escalation**
   - Capabilities are explicitly granted, not inherited
   - No direct system access from JSL code

3. **Resource Exhaustion**
   - Host can limit computation resources
   - JHIP allows resource monitoring and control

4. **Data Exfiltration**
   - All data access goes through controlled channels
   - Host can audit and restrict data access

### Threats Requiring Host Implementation

1. **Denial of Service**
   - Host must implement resource limits
   - Computation timeouts and memory limits

2. **Logic Bombs**
   - Host can implement execution monitoring
   - Behavioral analysis of code patterns

3. **Covert Channels**
   - Host must control timing and resource usage
   - Monitoring of computational patterns

## Security Best Practices

### For Host Implementations

1. **Capability Minimization**
   ```json
   // Good: Specific capability
   ["host", "file/read", "/app/data/config.json"]
   
   // Bad: Overly broad capability
   ["host", "shell", "cat /app/data/config.json"]
   ```

2. **Input Validation**
   - Validate all JHIP requests
   - Sanitize file paths and arguments
   - Check resource bounds

3. **Audit Logging**
   ```json
   {
     "timestamp": "2025-01-01T12:00:00Z",
     "code_source": "user@example.com",
     "operation": ["host", "file/read", "/sensitive/data"],
     "result": "success",
     "resource_usage": {"cpu_ms": 10, "memory_kb": 256}
   }
   ```

4. **Resource Limits**
   - CPU time limits
   - Memory usage caps
   - Network bandwidth restrictions
   - File size limits

### For JSL Code

1. **Principle of Least Privilege**
   - Request only necessary capabilities
   - Use specific rather than general operations

2. **Error Handling**
   ```json
   ["if", ["host", "file/exists", "/tmp/data.json"],
     ["host", "file/read", "/tmp/data.json"],
     null]
   ```

3. **Input Sanitization**
   - Validate external data before processing
   - Use type predicates to check assumptions

## Deployment Security

### Secure Code Distribution

1. **Code Signing**
   - Cryptographically sign JSL code
   - Verify signatures before execution

2. **Content Validation**
   - Validate JSON structure
   - Check for malicious patterns
   - Verify code against policies

3. **Sandboxed Execution**
   - Isolate code execution environments
   - Separate capabilities for different code sources

### Network Security

1. **Transport Security**
   - Use TLS for code transmission
   - Implement mutual authentication

2. **Code Integrity**
   - Hash verification of transmitted code
   - Detect tampering during transmission

3. **Access Control**
   - Authenticate code sources
   - Authorize based on code origin

## Security Monitoring

### Runtime Monitoring

- **Effect Tracking**: Monitor all JHIP requests
- **Resource Usage**: Track CPU, memory, and I/O usage
- **Behavioral Analysis**: Detect anomalous patterns

### Audit Capabilities

- **Complete Effect Log**: Record all external interactions
- **Code Provenance**: Track code sources and modifications
- **Decision Trails**: Log all security decisions

### Incident Response

- **Code Isolation**: Ability to quarantine suspicious code
- **Effect Rollback**: Undo harmful effects where possible
- **Forensic Analysis**: Detailed investigation capabilities

This security model ensures that JSL maintains its promise of safe code mobility while providing the transparency and control necessary for secure distributed computing.
