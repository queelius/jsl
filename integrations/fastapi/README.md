# JSL FastAPI Integration

A REST API service for executing JSL programs with support for resource management, pauseable/resumable execution, and session management.

## Features

### Core Endpoints

#### Program Management
- `POST /programs` - Upload a JSL program
- `GET /programs/{id}` - Get program details
- `DELETE /programs/{id}` - Delete a program
- `GET /programs` - List all programs

#### Execution Control
- `POST /execute` - Execute a program (one-shot)
- `POST /sessions` - Create an execution session
- `POST /sessions/{id}/step` - Step through execution
- `POST /sessions/{id}/pause` - Pause execution
- `POST /sessions/{id}/resume` - Resume execution
- `GET /sessions/{id}/state` - Get current execution state
- `DELETE /sessions/{id}` - Terminate session

#### Resource Management
- `POST /budgets` - Create resource budget
- `GET /budgets/{id}` - Get budget status
- `PUT /budgets/{id}` - Update budget limits
- `GET /budgets/{id}/usage` - Get resource usage

### Example API Usage

```python
# Upload a program
POST /programs
{
    "name": "fibonacci",
    "code": ["def", "fib", ["lambda", ["n"], 
             ["if", ["<=", "n", 1], "n",
              ["+", ["fib", ["-", "n", 1]], 
                    ["fib", ["-", "n", 2]]]]]]
}

# Create a session with resource budget
POST /sessions
{
    "program_id": "fibonacci-123",
    "budget": {
        "max_gas": 10000,
        "max_time_ms": 5000,
        "max_memory_mb": 100,
        "max_stack_depth": 1000
    },
    "args": {"n": 10}
}

# Execute with stepping
POST /sessions/{session_id}/step
{
    "steps": 100  # Execute up to 100 steps
}

# Get current state (includes serialized continuation)
GET /sessions/{session_id}/state
{
    "status": "paused",
    "gas_used": 4523,
    "continuation": { ... },  # Serialized execution state
    "result": null,
    "stack_trace": [ ... ]
}

# Resume execution
POST /sessions/{session_id}/resume
{
    "additional_gas": 5000  # Add more gas if needed
}
```

### WebSocket Support

```javascript
// Real-time execution monitoring
const ws = new WebSocket('ws://localhost:8000/ws/sessions/{session_id}');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Step ${data.step}: ${data.operation}`);
    console.log(`Gas remaining: ${data.gas_remaining}`);
};
```

### Implementation Sketch

```python
from fastapi import FastAPI, HTTPException, WebSocket
from typing import Dict, Any, Optional
import asyncio
import uuid

app = FastAPI(title="JSL Execution Service")

# In-memory storage (use Redis/PostgreSQL in production)
programs: Dict[str, Any] = {}
sessions: Dict[str, Any] = {}

@app.post("/programs")
async def upload_program(program: dict):
    program_id = str(uuid.uuid4())
    programs[program_id] = {
        "id": program_id,
        "name": program.get("name", "unnamed"),
        "code": program["code"],
        "created_at": datetime.now()
    }
    return {"program_id": program_id}

@app.post("/sessions")
async def create_session(
    program_id: str,
    budget: Optional[dict] = None,
    args: Optional[dict] = None
):
    if program_id not in programs:
        raise HTTPException(404, "Program not found")
    
    session_id = str(uuid.uuid4())
    
    # Initialize JSL runner with resource budget
    runner = JSLRunner(config={
        "max_gas": budget.get("max_gas", 100000),
        "max_time_ms": budget.get("max_time_ms", 10000),
        "max_memory_mb": budget.get("max_memory_mb", 256),
        "enable_host": False  # Disable host access for security
    })
    
    sessions[session_id] = {
        "id": session_id,
        "program_id": program_id,
        "runner": runner,
        "status": "created",
        "args": args or {},
        "created_at": datetime.now()
    }
    
    return {"session_id": session_id}

@app.post("/sessions/{session_id}/step")
async def step_execution(session_id: str, steps: int = 1):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    
    session = sessions[session_id]
    runner = session["runner"]
    
    try:
        # Execute specified number of steps
        result = runner.step(steps)
        
        if result.is_complete:
            session["status"] = "completed"
            session["result"] = result.value
        else:
            session["status"] = "paused"
            session["continuation"] = result.serialize()
        
        return {
            "status": session["status"],
            "gas_used": runner.gas_used,
            "result": session.get("result"),
            "continuation": session.get("continuation")
        }
    except ResourceExhausted as e:
        session["status"] = "exhausted"
        return {
            "status": "exhausted",
            "reason": str(e),
            "partial_result": e.partial_result
        }

@app.websocket("/ws/sessions/{session_id}")
async def websocket_monitor(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in sessions:
        await websocket.close(code=1008, reason="Session not found")
        return
    
    session = sessions[session_id]
    runner = session["runner"]
    
    # Set up execution hooks for real-time monitoring
    def on_step(step_info):
        asyncio.create_task(websocket.send_json({
            "type": "step",
            "step": step_info["step_number"],
            "operation": step_info["operation"],
            "gas_remaining": step_info["gas_remaining"]
        }))
    
    runner.add_hook("on_step", on_step)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle control commands via WebSocket
            if data == "pause":
                runner.pause()
            elif data == "resume":
                runner.resume()
    except WebSocketDisconnect:
        runner.remove_hook("on_step", on_step)
```

### Security Considerations

1. **Sandboxing**: Disable host operations by default
2. **Resource Limits**: Enforce strict gas/memory/time limits
3. **Authentication**: Add JWT/OAuth2 for production
4. **Rate Limiting**: Prevent DOS attacks
5. **Input Validation**: Validate all JSL programs before execution
6. **Isolation**: Run each session in isolated environment

### Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Testing

```python
import pytest
from fastapi.testclient import TestClient

def test_program_upload():
    client = TestClient(app)
    response = client.post("/programs", json={
        "name": "test",
        "code": ["+", 1, 2]
    })
    assert response.status_code == 200
    assert "program_id" in response.json()

def test_execution_with_budget():
    client = TestClient(app)
    # Upload program
    program_response = client.post("/programs", json={
        "code": ["*", 100, 200]
    })
    program_id = program_response.json()["program_id"]
    
    # Create session with budget
    session_response = client.post("/sessions", json={
        "program_id": program_id,
        "budget": {"max_gas": 1000}
    })
    session_id = session_response.json()["session_id"]
    
    # Execute
    exec_response = client.post(f"/sessions/{session_id}/step", json={
        "steps": 1000
    })
    
    assert exec_response.json()["status"] == "completed"
    assert exec_response.json()["result"] == 20000
```

## Next Steps

1. Implement core endpoints
2. Add Redis for session persistence
3. Implement WebSocket monitoring
4. Add Prometheus metrics
5. Create OpenAPI client generators
6. Add GraphQL endpoint option
7. Implement batch execution API
8. Add webhook support for async execution