# JSL Host Interaction Protocol (JHIP) - Version 1.0

## Introduction

The JSL Host Interaction Protocol (JHIP) defines how JSL programs interact with the host environment for side effects. JSL's core philosophy is to reify effects as data - side effects are described as JSON messages rather than executed directly, allowing the host environment to control, audit, and secure all external interactions.

## Core Principles

- **Effect Reification**: Side effects are described as data, not executed directly
- **Host Authority**: The host controls what operations are permitted and how they execute
- **JSON-Native**: All messages are valid JSON for universal compatibility
- **Synchronous Model**: From JSL's perspective, host operations are synchronous
- **Capability-Based Security**: Hosts provide only the capabilities they choose to expose

## Request Structure

JSL programs request host operations using the `host` special form:

```json
["host", "command", "arg1", "arg2", ...]
```

This creates a request message with the following structure:

```json
{
  "command": "string",
  "args": ["arg1", "arg2", ...]
}
```

### Request Examples

**File Operations:**
```json
// JSL code
["host", "@file/read", "@/tmp/data.txt"]

// Request message
{
  "command": "file/read",
  "args": ["/tmp/data.txt"]
}
```

**HTTP Requests:**
```json
// JSL code
["host", "@http/get", "@https://api.example.com/users", {"@Authorization": "@Bearer token"}]

// Request message
{
  "command": "http/get", 
  "args": ["https://api.example.com/users", {"Authorization": "Bearer token"}]
}
```

**Logging:**
```json
// JSL code
["host", "@log/info", "@User logged in", {"@user_id": 123}]

// Request message
{
  "command": "log/info",
  "args": ["User logged in", {"user_id": 123}]
}
```

## Response Structure

The host responds with either a success value or an error object.

### Success Response

Any valid JSON value represents success:

```json
// File read success
"file content as string"

// HTTP response success
{
  "status": 200,
  "headers": {"content-type": "application/json"},
  "body": {"users": [...]}
}

// Operation with no return value
null
```

### Error Response

Errors use a standard structure to distinguish them from successful `null`, `false`, or empty results:

```json
{
  "$jsl_error": {
    "type": "ErrorType",
    "message": "Human readable description",
    "details": {}
  }
}
```

**Error Fields:**
- `type`: Error category (e.g., "FileNotFound", "NetworkError", "PermissionDenied")
- `message`: Clear description for developers
- `details`: Additional structured information (optional)

**Error Examples:**

```json
// File not found
{
  "$jsl_error": {
    "type": "FileNotFound",
    "message": "File does not exist",
    "details": {
      "path": "/tmp/missing.txt",
      "operation": "file/read"
    }
  }
}

// Permission denied
{
  "$jsl_error": {
    "type": "PermissionDenied", 
    "message": "Insufficient permissions for operation",
    "details": {
      "operation": "file/write",
      "path": "/etc/passwd",
      "required_permission": "root"
    }
  }
}

// Network error
{
  "$jsl_error": {
    "type": "NetworkError",
    "message": "Connection timeout",
    "details": {
      "url": "https://api.example.com",
      "timeout_ms": 5000
    }
  }
}
```

## Standard Commands

While hosts define their own command sets, these common patterns are recommended:

### File System
- `@file/read` - Read file content as string
- `@file/write` - Write string to file  
- `@file/exists` - Check if file exists
- `@file/list` - List directory contents
- `@file/delete` - Delete file or directory

### HTTP
- `@http/get` - GET request
- `@http/post` - POST request
- `@http/put` - PUT request
- `@http/delete` - DELETE request

### Logging
- `@log/debug` - Debug level log
- `@log/info` - Info level log
- `@log/warn` - Warning level log
- `@log/error` - Error level log

### System
- `@env/get` - Get environment variable
- `@time/now` - Current timestamp
- `@random/uuid` - Generate UUID
- `@process/exec` - Execute system command

## Protocol Flow

1. **JSL Evaluation**: JSL encounters `["host", "command", ...args]`
2. **Argument Evaluation**: All arguments are evaluated to JSON values
3. **Message Construction**: Create request message with command and args
4. **Host Processing**: Host validates, executes, and responds
5. **Response Handling**: Success value returned or error thrown in JSL

## Security Model

JHIP implements capability-based security:

- **Host Controls Access**: Only commands explicitly enabled by the host are available
- **Argument Validation**: Host validates all arguments before execution
- **Resource Limits**: Host can impose limits on operations (file size, request timeouts, etc.)
- **Audit Trail**: All host interactions can be logged for security analysis

## Implementation Notes

### Error Handling in JSL

JSL implementations should convert JHIP error responses into JSL errors:

```json
// If host returns error, JSL should throw
["try",
  ["host", "file/read", "/missing.txt"],
  ["lambda", ["err"], 
    ["get", "err", "message"]]]
```

### Async Implementation

While JSL sees synchronous operations, hosts may implement async processing:

- Queue requests for batch processing
- Use connection pooling for HTTP requests
- Implement timeout and retry logic
- Cache results when appropriate

### Testing

JHIP enables easy testing by mocking host responses:

```json
// Mock successful file read
{"command": "file/read", "args": ["/data.txt"]} 
→ "mocked file content"

// Mock error response  
{"command": "file/read", "args": ["/missing.txt"]}
→ {"$jsl_error": {"type": "FileNotFound", "message": "File not found"}}
```
