# Basic Examples

This page provides practical examples of JSL programming patterns and idioms. Each example is fully runnable and demonstrates key language concepts.

## Mathematical Computing

### Prime Number Generator

```json
[
  "do",
  ["def", "is-prime?", 
   ["lambda", ["n"],
    ["if", ["<", "n", 2], 
     false,
     ["if", ["=", "n", 2],
      true,
      ["if", ["=", ["mod", "n", 2], 0],
       false,
       ["do",
        ["def", "check-divisor",
         ["lambda", ["d"],
          ["if", [">", ["*", "d", "d"], "n"],
           true,
           ["if", ["=", ["mod", "n", "d"], 0],
            false,
            ["check-divisor", ["+", "d", 2]]]]]],
        ["check-divisor", 3]]]]]]],
        
  ["def", "primes-up-to",
   ["lambda", ["limit"],
    ["filter", "is-prime?", 
     ["map", ["lambda", ["i"], ["+", "i", 2]], 
      ["list", 0, 1, 2, 3, 4, 5, 6, 7, 8]]]]],
      
  ["primes-up-to", 10]
]
```

Result: `[2, 3, 5, 7]`

### Fibonacci Sequence

```json
[
  "do",
  ["def", "fibonacci",
   ["lambda", ["n"],
    ["if", ["<=", "n", 1],
     "n",
     ["+", ["fibonacci", ["-", "n", 1]], 
          ["fibonacci", ["-", "n", 2]]]]]],
          
  ["map", "fibonacci", ["list", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
]
```

Result: `[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]`

## Data Processing

### CSV-Like Data Analysis

```json
[
  "do",
  ["def", "sales-data", [
    {"product": "Laptop", "price": 999, "quantity": 5, "region": "North"},
    {"product": "Mouse", "price": 25, "quantity": 50, "region": "South"},
    {"product": "Keyboard", "price": 75, "quantity": 30, "region": "North"},
    {"product": "Monitor", "price": 299, "quantity": 15, "region": "East"},
    {"product": "Laptop", "price": 999, "quantity": 8, "region": "South"}
  ]],
  
  ["def", "total-revenue",
   ["lambda", ["record"],
    ["*", ["get", "record", "price"], ["get", "record", "quantity"]]]],
    
  ["def", "high-value-sales",
   ["filter", 
    ["lambda", ["record"], [">", ["total-revenue", "record"], 1000]],
    "sales-data"]],
    
  ["def", "revenue-by-region",
   ["lambda", ["region"],
    ["reduce", "+",
     ["map", "total-revenue",
      ["filter", 
       ["lambda", ["record"], ["=", ["get", "record", "region"], "region"]],
       "sales-data"]], 0]]],
       
  {
    "high_value_sales": ["map", ["lambda", ["r"], ["get", "r", "product"]], "high-value-sales"],
    "north_revenue": ["revenue-by-region", "North"],
    "south_revenue": ["revenue-by-region", "South"],
    "total_items": ["reduce", "+", ["map", ["lambda", ["r"], ["get", "r", "quantity"]], "sales-data"], 0]
  }
]
```

### Text Processing

```json
[
  "do",
  ["def", "text", "The quick brown fox jumps over the lazy dog"],
  
  ["def", "words", ["str-split", ["str-lower", "text"], " "]],
  
  ["def", "word-count",
   ["lambda", ["word-list"],
    ["reduce",
     ["lambda", ["acc", "word"],
      ["if", ["has-key?", "acc", "word"],
       ["set", "acc", "word", ["+", ["get", "acc", "word"], 1]],
       ["set", "acc", "word", 1]]],
     "word-list", {}]]],
     
  ["def", "word-length-stats",
   ["lambda", ["word-list"],
    ["do",
     ["def", "lengths", ["map", "str-length", "word-list"]],
     {
       "min": ["apply", "min", "lengths"],
       "max": ["apply", "max", "lengths"],
       "average": ["/", ["reduce", "+", "lengths", 0], ["length", "lengths"]]
     }]]],
     
  {
    "original_text": "text",
    "word_count": ["word-count", "words"],
    "length_stats": ["word-length-stats", "words"],
    "unique_words": ["length", ["keys", ["word-count", "words"]]]
  }
]
```

## Web API Simulation

### User Management System

```json
[
  "do",
  ["def", "users", [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"}
  ]],
  
  ["def", "find-user-by-id",
   ["lambda", ["user-id"],
    ["first",
     ["filter", 
      ["lambda", ["user"], ["=", ["get", "user", "id"], "user-id"]],
      "users"]]]],
      
  ["def", "update-user",
   ["lambda", ["user-id", "updates"],
    ["map",
     ["lambda", ["user"],
      ["if", ["=", ["get", "user", "id"], "user-id"],
       ["merge", "user", "updates"],
       "user"]],
     "users"]]],
     
  ["def", "create-user-profile",
   ["lambda", ["user"],
    ["template", {
      "profile": {
        "id": {"$": ["get", "user", "id"]},
        "display_name": {"$": ["get", "user", "name"]},
        "contact": {"$": ["get", "user", "email"]},
        "permissions": {"$": ["if", ["=", ["get", "user", "role"], "admin"], ["list", "read", "write", "admin"], ["list", "read"]]},
        "created_at": {"$": ["str-concat", "2024-01-01T", ["get", "user", "id"], ":00:00Z"]}
      }
    }]]],
    
  ["def", "api-response",
   ["lambda", ["data", "status"],
    {
      "status": "status",
      "data": "data",
      "timestamp": "2024-01-01T12:00:00Z"
    }]],
    
  {
    "get_user": ["api-response", ["create-user-profile", ["find-user-by-id", 1]], "success"],
    "update_result": ["api-response", ["update-user", 2, {"role": "moderator"}], "success"],
    "all_profiles": ["map", "create-user-profile", "users"]
  }
]
```

## Algorithm Implementations

### Quick Sort

```json
[
  "do",
  ["def", "quicksort",
   ["lambda", ["lst"],
    ["if", ["<=", ["length", "lst"], 1],
     "lst",
     ["do",
      ["def", "pivot", ["first", "lst"]],
      ["def", "rest-list", ["rest", "lst"]],
      ["def", "less", ["filter", ["lambda", ["x"], ["<", "x", "pivot"]], "rest-list"]],
      ["def", "greater", ["filter", ["lambda", ["x"], [">=", "x", "pivot"]], "rest-list"]],
      ["concat", ["quicksort", "less"], ["list", "pivot"], ["quicksort", "greater"]]]]]],
      
  ["def", "unsorted", [64, 34, 25, 12, 22, 11, 90, 88, 76, 50, 42]],
  
  {
    "original": "unsorted",
    "sorted": ["quicksort", "unsorted"],
    "verification": ["=", ["quicksort", "unsorted"], [11, 12, 22, 25, 34, 42, 50, 64, 76, 88, 90]]
  }
]
```

### Binary Search

```json
[
  "do",
  ["def", "binary-search",
   ["lambda", ["sorted-list", "target"],
    ["do",
     ["def", "search-range",
      ["lambda", ["low", "high"],
       ["if", [">", "low", "high"],
        -1,
        ["do",
         ["def", "mid", ["/", ["+", "low", "high"], 2]],
         ["def", "mid-val", ["nth", "sorted-list", "mid"]],
         ["if", ["=", "mid-val", "target"],
          "mid",
          ["if", ["<", "mid-val", "target"],
           ["search-range", ["+", "mid", 1], "high"],
           ["search-range", "low", ["-", "mid", 1]]]]]]]],
     ["search-range", 0, ["-", ["length", "sorted-list"], 1]]]]],
     
  ["def", "sorted-numbers", [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]],
  
  {
    "list": "sorted-numbers",
    "find_7": ["binary-search", "sorted-numbers", 7],
    "find_15": ["binary-search", "sorted-numbers", 15],
    "find_missing": ["binary-search", "sorted-numbers", 8]
  }
]
```

## Configuration and Templates

### Dynamic Configuration

```json
[
  "do",
  ["def", "environment", "production"],
  ["def", "app-name", "my-web-app"],
  ["def", "version", "1.2.3"],
  
  ["def", "config-template",
   ["template", {
     "application": {
       "name": {"$": "app-name"},
       "version": {"$": "version"},
       "environment": {"$": "environment"}
     },
     "database": {
       "host": {"$": ["if", ["=", "environment", "production"], "prod-db.example.com", "localhost"]},
       "port": {"$": ["if", ["=", "environment", "production"], 5432, 5433]},
       "ssl": {"$": ["=", "environment", "production"]},
       "pool_size": {"$": ["if", ["=", "environment", "production"], 20, 5]}
     },
     "cache": {
       "enabled": {"$": ["=", "environment", "production"]},
       "ttl": {"$": ["if", ["=", "environment", "production"], 3600, 300]}
     },
     "logging": {
       "level": {"$": ["if", ["=", "environment", "production"], "INFO", "DEBUG"]},
       "file": {"$": ["str-concat", "/var/log/", "app-name", ".log"]}
     }
   }]],
   
  "config-template"
]
```

## Functional Programming Patterns

### Function Composition

```json
[
  "do",
  ["def", "compose",
   ["lambda", ["f", "g"],
    ["lambda", ["x"], ["f", ["g", "x"]]]]],
    
  ["def", "pipe",
   ["lambda", ["value", "functions"],
    ["reduce", 
     ["lambda", ["acc", "fn"], ["fn", "acc"]],
     "functions", "value"]]],
     
  ["def", "add-ten", ["lambda", ["x"], ["+", "x", 10]]],
  ["def", "multiply-by-two", ["lambda", ["x"], ["*", "x", 2]]],
  ["def", "square", ["lambda", ["x"], ["*", "x", "x"]]],
  
  ["def", "complex-transform", ["compose", "square", ["compose", "multiply-by-two", "add-ten"]]],
  
  ["def", "pipeline-transform",
   ["lambda", ["x"],
    ["pipe", "x", ["list", "add-ten", "multiply-by-two", "square"]]]],
    
  ["def", "numbers", [1, 2, 3, 4, 5]],
  
  {
    "original": "numbers",
    "composed": ["map", "complex-transform", "numbers"],
    "piped": ["map", "pipeline-transform", "numbers"],
    "single_example": {
      "input": 5,
      "composed_result": ["complex-transform", 5],
      "piped_result": ["pipeline-transform", 5]
    }
  }
]
```

These examples demonstrate JSL's power for:

- **Mathematical computing** with recursive algorithms
- **Data processing** using functional programming patterns  
- **API development** with dynamic templates
- **Algorithm implementation** showing classic computer science problems
- **Configuration management** with environment-specific settings
- **Functional composition** for building complex transformations

Each example is self-contained and can be run directly with the JSL interpreter. Try modifying them to explore different variations and learn JSL's capabilities!
