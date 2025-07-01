# Built-in Commands

## Overview

JHIP (JSL Host Interaction Protocol) defines a standard set of built-in commands that JSL host implementations are expected to support. These commands provide essential functionality for file I/O, network operations, logging, and system interaction.

## File System Operations

### File Reading

```json
["host", "file/read", "/path/to/file"]
```

Reads the entire contents of a file as a string.

**Parameters:**
- `path` (string): Absolute or relative path to the file

**Returns:** String content of the file

**Error Types:**
- `FileNotFound`: File does not exist
- `PermissionDenied`: Insufficient permissions to read file
- `FileSystemError`: General I/O error

### File Writing

```json
["host", "file/write", "/path/to/file", "content"]
```

Writes string content to a file, creating it if it doesn't exist.

**Parameters:**
- `path` (string): Path where to write the file
- `content` (string): Content to write

**Returns:** `null` on success

### Directory Listing

```json
["host", "file/list", "/path/to/directory"]
```

Lists contents of a directory.

**Returns:** Array of filenames

## Network Operations

### HTTP GET

```json
["host", "http/get", "https://api.example.com/data"]
```

Performs HTTP GET request.

**Returns:** Response body as string

### HTTP POST

```json
["host", "http/post", "https://api.example.com/submit", {"key": "value"}]
```

Performs HTTP POST request with JSON payload.

## Logging Operations

### Info Logging

```json
["host", "log/info", "Application started successfully"]
```

Logs an informational message.

**Returns:** `null`

### Error Logging

```json
["host", "log/error", "Failed to process request", {"error_code": 500}]
```

Logs an error message with optional structured data.

## System Operations

### Environment Variable Access

```json
["host", "env/get", "PATH"]
```

Retrieves environment variable value.

### Command Execution

```json
["host", "exec", "ls", ["-la", "/tmp"]]
```

Executes system command with arguments.

**Security Note:** This operation should be heavily restricted in production environments.

## Database Operations

### Query Execution

```json
["host", "db/query", "SELECT * FROM users WHERE active = ?", [true]]
```

Executes parameterized database query.

### Transaction Operations

```json
["host", "db/transaction", [
  ["INSERT INTO logs (message) VALUES (?)", ["Log entry 1"]],
  ["INSERT INTO logs (message) VALUES (?)", ["Log entry 2"]]
]]
```

Executes multiple operations in a transaction.

## Time and Date Operations

### Current Timestamp

```json
["host", "time/now"]
```

Returns current UTC timestamp.

### Date Formatting

```json
["host", "time/format", "2025-01-01T12:00:00Z", "YYYY-MM-DD"]
```

Formats timestamp according to format string.

## Cryptographic Operations

### Hash Generation

```json
["host", "crypto/hash", "sha256", "data to hash"]
```

Generates cryptographic hash of input data.

### Random Generation

```json
["host", "crypto/random", 32]
```

Generates cryptographically secure random bytes.

## Implementation Guidelines

### Security Considerations

1. **Input Validation**: All parameters must be validated
2. **Path Sanitization**: File paths must be sanitized to prevent directory traversal
3. **Resource Limits**: Operations should have timeouts and size limits
4. **Capability Checking**: Verify permissions before executing operations

### Error Handling

All commands should return consistent error responses:

```json
{
  "$jsl_host_error": {
    "type": "CommandError",
    "message": "Descriptive error message",
    "details": {
      "command": "file/read",
      "parameters": ["/nonexistent/file"]
    }
  }
}
```

### Performance Considerations

- Implement connection pooling for network operations
- Use streaming for large file operations
- Cache frequently accessed data where appropriate
- Implement proper timeout handling

## Host-Specific Extensions

Hosts may implement additional commands beyond this standard set. Extension commands should follow the naming convention:

```json
["host", "vendor/operation", ...args]
```

For example:
```json
["host", "aws/s3/get", "bucket-name", "object-key"]
["host", "docker/container/start", "container-id"]
```
