# Host Commands

## Overview

JHIP defines the protocol structure for host interactions, but **all commands are host-specific** and defined by individual host implementations. Each JSL host chooses which commands to support based on their specific environment and use cases. This extensibility allows JSL to integrate with any system while maintaining the security and audit benefits of the JHIP protocol.

There are no "built-in" or "standard" commands - JHIP is purely a communication protocol. However, community conventions have emerged for common operations.

## Community Conventions

While hosts define their own command sets, these naming patterns are commonly used:

### File System Operations
```json
["host", "@file/read", "@/path/to/file"]
["host", "@file/write", "@/path/to/file", "@content"]
["host", "@file/exists", "@/path/to/file"]
["host", "@file/list", "@/path/to/directory"]
["host", "@file/delete", "@/path/to/file"]
```

### HTTP Operations
```json
["host", "@http/get", "@https://api.example.com/data"]
["host", "@http/post", "@https://api.example.com/submit", {"@key": "@value"}]
["host", "@http/put", "@https://api.example.com/update", {"@data": "@updated"}]
["host", "@http/delete", "@https://api.example.com/item/123"]
```

### Logging Operations
```json
["host", "@log/debug", "@Debug message", {"@context": "@additional info"}]
["host", "@log/info", "@Application started successfully"]
["host", "@log/warn", "@Warning message"]
["host", "@log/error", "@Error occurred", {"@error_code": 500}]
```

### System Operations
```json
["host", "@env/get", "@PATH"]
["host", "@time/now"]
["host", "@time/format", "@2025-01-01T12:00:00Z", "@YYYY-MM-DD"]
["host", "@random/uuid"]
["host", "@process/exec", "@ls", ["@", ["@-la", "@/tmp"]]]
```

### Database Operations
```json
["host", "@db/query", "@SELECT * FROM users WHERE active = ?", ["@", [true]]]
["host", "@db/transaction", ["@", [
  ["@INSERT INTO logs (message) VALUES (?)", ["@", ["@Log entry 1"]]],
  ["@INSERT INTO logs (message) VALUES (?)", ["@", ["@Log entry 2"]]]
]]]
```

### Cryptographic Operations
```json
["host", "@crypto/hash", "@sha256", "@data to hash"]
["host", "@crypto/random", 32]
```

## Command Design Principles

### Naming Conventions

Host commands should follow a hierarchical naming structure:

```
<namespace>/<category>/<operation>
```

Examples:
- `myapp/user/create`
- `aws/s3/upload`
- `database/postgres/query`
- `ml/tensorflow/predict`

### Command Categories

#### Cloud Services
```json
["host", "@aws/s3/upload", "@bucket-name", "@key", "data"]
["host", "@gcp/storage/download", "@bucket", "@object"]
["host", "@azure/blob/delete", "@container", "@blob-name"]
```

#### Machine Learning
```json
["host", "@tensorflow/predict", "@model-id", {"@features": ["@", [1, 2, 3]]}]
["host", "@pytorch/train", "@model-config", "training-data"]
```

#### Business Logic
```json
["host", "@ecommerce/order/create", {"@product": "@123", "@quantity": 2}]
["host", "@crm/contact/update", "@contact-id", {"@email": "@new@example.com"}]
```

## Implementation Guidelines

### Command Handler Interface

```python
class HostCommandHandler:
    def __init__(self, command_id: str):
        self.command_id = command_id
    
    def validate_args(self, args: list) -> bool:
        """Validate command arguments"""
        # Implement argument validation
        pass
    
    def execute(self, args: list) -> any:
        """Execute the command and return result"""
        # Implement command logic
        pass
    
    def get_permissions(self) -> list:
        """Return required permissions for this command"""
        # Return list of required permissions
        pass
```

### Registration Pattern

```python
# Register host command handlers
jsl_host.register_command("file/read", FileReadHandler())
jsl_host.register_command("http/get", HttpGetHandler())
jsl_host.register_command("myapp/user/create", UserCreateHandler())
```

### Error Handling

All commands must return errors in standard JHIP format:

```json
{
  "$jsl_error": {
    "type": "CommandError",
    "message": "File not found",
    "details": {
      "command": "file/read",
      "path": "/nonexistent/file"
    }
  }
}
```

## Example Command Implementations

### File Read Command

```python
class FileReadHandler(HostCommandHandler):
    def validate_args(self, args: list) -> bool:
        return len(args) == 1 and isinstance(args[0], str)
    
    def execute(self, args: list) -> str:
        path = args[0]
        try:
            with open(path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            return {
                "$jsl_error": {
                    "type": "FileNotFound",
                    "message": f"File does not exist: {path}",
                    "details": {"path": path, "operation": "file/read"}
                }
            }
        except PermissionError:
            return {
                "$jsl_error": {
                    "type": "PermissionDenied", 
                    "message": f"Permission denied: {path}",
                    "details": {"path": path, "operation": "file/read"}
                }
            }
    
    def get_permissions(self) -> list:
        return ["file.read"]
```

### HTTP GET Command

```python
import requests

class HttpGetHandler(HostCommandHandler):
    def validate_args(self, args: list) -> bool:
        return len(args) >= 1 and isinstance(args[0], str)
    
    def execute(self, args: list) -> dict:
        url = args[0]
        headers = args[1] if len(args) > 1 else {}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            return {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }
        except requests.exceptions.Timeout:
            return {
                "$jsl_error": {
                    "type": "NetworkError",
                    "message": "Request timeout",
                    "details": {"url": url, "timeout_ms": 30000}
                }
            }
        except requests.exceptions.ConnectionError:
            return {
                "$jsl_error": {
                    "type": "NetworkError", 
                    "message": "Connection failed",
                    "details": {"url": url}
                }
            }
    
    def get_permissions(self) -> list:
        return ["network.http"]
```

### Custom Business Logic Command

```python
class UserCreateHandler(HostCommandHandler):
    def validate_args(self, args: list) -> bool:
        if len(args) != 1 or not isinstance(args[0], dict):
            return False
        
        user_data = args[0]
        required_fields = ["email", "name"]
        return all(field in user_data for field in required_fields)
    
    def execute(self, args: list) -> dict:
        user_data = args[0]
        
        # Validate email format
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", user_data["email"]):
            return {
                "$jsl_error": {
                    "type": "ValidationError",
                    "message": "Invalid email format",
                    "details": {"field": "email", "value": user_data["email"]}
                }
            }
        
        # Check for duplicate email
        if self.email_exists(user_data["email"]):
            return {
                "$jsl_error": {
                    "type": "DuplicateError",
                    "message": "Email already exists",
                    "details": {"field": "email", "value": user_data["email"]}
                }
            }
        
        # Create user
        user_id = self.create_user_in_database(user_data)
        
        return {
            "user_id": user_id,
            "email": user_data["email"],
            "created_at": datetime.utcnow().isoformat()
        }
    
    def get_permissions(self) -> list:
        return ["user.create"]
```

## Security Considerations

### Permission System

```python
class PermissionChecker:
    def check_command_permission(self, command_id: str, user_context: dict) -> bool:
        # Example permission logic
        user_permissions = user_context.get("permissions", [])
        
        # Admin bypass
        if "admin" in user_context.get("roles", []):
            return True
        
        # Check specific command permissions
        if command_id.startswith("file/"):
            return "file.access" in user_permissions
        
        if command_id.startswith("http/"):
            return "network.http" in user_permissions
        
        # Custom business logic permissions
        if command_id.startswith("myapp/"):
            return f"myapp.{command_id.split('/')[-1]}" in user_permissions
        
        return False
```

### Input Validation

```python
def validate_command_args(command_id: str, args: list):
    """Validate arguments for security and correctness"""
    
    if command_id == "file/read":
        if len(args) != 1 or not isinstance(args[0], str):
            raise ValueError("file/read requires exactly one string argument")
        
        # Prevent directory traversal
        path = os.path.normpath(args[0])
        if path.startswith("../") or "/../" in path:
            raise ValueError("Directory traversal not allowed")
    
    elif command_id == "process/exec":
        if len(args) < 1:
            raise ValueError("process/exec requires at least one argument")
        
        # Whitelist allowed commands
        allowed_commands = ["ls", "cat", "echo", "date"]
        if args[0] not in allowed_commands:
            raise ValueError(f"Command not allowed: {args[0]}")
```

### Resource Limits

```python
class ResourceLimiter:
    def __init__(self):
        self.limits = {
            "max_execution_time": 30,  # seconds
            "max_memory_usage": 100 * 1024 * 1024,  # 100MB
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "max_network_requests_per_minute": 60
        }
        self.usage_tracking = {}
    
    def check_limits(self, command_id: str, user_id: str):
        # Implement rate limiting and resource checking
        current_time = time.time()
        
        # Check rate limits
        user_requests = self.usage_tracking.get(user_id, [])
        recent_requests = [t for t in user_requests if current_time - t < 60]
        
        if len(recent_requests) >= self.limits["max_network_requests_per_minute"]:
            raise Exception("Rate limit exceeded")
        
        # Track this request
        self.usage_tracking[user_id] = recent_requests + [current_time]
```

## Testing Host Commands

### Unit Testing

```python
def test_file_read_command():
    handler = FileReadHandler()
    
    # Test successful read
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        f.flush()
        
        result = handler.execute([f.name])
        assert result == "test content"
    
    # Test file not found
    result = handler.execute(["/nonexistent/file"])
    assert "$jsl_error" in result
    assert result["$jsl_error"]["type"] == "FileNotFound"
```

### Integration Testing

```python
def test_command_through_jsl():
    # Test command through JSL runtime
    jsl_code = ["host", "@file/read", "@/tmp/test.txt"]
    
    # Mock the host command
    with patch('jsl_host.execute_command') as mock_execute:
        mock_execute.return_value = "mocked file content"
        
        result = jsl_runtime.evaluate(jsl_code)
        assert result == "mocked file content"
        
        mock_execute.assert_called_once_with("file/read", ["/tmp/test.txt"])
```

## Documentation Template

Use this template when documenting host commands:

**Command:** `myapp/user/create`

**Description:** Creates a new user account in the system.

**Parameters:**
- `user_data` (object): User information
  - `email` (string, required): User's email address
  - `name` (string, required): User's full name
  - `role` (string, optional): User role, defaults to "user"

**Returns:** 
- `user_id` (string): Unique identifier for created user
- `email` (string): Confirmed email address
- `created_at` (string): ISO timestamp of creation

**Permissions Required:** `user.create`

**Example:**
```json
["host", "@myapp/user/create", {
  "@email": "@john@example.com",
  "@name": "@John Doe",
  "@role": "@editor"
}]
```

**Error Types:**
- `DUPLICATE_EMAIL`: Email address already exists
- `INVALID_EMAIL`: Email format is invalid
- `PERMISSION_DENIED`: Insufficient permissions

## Best Practices

### Design Guidelines

1. **Atomic Operations**: Commands should perform single, well-defined operations
2. **Idempotency**: Where possible, commands should be idempotent
3. **Error Transparency**: Provide clear, actionable error messages
4. **Resource Efficiency**: Minimize resource usage and implement proper cleanup
5. **Backward Compatibility**: Maintain compatibility when updating commands

### Performance Optimization

1. **Caching**: Cache frequently accessed data
2. **Connection Pooling**: Reuse database and network connections
3. **Async Operations**: Use async patterns for I/O operations
4. **Batch Processing**: Support batch operations where appropriate

### Security Best Practices

1. **Input Sanitization**: Always validate and sanitize inputs
2. **Principle of Least Privilege**: Grant minimal required permissions
3. **Audit Logging**: Log all command executions for security analysis
4. **Rate Limiting**: Implement rate limits to prevent abuse
5. **Resource Limits**: Set timeouts and size limits on operations

Host commands are how JSL integrates with the real world while maintaining security, transparency, and auditability. By following these guidelines and community conventions, you can create robust, secure, and maintainable host command implementations that work well with the broader JSL ecosystem.