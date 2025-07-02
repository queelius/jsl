# Advanced JSL Examples

## Distributed Computing

This example demonstrates a map-reduce implementation for word counting.

```json
["let", [
  ["map-reduce",
    ["lambda", ["data", "map-fn", "reduce-fn"],
      ["let", [["mapped", ["map", "map-fn", "data"]]],
        ["reduce", "reduce-fn", {}, "mapped"]]]],
  
  ["word-count",
    ["lambda", ["text"],
      ["let", [
        ["words", ["str-split", ["str-lower", "text"], "@ "]],
        ["count-word", 
          ["lambda", ["acc", "word"],
            ["set", "acc", "word", 
              ["+", ["get", "acc", "word", 0], 1]]]]
      ],
        ["reduce", "count-word", {}, "words"]]]]
],
  ["word-count", "@The quick brown fox jumps over the lazy dog"]
]
```

## Closure Serialization

This example shows how a closure can be serialized to JSON, then deserialized and executed.

```json
["let", [
  ["create-adder",
    ["lambda", ["n"],
      ["lambda", ["x"], ["+", "x", "n"]]]],
  
  ["add-five", ["create-adder", 5]],
  ["serialized", ["serialize", "add-five"]],
  ["restored", ["deserialize", "serialized"]]
],
  ["restored", 10]
]
```

Result: `15` - The closure maintains its captured environment even after serialization.

## Dynamic Configuration Objects

Build configuration objects that adapt based on environment settings.

```json
["let", [
  ["env", "@production"],
  ["is-prod", ["=", "env", "@production"]],
  ["db-host", ["if", "is-prod", "@db.prod.example.com", "@localhost"]]
],
  {
    "@database": {
      "@host": "db-host",
      "@port": ["if", "is-prod", 5432, 5433],
      "@name": ["str-concat", "@myapp_", "env"],
      "@ssl": "is-prod",
      "@pool_size": ["if", "is-prod", 20, 5]
    },
    "@services": {
      "@auth": {
        "@url": ["str-concat", "@https://auth.", "env", "@.example.com"],
        "@timeout": ["if", "is-prod", 5000, 30000]
      },
      "@cache": {
        "@enabled": "is-prod",
        "@ttl": ["if", "is-prod", 3600, 300]
      }
    }
  }
]
```

## Memoization Pattern

Create a memoized version of expensive computations.

```json
["let", [
  ["memoize",
    ["lambda", ["fn"],
      ["let", [["cache", {}]],
        ["lambda", ["arg"],
          ["let", [["key", ["str", "arg"]]],
            ["if", ["has", "cache", "key"],
              ["get", "cache", "key"],
              ["let", [["result", ["fn", "arg"]]],
                ["do",
                  ["set", "cache", "key", "result"],
                  "result"]]]]]]]],
  
  ["fibonacci",
    ["lambda", ["n"],
      ["if", ["<=", "n", 1],
        "n",
        ["+", 
          ["fibonacci", ["-", "n", 1]], 
          ["fibonacci", ["-", "n", 2]]]]]],
  
  ["fast-fib", ["memoize", "fibonacci"]]
],
  ["map", "fast-fib", ["@", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]]
]
```

## Pipeline Processing

Build a data processing pipeline with error handling.

```json
["let", [
  ["pipeline",
    ["lambda", ["data", "transformations"],
      ["reduce",
        ["lambda", ["acc", "transform"],
          ["try",
            ["transform", "acc"],
            ["lambda", ["err"],
              {"@error": true, 
               "@message": ["get", "err", "@message"],
               "@data": "acc"}]]],
        "data",
        "transformations"]]],
  
  ["validate-user",
    ["lambda", ["user"],
      ["if", ["and",
              ["has", "user", "@email"],
              ["str-contains", ["get", "user", "@email"], "@@"]],
        "user",
        ["error", "@Invalid email"]]]],
  
  ["enrich-user",
    ["lambda", ["user"],
      ["set", "user", "@id", 
        ["str-concat", "@user_", ["str", ["random-int", 1000, 9999]]]]]],
  
  ["user-data", {"@name": "@Alice", "@email": "@alice@example.com"}]
],
  ["pipeline", "user-data", ["@", ["validate-user", "enrich-user"]]]
]
```

## Key Advanced Patterns

1. **Map-Reduce** - Process large datasets in a functional way
2. **Closure Serialization** - Send functions with their context over the network
3. **Dynamic Objects** - Build configuration that adapts to runtime conditions
4. **Memoization** - Cache expensive computations transparently
5. **Pipeline Processing** - Chain transformations with error handling
