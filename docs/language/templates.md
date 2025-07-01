# JSON Templates

## Overview

JSL's JSON templating system provides a clean, consistent way to create dynamic JSON structures. Templates use reversed sigils from regular JSL: literal strings are the default, and variables are marked with `@`. When embedding JSL expressions, normal JSL syntax applies within the expression.

## Design Principles

1. **Reversed Sigils**: In templates, literals are default and variables use `@`
2. **JSL Consistency**: Embedded JSL expressions use standard JSL syntax
3. **S-Expression Structure**: Template expressions follow `["$eval", ...]` pattern
4. **Type Preservation**: Template resolution preserves JSON types
5. **JSON Compatibility**: Templates are valid JSON documents

## Template Syntax

### Template Context vs JSL Context

| Context | Literals | Variables |
|---------|----------|-----------|
| **Template** | `"hello"` | `"@username"` |
| **JSL Code** | `"@hello"` | `"username"` |
| **Template $eval** | `["$eval", ["str", "@hello"]]` | `["$eval", ["get", "username"]]` |

### Basic Template Elements

```json
{
  "literal": "Hello World",              // Template literal
  "variable": "@username",               // Template variable lookup
  "interpolated": "Hello @first @last!", // Template string interpolation
  "computed": ["$eval", ["+", "@age", 1]] // JSL expression (JSL syntax inside)
}
```

### String Interpolation

Embed variables within literal strings using `@variable` syntax:

```json
{
  "greeting": "Hello @username, welcome back!",
  "status": "User @username has @message_count messages",
  "path": "/users/@user_id/profile"
}
```

### JSL Expression Evaluation

Use `["$eval", ...]` with standard JSL syntax inside:

```json
{
  "age_next_year": ["$eval", ["+", "@age", 1]],
  "is_adult": ["$eval", [">=", "@age", 18]],
  "greeting": ["$eval", ["str-join", "@", ["@Hello ", "username", "@!"]]],
  "filtered_items": ["$eval", ["filter", ["lambda", ["x"], [">", "x", "threshold"]], "items"]]
}
```

Note how inside `$eval`:
- `"@age"` is a JSL literal (the number stored in variable `age`)
- `"username"` is a JSL variable lookup
- `"threshold"` is a JSL variable lookup
- `"items"` is a JSL variable lookup

### Complex Expression Examples

```json
{
  "user_summary": ["$eval", ["if", [">=", "age", "@18"],
    ["str-join", "@", ["username", "@ (adult)"]],
    ["str-join", "@", ["username", "@ (minor)"]]
  ]],
  
  "permissions": ["$eval", ["if", ["=", "role", "@admin"],
    ["@", ["read", "write", "delete"]],
    ["@", ["read"]]
  ]],
  
  "statistics": {
    "total": ["$eval", ["length", "items"]],
    "average": ["$eval", ["/", ["sum", "values"], ["length", "values"]]],
    "above_threshold": ["$eval", ["filter", 
      ["lambda", ["x"], [">", "x", "threshold"]], 
      "values"
    ]]
  }
}
```

### Template Processing Rules

1. **Variable Substitution**: Replace `@variable` with environment values
2. **String Interpolation**: Process embedded `@variables` in strings  
3. **Expression Evaluation**: Execute `["$eval", ...]` as JSL code
4. **Type Preservation**: Maintain original types through resolution

### Processing Example

```json
// Template
{
  "name": "@username",
  "age_group": ["$eval", ["if", [">=", "age", "@21"], "@adult", "@young"]]
}

// Environment: username="alice", age=25
// Step 1 - Variable substitution: username → "alice"
// Step 2 - Expression evaluation: 
//   - "age" (JSL variable) → 25
//   - "@21" (JSL literal) → 21
//   - [">=", 25, 21] → true
//   - "@adult" (JSL literal) → "adult"
// Result:
{
  "name": "alice",
  "age_group": "adult"
}
```

## Advanced Template Patterns

### Nested Data Generation

```json
{
  "users": ["$eval", ["map", 
    ["lambda", ["user"], {
      "id": ["get", "user", "@id"],
      "name": ["get", "user", "@name"], 
      "email": ["str-join", "@", [
        ["get", "user", "@name"], 
        "@@", 
        "domain"
      ]]
    }],
    "user_list"
  ]]
}
```

### Conditional Structure Generation

```json
{
  "basic_info": {
    "name": "@full_name",
    "email": "@email"
  },
  "admin_info": ["$eval", ["if", ["=", "role", "@admin"],
    {
      "permissions": "admin_permissions",
      "last_login": "admin_last_login"
    },
    "@null"
  ]]
}
```

### Dynamic Key Generation

```json
["$eval", ["object", 
  ["str-join", "@", ["@user_", "user_id"]], "user_data",
  ["str-join", "@", ["@session_", "session_id"]], "session_data"
]]
```

## Integration Examples

### With JHIP

```json
{
  "request": ["$eval", ["host", "operation_type", "file_path", {
    "content": "file_content",
    "metadata": {
      "author": "current_user", 
      "timestamp": ["$eval", ["host", "@time/now"]]
    }
  }]]
}
```

### Database Query Templates

```json
{
  "query": "SELECT * FROM users WHERE status = '@status' AND age >= @min_age",
  "params": ["$eval", ["object",
    "@status", "filter_status",
    "@min_age", "age_threshold"
  ]]
}
```

### API Response Templates

```json
{
  "status": "@success",
  "data": {
    "user_id": "@current_user_id",
    "username": "@current_username",
    "computed_score": ["$eval", ["*", "base_score", "multiplier"]],
    "recommendations": ["$eval", ["take", "@5", ["sort-by", "score", "all_recommendations"]]]
  },
  "links": {
    "self": "/api/users/@current_user_id",
    "edit": ["$eval", ["if", ["=", "role", "@admin"], 
      ["str-join", "@", ["/api/users/", "current_user_id", "/edit"]], 
      "@null"
    ]]
  }
}
```

## Error Handling

### Undefined Variables

```json
// Template variable not found
{"user": "@missing_username"}
// Error: Template variable 'missing_username' not found

// JSL variable not found in $eval
{"computed": ["$eval", ["get", "missing_var"]]}
// Error: Variable 'missing_var' not found in JSL environment
```

### Type Consistency

The dual syntax system maintains clear separation:

```json
{
  "template_string": "Hello @name",        // Template interpolation
  "jsl_string": ["$eval", ["str-join", "@", ["@Hello ", "name"]]] // JSL string ops
}
```

## Best Practices

1. **Use interpolation for simple cases**: `"Hello @name"` vs `["$eval", ["str-join", "@", ["@Hello ", "name"]]]`
2. **Use $eval for computation**: Mathematical operations, conditional logic, data transformations
3. **Maintain context awareness**: Remember which syntax applies in which context
4. **Document variable expectations**: Clearly specify template variable requirements
5. **Validate environments**: Ensure all required variables exist before template processing

This design achieves perfect consistency: templates use their own conventions at the top level, but embedded JSL code uses standard JSL conventions. The `["$eval", ...]` syntax follows JSL's S-expression pattern while clearly marking the transition between template and JSL contexts.