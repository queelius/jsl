# Distributed Computing with JSL

## Overview

JSL's network transparency enables seamless distributed computing. Code can move freely between nodes, execute remotely, and coordinate across network boundaries while maintaining the same semantics as local execution.

## Distributed Execution Patterns

### Remote Function Execution

```json
// Execute function on remote node
["host", "remote/execute", "node_2", 
  ["lambda", ["data"], ["map", "expensive_operation", "data"]],
  "large_dataset"]
```

### Code Migration

```json
// Move computation to data location
["do",
  ["def", "processor", ["lambda", ["items"], 
    ["filter", ["lambda", ["x"], [">", ["get", "x", "score"], 0.8]], "items"]]],
  ["host", "remote/migrate", "data_node", "processor", "dataset_id"]
]
```

### Distributed Pipeline

```json
// Multi-stage distributed processing
["do",
  ["def", "stage1", ["remote/execute", "node1", "extract_features", "raw_data"]],
  ["def", "stage2", ["remote/execute", "node2", "transform_features", "stage1"]],
  ["def", "stage3", ["remote/execute", "node3", "classify", "stage2"]],
  "stage3"]
```

## Network Topologies

### Master-Worker Pattern

```json
// Coordinator distributes work
["def", "distribute_work",
  ["lambda", ["work_items", "workers"],
    ["do",
      ["def", "chunks", ["partition", "work_items", ["length", "workers"]]],
      ["def", "tasks", ["zip", "workers", "chunks"]],
      ["map", 
        ["lambda", ["task"],
          ["remote/execute", ["first", "task"], "process_chunk", ["second", "task"]]],
        "tasks"]]]]
```

### Peer-to-Peer Processing

```json
// Nodes coordinate directly
["def", "p2p_reduce",
  ["lambda", ["operation", "initial", "nodes"],
    ["fold", 
      ["lambda", ["acc", "node"],
        ["remote/call", "node", "partial_reduce", "operation", "acc"]],
      "initial",
      "nodes"]]]
```

### Ring Topology

```json
// Pass computation around ring
["def", "ring_process",
  ["lambda", ["data", "processors", "nodes"],
    ["fold",
      ["lambda", ["result", "step"],
        ["remote/execute", 
          ["get", "nodes", ["mod", "step", ["length", "nodes"]]],
          ["get", "processors", "step"],
          "result"]],
      "data",
      ["range", ["length", "processors"]]]]]
```

## Distributed Data Structures

### Distributed Hash Table

```json
["def", "dht_get",
  ["lambda", ["key", "nodes"],
    ["do",
      ["def", "target_node", ["hash_to_node", "key", "nodes"]],
      ["remote/call", "target_node", "local_get", "key"]]]]

["def", "dht_put", 
  ["lambda", ["key", "value", "nodes"],
    ["do",
      ["def", "target_node", ["hash_to_node", "key", "nodes"]],
      ["remote/call", "target_node", "local_put", "key", "value"]]]]
```

### Replicated State

```json
["def", "replicated_update",
  ["lambda", ["state_key", "update_fn", "replica_nodes"],
    ["do",
      ["def", "new_state", ["update_fn", ["local_get", "state_key"]]],
      ["map",
        ["lambda", ["node"],
          ["remote/call", "node", "local_put", "state_key", "new_state"]],
        "replica_nodes"],
      "new_state"]]]
```

### Distributed List

```json
["def", "distributed_map",
  ["lambda", ["fn", "distributed_list", "worker_nodes"],
    ["do",
      ["def", "chunks", ["partition", "distributed_list", ["length", "worker_nodes"]]],
      ["def", "results", ["map",
        ["lambda", ["chunk_node_pair"],
          ["remote/execute", 
            ["second", "chunk_node_pair"], 
            ["partial", "map", "fn"], 
            ["first", "chunk_node_pair"]]],
        ["zip", "chunks", "worker_nodes"]]],
      ["flatten", "results"]]]]
```

## Fault Tolerance

### Retry Mechanisms

```json
["def", "reliable_remote_call",
  ["lambda", ["node", "function", "args", "max_retries"],
    ["do",
      ["def", "try_call",
        ["lambda", ["attempts_left"],
          ["if", ["=", "attempts_left", 0],
            ["error", "Max retries exceeded"],
            ["try",
              ["remote/call", "node", "function", "args"],
              ["lambda", ["error"],
                ["do",
                  ["host", "log", ["str", "Retry ", ["- ", "max_retries", "attempts_left"]]],
                  ["try_call", ["-", "attempts_left", 1]])]]]]],
      ["try_call", "max_retries"]]]]
```

### Redundant Execution

```json
["def", "redundant_execute",
  ["lambda", ["function", "args", "nodes"],
    ["do",
      ["def", "results", ["map",
        ["lambda", ["node"],
          ["async", ["remote/call", "node", "function", "args"]]],
        "nodes"]],
      ["first", ["await_any", "results"]]]]] // Return first successful result
```

### Checkpointing

```json
["def", "checkpointed_computation",
  ["lambda", ["steps", "checkpoint_interval"],
    ["fold",
      ["lambda", ["state", "step_index"],
        ["do",
          ["def", "new_state", ["execute_step", ["get", "steps", "step_index"], "state"]],
          ["if", ["=", ["mod", "step_index", "checkpoint_interval"], 0],
            ["host", "checkpoint/save", "step_index", "new_state"],
            "@null"],
          "new_state"]],
      ["host", "checkpoint/load"],
      ["range", ["length", "steps"]]]]]
```

## Load Balancing

### Dynamic Load Distribution

```json
["def", "load_balanced_execute",
  ["lambda", ["tasks", "nodes"],
    ["do",
      ["def", "node_loads", ["map", ["lambda", ["node"], ["remote/call", "node", "get_load"]], "nodes"]],
      ["def", "sorted_nodes", ["sort_by", "second", ["zip", "nodes", "node_loads"]]],
      ["map",
        ["lambda", ["task_index"],
          ["do",
            ["def", "target_node", ["get", "sorted_nodes", ["mod", "task_index", ["length", "nodes"]]]],
            ["remote/execute", ["first", "target_node"], ["get", "tasks", "task_index"]]]],
        ["range", ["length", "tasks"]]]]]]
```

### Adaptive Partitioning

```json
["def", "adaptive_partition",
  ["lambda", ["data", "nodes", "performance_history"],
    ["do",
      ["def", "node_speeds", ["map", 
        ["lambda", ["node"], ["get", "performance_history", "node", "avg_speed"]],
        "nodes"]],
      ["def", "total_speed", ["sum", "node_speeds"]],
      ["def", "proportions", ["map", 
        ["lambda", ["speed"], ["/", "speed", "total_speed"]],
        "node_speeds"]],
      ["def", "chunk_sizes", ["map",
        ["lambda", ["prop"], ["floor", ["*", "prop", ["length", "data"]]]],
        "proportions"]],
      ["partition_with_sizes", "data", "chunk_sizes"]]]]
```

## Consistency Models

### Eventually Consistent

```json
["def", "eventual_consistency_update",
  ["lambda", ["key", "value", "replicas"],
    ["do",
      ["async_map",
        ["lambda", ["replica"],
          ["remote/call", "replica", "async_update", "key", "value"]],
        "replicas"],
      "value"]]] // Return immediately, updates propagate asynchronously
```

### Strong Consistency (Consensus)

```json
["def", "consensus_update",
  ["lambda", ["key", "value", "replicas"],
    ["do",
      ["def", "proposal_id", ["generate_unique_id"]],
      ["def", "promises", ["map",
        ["lambda", ["replica"],
          ["remote/call", "replica", "prepare", "proposal_id"]],
        "replicas"]],
      ["if", [">", ["length", ["filter", "identity", "promises"]], ["/", ["length", "replicas"], 2]],
        ["do",
          ["map",
            ["lambda", ["replica"],
              ["remote/call", "replica", "accept", "proposal_id", "key", "value"]],
            "replicas"],
          "value"],
        ["error", "Consensus failed"]]]]]
```

## Distributed Algorithms

### MapReduce Implementation

```json
["def", "mapreduce",
  ["lambda", ["map_fn", "reduce_fn", "data", "map_nodes", "reduce_nodes"],
    ["do",
      // Map phase
      ["def", "map_results", ["distributed_map", "map_fn", "data", "map_nodes"]],
      
      // Shuffle phase  
      ["def", "grouped", ["group_by", "first", "map_results"]],
      
      // Reduce phase
      ["def", "reduce_tasks", ["map", 
        ["lambda", ["group"],
          ["list", ["first", "group"], ["map", "second", ["second", "group"]]]],
        "grouped"]],
      
      ["distributed_map",
        ["lambda", ["task"],
          ["list", ["first", "task"], ["reduce_fn", ["second", "task"]]]],
        "reduce_tasks",
        "reduce_nodes"]]]]
```

### Distributed Sorting

```json
["def", "distributed_sort",
  ["lambda", ["data", "nodes"],
    ["do",
      // Sample and determine pivots
      ["def", "samples", ["sample", "data", ["*", ["length", "nodes"], 100]]],
      ["def", "pivots", ["select_pivots", ["sort", "samples"], ["length", "nodes"]]],
      
      // Partition data by pivots
      ["def", "partitions", ["partition_by_pivots", "data", "pivots"]],
      
      // Sort each partition on different nodes
      ["def", "sorted_partitions", ["map",
        ["lambda", ["partition_node_pair"],
          ["remote/execute", 
            ["second", "partition_node_pair"], 
            "sort", 
            ["first", "partition_node_pair"]]],
        ["zip", "partitions", "nodes"]]],
      
      // Concatenate results
      ["flatten", "sorted_partitions"]]]]
```

## Network Communication

### Message Passing

```json
["def", "reliable_broadcast",
  ["lambda", ["message", "nodes"],
    ["map",
      ["lambda", ["node"],
        ["reliable_remote_call", "node", "receive_message", ["list", "message"], 3]],
      "nodes"]]]
```

### Gossip Protocol

```json
["def", "gossip_propagate",
  ["lambda", ["data", "nodes", "gossip_factor"],
    ["do",
      ["def", "targets", ["random_sample", "nodes", "gossip_factor"]],
      ["map",
        ["lambda", ["target"],
          ["remote/call", "target", "gossip_receive", "data"]],
        "targets"]]]]
```

## Monitoring and Debugging

### Distributed Tracing

```json
["def", "traced_remote_call",
  ["lambda", ["node", "function", "args", "trace_id"],
    ["do",
      ["host", "trace/start", "trace_id", "remote_call", "node"],
      ["def", "result", ["remote/call", "node", "function", "args"]],
      ["host", "trace/end", "trace_id", "result"],
      "result"]]]
```

### Health Monitoring

```json
["def", "monitor_cluster",
  ["lambda", ["nodes"],
    ["map",
      ["lambda", ["node"],
        ["try",
          ["do",
            ["def", "health", ["remote/call", "node", "health_check"]],
            ["list", "node", "healthy", "health"]],
          ["lambda", ["error"],
            ["list", "node", "unhealthy", ["str", "error"]]]]],
      "nodes"]]]
```

JSL's distributed computing capabilities enable building resilient, scalable systems while maintaining the simplicity and clarity of the language's core design principles.