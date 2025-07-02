# Distributed Computing with JSL

## Overview

JSL's core design—being homoiconic and having a robust, verifiable serialization model—makes it an ideal language for building distributed systems. Because both code and state can be safely transmitted over the network, complex distributed patterns can be expressed with the same clarity as local computations.

> **An Architectural Showcase:**
> The following examples are an architectural showcase of what is possible. They are not a standard library reference. These patterns assume the host environment provides a rich set of networking primitives (e.g., `remote/execute`, `remote/call`). The purpose is to demonstrate how JSL can be used as the foundation for a powerful distributed computing framework.

## Core Patterns

### 1. Remote Execution

The most fundamental pattern is executing a function on a remote node. JSL's serializable closures make this trivial. The closure packages its code and its environment, which can be sent to a remote host for evaluation.

The host provides `remote/execute` which takes a node, a function, and arguments.
```json
["host", "remote/execute", "node-2", 
  ["lambda", ["x"], ["*", "x", "x"]],
  5]
```

### 2. Master-Worker Pattern

A coordinator node can partition a workload and distribute it among a set of worker nodes. This pattern highlights how JSL's functional nature (`map`, `zip`) simplifies parallel processing logic. The worker function itself is passed as an argument, making this a flexible, higher-order function.

```json
["def", "distribute_work",
  ["lambda", ["work_items", "workers", "work_fn"],
    ["do",
      ["def", "chunks", ["partition", "work_items", ["length", "workers"]]],
      ["def", "tasks", ["zip", "workers", "chunks"]],
      ["map", 
        ["lambda", ["task"],
          ["host", "remote/execute", 
            ["first", "task"],
            "work_fn",
            ["second", "task"]]],
        "tasks"]]]]
```

### 3. Fault Tolerance via Retries

Handling network failures is critical. Because JSL code is data, we can easily write higher-order functions that wrap any remote call with a retry mechanism.

This example defines a recursive inner function, `try_call`, to handle the retry loop. The `try` special form is used to catch failures, and the error handler recursively calls itself with one fewer attempt.
```json
["def", "reliable_remote_call",
  ["lambda", ["node", "function", "args", "max_retries"],
    ["do",
      ["def", "try_call",
        ["lambda", ["attempts_left"],
          ["if", ["=", "attempts_left", 0],
            ["error", "Max retries exceeded"],
            ["try",
              ["host", "remote/call", "node", "function", "args"],
              ["lambda", ["error"],
                ["do",
                  ["host", "log/warn", ["@", "Retry attempt ", ["-", ["+", "max_retries", 1], "attempts_left"], " failed. Retrying..."]],
                  ["try_call", ["-", "attempts_left", 1]]
                ]
              ]
            ]
          ]
        ]
      ],
      ["try_call", "max_retries"]
    ]
  ]
]
```

## Advanced Patterns

JSL's composability allows these simple building blocks to be combined into sophisticated distributed algorithms.

### MapReduce Implementation

This example shows how a full MapReduce job can be expressed by composing the `distribute_work` function defined earlier.

The process is broken down into three phases:
1.  **MAP PHASE:** Distribute the map function across the map nodes.
2.  **SHUFFLE PHASE:** Group the intermediate results by key.
3.  **REDUCE PHASE:** Distribute the reduce function across the reduce nodes to produce the final result.
```json
["def", "mapreduce",
  ["lambda", ["map_fn", "reduce_fn", "data", "map_nodes", "reduce_nodes"],
    ["do",
      ["def", "map_results", ["distribute_work", "data", "map_nodes", "map_fn"]],
      ["def", "grouped", ["group_by", "first", ["flatten", "map_results"]]],
      ["def", "reduce_tasks", ["items", "grouped"]],
      ["distribute_work", "reduce_tasks", "reduce_nodes", "reduce_fn"]
    ]
  ]
]
```

These examples illustrate that JSL provides the ideal substrate for building resilient, scalable systems while maintaining the simplicity and clarity of the language's core design principles.