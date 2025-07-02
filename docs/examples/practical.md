# Practical JSL Examples

These examples demonstrate core JSL patterns for real-world programming tasks.

## Data Processing

### Filtering and Transforming Lists

Extract email addresses from active users:

```json
["let", [
  ["users", ["@", [
    {"@name": "@Alice", "@email": "@alice@example.com", "@active": true},
    {"@name": "@Bob", "@email": "@bob@example.com", "@active": false},
    {"@name": "@Charlie", "@email": "@charlie@example.com", "@active": true}
  ]]],
  ["active-emails", 
    ["map",
      ["lambda", ["user"], ["get", "user", "@email"]],
      ["filter",
        ["lambda", ["user"], ["get", "user", "@active"]],
        "users"]]]
],
  "active-emails"
]
```

Result: `["alice@example.com", "charlie@example.com"]`

## File Operations

### Reading and Processing a File

Read a configuration file and parse it:

```json
["let", [
  ["config-path", "@/app/config.json"],
  ["config", ["try",
    ["json-parse", ["host", "file/read", "config-path"]],
    ["lambda", ["err"], 
      {"@debug": false, "@timeout": 30}]]]
],
  ["get", "config", "@debug", false]
]
```

This safely reads a JSON config file with a fallback default if the file doesn't exist.

## Dynamic Configuration

### Environment-Based Settings

Build configuration that adapts to the current environment:

```json
["let", [
  ["env", "@production"],
  ["is-prod", ["=", "env", "@production"]]
],
  {
    "@app": "@my-service",
    "@database": {
      "@host": ["if", "is-prod", "@db.prod.example.com", "@localhost"],
      "@port": 5432,
      "@pool_size": ["if", "is-prod", 20, 5]
    },
    "@logging": {
      "@level": ["if", "is-prod", "@warn", "@debug"],
      "@format": "@json"
    }
  }
]
```

## API Request with Error Handling

### Safe HTTP Request

Fetch user data with proper error handling:

```json
["let", [
  ["fetch-user",
    ["lambda", ["id"],
      ["try",
        ["host", "http/get", ["str-concat", "@/api/users/", "id"]],
        ["lambda", ["err"],
          {"@error": true, "@message": ["get", "err", "@message"]}]]]]
],
  ["fetch-user", "@12345"]
]
```

## Key Patterns Demonstrated

1. **`let` for functional bindings** - Clean variable scoping without mutation
2. **First-class objects** - JSON objects as native data structures  
3. **Error handling with `try`** - Graceful failure recovery
4. **Higher-order functions** - `map` and `filter` for data transformation
5. **Dynamic values** - Computing object properties with expressions
