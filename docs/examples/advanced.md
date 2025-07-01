# Advanced JSL Examples

## Distributed Computing

```json
{
  "forms": [
    ["def", "map-reduce-job",
     ["lambda", ["data", "map-fn", "reduce-fn"],
      ["do",
       ["def", "mapped", ["map", "map-fn", "data"]],
       ["reduce", "reduce-fn", "mapped"]]]],
    
    ["def", "word-count",
     ["lambda", ["text"],
      ["map-reduce-job",
       ["str-split", "text", "@\\s+"],
       ["lambda", ["word"], [["to-lower", "word"], 1]],
       ["lambda", ["acc", "item"], 
        ["set", "acc", ["first", "item"], 
         ["+", ["get", "acc", ["first", "item"], 0], ["second", "item"]]]]]]]
  ],
  "entrypoint": ["word-count", "@The quick brown fox jumps over the lazy dog"]
}
```

## Closure Serialization

```json
["do",
  ["def", "create-adder",
   ["lambda", ["n"],
    ["lambda", ["x"], ["+", "x", "n"]]]],
  
  ["def", "add-five", ["create-adder", 5]],
  
  ["def", "serialized-adder", ["to-json", "add-five"]],
  
  ["def", "restored-adder", ["from-json", "serialized-adder"]],
  
  ["restored-adder", 10]]
```

## Template-Driven Configuration

```json
{
  "database": {
    "host": "db_host",
    "port": "db_port",
    "name": "db_name",
    "ssl": "ssl_enabled"
  },
  "services": {
    "auth": {
      "url": "auth_service_url",
      "timeout": "auth_timeout"
    },
    "cache": {
      "url": "cache_service_url", 
      "ttl": "cache_ttl"
    }
  }
}
```