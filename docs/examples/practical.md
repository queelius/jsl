# Practical JSL Examples

## File Processing

```json
["do",
  ["def", "process-file", 
   ["lambda", ["path"],
    ["do",
     ["def", "content", ["host", "@file/read-string", "path"]],
     ["str-split", "content", "@\n"]]]],
  ["process-file", "@/tmp/data.txt"]]
```

## Data Transformation

```json
["do",
  ["def", "users", [
    {"name": "@Alice", "age": 30},
    {"name": "@Bob", "age": 25}, 
    {"name": "@Charlie", "age": 35}
  ]],
  ["def", "adult-names",
   ["map", 
    ["lambda", ["user"], ["get", "user", "@name"]],
    ["filter", 
     ["lambda", ["user"], [">", ["get", "user", "@age"], 21]], 
     "users"]]],
  "adult-names"]
```

## API Integration

```json
["do",
  ["def", "fetch-user-data",
   ["lambda", ["user-id"],
    ["host", "@http/get", 
     ["str-concat", "@https://api.example.com/users/", "user-id"]]]],
  ["def", "process-response",
   ["lambda", ["response"],
    ["get", ["get", "response", "@data"], "@name"]]],
  ["process-response", ["fetch-user-data", "@123"]]]
```