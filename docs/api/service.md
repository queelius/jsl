# Service API

## Overview

The JSL Service API provides a high-level interface for deploying JSL as a network service, handling HTTP requests, WebSocket connections, and distributed execution coordination.

## Core Classes

::: jsl.service
    options:
      show_root_heading: false
      show_source: true
      members:
        - JSLService
        - RequestHandler
        - WebSocketHandler

## HTTP Service

### Basic Service Setup

```python
from jsl.service import JSLService

# Create service instance
service = JSLService(host="0.0.0.0", port=8080)

# Start service
service.start()
```

### Custom Request Handling

```python
from jsl.service import JSLService, RequestHandler

class CustomHandler(RequestHandler):
    def handle_execute(self, request):
        # Custom execution logic
        code = request.get("code")
        context = request.get("context", {})
        
        # Add custom validation
        if not self.validate_code(code):
            return {"error": "Invalid code"}
        
        # Execute with custom environment
        result = self.runner.execute(code, context)
        return {"result": result}

# Use custom handler
service = JSLService(handler=CustomHandler())
```

### API Endpoints

The service automatically provides these endpoints:

#### POST /execute
```json
{
  "code": ["lambda", ["x"], ["*", "x", "x"]],
  "args": [5],
  "context": {}
}
```

Response:
```json
{
  "result": 25,
  "execution_time_ms": 12,
  "memory_used_bytes": 1024
}
```

#### POST /evaluate
```json
{
  "expression": ["+", 1, 2],
  "environment": {"x": 10}
}
```

#### GET /health
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "active_connections": 5
}
```

## WebSocket Interface

### Real-time Code Execution

```python
import asyncio
import websockets
import json

async def execute_stream():
    uri = "ws://localhost:8080/ws"
    async with websockets.connect(uri) as websocket:
        # Send code for execution
        request = {
            "type": "execute",
            "code": ["map", ["lambda", ["x"], ["*", "x", 2]], [1, 2, 3, 4]]
        }
        await websocket.send(json.dumps(request))
        
        # Receive result
        response = await websocket.recv()
        result = json.loads(response)
        print(result)  # {"result": [2, 4, 6, 8]}

asyncio.run(execute_stream())
```

### Code Streaming

```python
# Stream large code structures
async def stream_large_program():
    async with websockets.connect("ws://localhost:8080/ws") as ws:
        # Start streaming session
        await ws.send(json.dumps({"type": "stream_start", "id": "prog1"}))
        
        # Send code chunks
        for chunk in large_program_chunks:
            await ws.send(json.dumps({
                "type": "stream_chunk",
                "id": "prog1", 
                "data": chunk
            }))
        
        # Execute streamed program
        await ws.send(json.dumps({"type": "stream_execute", "id": "prog1"}))
        
        # Get result
        result = await ws.recv()
```

## Distributed Coordination

### Cluster Configuration

```python
from jsl.service import JSLService, ClusterConfig

cluster_config = ClusterConfig(
    nodes=["http://node1:8080", "http://node2:8080", "http://node3:8080"],
    replication_factor=2,
    load_balancing="round_robin"
)

service = JSLService(cluster=cluster_config)
```

### Remote Execution

```python
# Execute code on specific nodes
response = service.execute_on_node(
    node="http://node2:8080",
    code=["expensive_computation", "large_dataset"]
)

# Distribute computation across cluster
response = service.distribute_execution(
    code=["map", "process_item", "huge_list"],
    partition_strategy="size_based"
)
```

## Security and Authentication

### API Key Authentication

```python
from jsl.service import JSLService, APIKeyAuth

auth = APIKeyAuth(keys=["secret-key-1", "secret-key-2"])
service = JSLService(auth=auth)
```

### Request Validation

```python
from jsl.service import JSLService, RequestValidator

class SecurityValidator(RequestValidator):
    def validate_code(self, code):
        # Check for dangerous operations
        dangerous_ops = ["host", "file/write", "system/exec"]
        return not any(op in str(code) for op in dangerous_ops)
    
    def validate_request(self, request):
        # Rate limiting, size limits, etc.
        return len(str(request)) < 1024 * 1024  # 1MB limit

service = JSLService(validator=SecurityValidator())
```

## Monitoring and Logging

### Metrics Collection

```python
from jsl.service import JSLService
import prometheus_client

# Enable Prometheus metrics
service = JSLService(metrics_enabled=True)

# Custom metrics
request_counter = prometheus_client.Counter(
    'jsl_requests_total', 
    'Total JSL requests'
)

execution_time = prometheus_client.Histogram(
    'jsl_execution_duration_seconds',
    'JSL execution time'
)
```

### Structured Logging

```python
import logging
from jsl.service import JSLService

# Configure structured logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

service = JSLService(
    log_level="INFO",
    log_format="json",
    log_requests=True
)
```

## Deployment Examples

### Docker Deployment

```dockerfile
FROM python:3.11-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8080
CMD ["python", "-m", "jsl.service", "--host=0.0.0.0", "--port=8080"]
```

### Kubernetes Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jsl-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jsl-service
  template:
    metadata:
      labels:
        app: jsl-service
    spec:
      containers:
      - name: jsl-service
        image: jsl:latest
        ports:
        - containerPort: 8080
        env:
        - name: JSL_CLUSTER_NODES
          value: "http://jsl-1:8080,http://jsl-2:8080,http://jsl-3:8080"
```

The Service API makes it easy to deploy JSL as a scalable, production-ready service with support for clustering, security, and monitoring.