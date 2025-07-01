# Custom Commands

## Overview

While JHIP defines a standard set of built-in commands, JSL hosts can extend the protocol with custom commands tailored to their specific environments and use cases. This extensibility allows JSL to integrate with any system while maintaining the security and audit benefits of the JHIP protocol.

## Command Design Principles

### Naming Conventions

Custom commands should follow a hierarchical naming structure:

```
<namespace>/<category>/<operation>
```

Examples:
- `myapp/user/create`
- `aws/s3/upload`
- `database/postgres/query`
- `ml/tensorflow/predict`

### Command Categories

#### System Integration
```json
["host", "system/service/status", "nginx"]
["host", "system/process/kill", "12345"]
["host", "system/disk/usage", "/var/log"]
```

#### Cloud Services
```json
["host", "aws/s3/upload", "bucket-name", "key", "data"]
["host", "gcp/storage/download", "bucket", "object"]
["host", "azure/blob/delete", "container", "blob-name"]
```

#### Database Operations
```json
["host", "postgres/query", "SELECT * FROM users", []]
["host", "redis/set", "key", "value", 3600]
["host", "mongodb/find", "collection", {"status": "active"}]
```

#### Machine Learning
```json
["host", "tensorflow/predict", "model-id", {"features": [1, 2, 3]}]
["host", "pytorch/train", "model-config", "training-data"]
```

#### Business Logic
```json
["host", "ecommerce/order/create", {"product": "123", "quantity": 2}]
["host", "crm/contact/update", "contact-id", {"email": "new@example.com"}]
```

## Implementation Guidelines

### Command Handler Interface

```python
class CustomCommandHandler:
    def __init__(self, command_id: str):
        self.command_id = command_id
    
    def validate_args(self, args: list) -> bool:
        """Validate command arguments"""
        pass
    
    def execute(self, args: list) -> any:
        """Execute the command and return result"""
        pass
    
    def get_permissions(self) -> list:
        """Return required permissions for this command"""
        pass
```

### Registration Pattern

```python
# Register custom command handler
jsl_host.register_command("myapp/user/create", UserCreateHandler())
jsl_host.register_command("myapp/user/delete", UserDeleteHandler())
jsl_host.register_command("myapp/order/process", OrderProcessHandler())
```

### Error Handling

Custom commands must return errors in standard JHIP format:

```json
{
  "$jsl_host_error": {
    "type": "CustomCommandError",
    "message": "User creation failed: email already exists",
    "details": {
      "command": "myapp/user/create",
      "error_code": "DUPLICATE_EMAIL",
      "field": "email",
      "value": "user@example.com"
    }
  }
}
```

## Security Considerations

### Permission System

```python
class PermissionChecker:
    def check_command_permission(self, command_id: str, user_context: dict) -> bool:
        # Example permission check
        if command_id.startswith("admin/"):
            return user_context.get("role") == "admin"
        
        if command_id.startswith("user/"):
            return user_context.get("authenticated", False)
        
        return False
```

### Input Validation

```python
def validate_user_create_args(args):
    if len(args) != 1:
        raise ValueError("Expected 1 argument")
    
    user_data = args[0]
    if not isinstance(user_data, dict):
        raise ValueError("User data must be object")
    
    required_fields = ["email", "name"]
    for field in required_fields:
        if field not in user_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", user_data["email"]):
        raise ValueError("Invalid email format")
```

### Resource Limits

```python
class ResourceLimiter:
    def __init__(self):
        self.limits = {
            "max_execution_time": 30,  # seconds
            "max_memory_usage": 100 * 1024 * 1024,  # 100MB
            "max_network_requests": 10,
            "max_file_size": 10 * 1024 * 1024  # 10MB
        }
    
    def check_limits(self, command_id: str, resource_usage: dict):
        # Implement resource checking logic
        pass
```

## Example Implementations

### E-commerce Integration

```json
// Create order
["host", "ecommerce/order/create", {
  "customer_id": "cust_123",
  "items": [
    {"product_id": "prod_456", "quantity": 2, "price": 29.99},
    {"product_id": "prod_789", "quantity": 1, "price": 19.99}
  ],
  "shipping_address": {
    "street": "123 Main St",
    "city": "Anytown",
    "zip": "12345"
  }
}]

// Response
{
  "order_id": "order_abc123",
  "total": 79.97,
  "status": "pending",
  "estimated_delivery": "2025-01-10"
}
```

### Content Management

```json
// Publish article
["host", "cms/article/publish", {
  "title": "Introduction to JSL",
  "content": "JSL is a network-native programming language...",
  "author": "john@example.com",
  "tags": ["programming", "json", "distributed"],
  "publish_date": "2025-01-01T12:00:00Z"
}]

// Response  
{
  "article_id": "art_456",
  "url": "https://blog.example.com/intro-to-jsl",
  "status": "published"
}
```

### Analytics Integration

```json
// Track event
["host", "analytics/event/track", {
  "event_name": "user_signup",
  "user_id": "user_789",
  "properties": {
    "source": "organic",
    "plan": "premium",
    "trial_days": 30
  },
  "timestamp": "2025-01-01T12:00:00Z"
}]

// Query metrics
["host", "analytics/metrics/query", {
  "metric": "user_signups",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "group_by": ["source", "plan"]
}]
```

## Testing Custom Commands

### Unit Testing

```python
def test_user_create_command():
    handler = UserCreateHandler()
    
    # Test successful creation
    result = handler.execute([{
        "email": "test@example.com",
        "name": "Test User"
    }])
    
    assert result["user_id"] is not None
    assert result["email"] == "test@example.com"
    
    # Test validation error
    with pytest.raises(ValidationError):
        handler.execute([{"email": "invalid"}])
```

### Integration Testing

```python
def test_command_through_jsl():
    jsl_code = [
        "host", "myapp/user/create", {
            "email": "integration@example.com",
            "name": "Integration Test"
        }
    ]
    
    result = jsl_runtime.evaluate(jsl_code)
    assert result["user_id"] is not None
```

### Security Testing

```python
def test_command_security():
    # Test unauthorized access
    with pytest.raises(PermissionError):
        handler.execute_as_user([{"email": "test@example.com"}], user_role="guest")
    
    # Test injection attacks
    malicious_input = {"email": "'; DROP TABLE users; --"}
    with pytest.raises(ValidationError):
        handler.execute([malicious_input])
```

## Documentation Standards

### Command Documentation Template

```markdown
### myapp/user/create

Creates a new user account in the system.

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
["host", "myapp/user/create", {
  "email": "john@example.com",
  "name": "John Doe",
  "role": "editor"
}]
```

**Error Types:**
- `DUPLICATE_EMAIL`: Email address already exists
- `INVALID_EMAIL`: Email format is invalid
- `PERMISSION_DENIED`: Insufficient permissions
```

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

### Monitoring and Observability

1. **Metrics Collection**: Track command usage, success rates, and performance
2. **Logging**: Log all command executions for audit and debugging
3. **Health Checks**: Implement health checks for external dependencies
4. **Alerting**: Set up alerts for command failures and performance issues

Custom commands extend JSL's capabilities while maintaining the security, transparency, and auditability that make JSL suitable for distributed systems. By following these guidelines, you can create robust, secure, and maintainable custom command implementations.
