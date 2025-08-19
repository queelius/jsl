# JSL Model Context Protocol (MCP) Integration

Integration layer for connecting JSL with AI/LLM systems through the Model Context Protocol.

## Overview

The Model Context Protocol enables LLMs to interact with external systems in a structured, capability-based manner. This integration allows AI assistants to:

1. Execute JSL programs safely
2. Manipulate JSON data using JSL's functional primitives
3. Maintain stateful conversations with serializable context
4. Perform complex data transformations

## MCP Server Implementation

```python
from mcp import MCPServer, Tool, Resource
from jsl.runner import JSLRunner
import json

class JSLMCPServer(MCPServer):
    """MCP server exposing JSL capabilities to LLMs."""
    
    def __init__(self):
        super().__init__("jsl-mcp-server")
        self.sessions = {}
        
    @Tool(
        name="jsl_execute",
        description="Execute a JSL program",
        parameters={
            "code": "JSL program as JSON array",
            "args": "Arguments to pass to the program",
            "max_gas": "Maximum gas to consume (default: 10000)"
        }
    )
    async def execute_jsl(self, code: list, args: dict = None, max_gas: int = 10000):
        """Execute a JSL program with resource limits."""
        runner = JSLRunner(config={"max_gas": max_gas})
        
        try:
            # Define any arguments
            if args:
                for key, value in args.items():
                    runner.execute(["def", key, ["@", value]])
            
            # Execute the program
            result = runner.execute(code)
            
            return {
                "success": True,
                "result": result,
                "gas_used": runner.gas_used
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @Tool(
        name="jsl_transform",
        description="Transform JSON data using JSL operations",
        parameters={
            "data": "Input JSON data",
            "operations": "List of JSL transform operations"
        }
    )
    async def transform_json(self, data: Any, operations: list):
        """Apply JSL transformations to JSON data."""
        runner = JSLRunner()
        
        # Define the data
        runner.execute(["def", "data", ["@", data]])
        
        # Build the transform expression
        transform_expr = ["transform", "data"] + operations
        
        try:
            result = runner.execute(transform_expr)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @Tool(
        name="jsl_query",
        description="Query JSON data using JSL where clauses",
        parameters={
            "data": "Input JSON collection",
            "condition": "JSL condition expression"
        }
    )
    async def query_json(self, data: list, condition: list):
        """Filter JSON data using JSL where clauses."""
        runner = JSLRunner()
        
        # Define the data
        runner.execute(["def", "data", ["@", data]])
        
        # Build where expression
        where_expr = ["where", "data", condition]
        
        try:
            result = runner.execute(where_expr)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @Resource(
        name="jsl_session",
        description="Stateful JSL execution session"
    )
    async def get_session(self, session_id: str = None):
        """Get or create a stateful JSL session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = JSLRunner()
        
        return {
            "session_id": session_id,
            "environment": self.sessions[session_id].get_environment()
        }
```

## LLM Usage Examples

### Claude Integration

```python
# In Claude's system prompt or via MCP
tools:
  - jsl_execute:
      description: Execute JSL programs for data manipulation
      examples:
        - Calculate fibonacci:
          code: ["def", "fib", ["lambda", ["n"], ...]]
          args: {"n": 10}
        
        - Process JSON data:
          code: ["where", "users", [">", "age", 25]]
          args: {"users": [...]}

# Claude can then use it like:
"I'll filter the users over 25 using JSL:"
<use_tool name="jsl_execute">
  <code>["where", "users", [">", "age", 25]]</code>
  <args>{"users": [{"name": "Alice", "age": 30}, ...]}</args>
</use_tool>
```

### ChatGPT Function Calling

```json
{
  "name": "jsl_transform",
  "description": "Transform JSON data using JSL",
  "parameters": {
    "type": "object",
    "properties": {
      "data": {
        "type": "array",
        "description": "JSON array to transform"
      },
      "operations": {
        "type": "array",
        "description": "JSL transformation operations"
      }
    }
  }
}
```

## Security Model

### Capability-Based Security

```python
class SecureJSLMCP(JSLMCPServer):
    """MCP server with capability-based security."""
    
    def __init__(self, capabilities: set = None):
        super().__init__()
        self.capabilities = capabilities or {
            "compute",  # Basic computation
            "transform",  # Data transformation
            "query",  # Data querying
            # "host",  # Disabled by default
            # "network",  # Disabled by default
        }
    
    async def execute_jsl(self, code: list, **kwargs):
        # Check for prohibited operations
        if self._contains_host_ops(code) and "host" not in self.capabilities:
            return {
                "success": False,
                "error": "Host operations not permitted"
            }
        
        # Execute with sandboxing
        runner = JSLRunner(config={
            "enable_host": "host" in self.capabilities,
            "max_gas": kwargs.get("max_gas", 10000)
        })
        
        return await super().execute_jsl(code, **kwargs)
```

## Integration Patterns

### 1. Data Processing Assistant

```python
# LLM can help users process data
USER: "I have a list of orders. Can you find all orders over $100 and add a 'high_value' flag?"

ASSISTANT: "I'll use JSL to filter and transform your orders:"

<use_tool name="jsl_transform">
  <data>[...orders...]</data>
  <operations>[
    ["where", "data", [">", "total", 100]],
    ["transform", "data", ["assign", "@high_value", true]]
  ]</operations>
</use_tool>
```

### 2. Code Generation

```python
# LLM generates JSL programs
USER: "Write a function to calculate the factorial of a number"

ASSISTANT: "Here's a JSL factorial function:"

<use_tool name="jsl_execute">
  <code>
    ["def", "factorial", 
      ["lambda", ["n"],
        ["if", ["<=", "n", 1], 
          1,
          ["*", "n", ["factorial", ["-", "n", 1]]]]]]
  </code>
  <args>{"n": 5}</args>
</use_tool>
```

### 3. Interactive Data Exploration

```python
# Stateful session for exploration
SESSION = create_jsl_session()

USER: "Load the sales data"
<execute session_id=SESSION>
  ["def", "sales", ["@", [...]]]
</execute>

USER: "What's the total revenue?"
<execute session_id=SESSION>
  ["reduce", "+", ["pluck", "sales", "@amount"], 0]
</execute>

USER: "Group by category"
<execute session_id=SESSION>
  ["group-by", ["lambda", ["x"], ["get", "x", "@category"]], "sales"]
</execute>
```

## Future Enhancements

1. **Streaming Execution**: Stream JSL execution steps to LLM for debugging
2. **Code Explanation**: Generate natural language explanations of JSL code
3. **Error Recovery**: Help LLMs understand and fix JSL errors
4. **Performance Hints**: Suggest optimizations for JSL programs
5. **Visual Output**: Generate visualizations from JSL data
6. **Multi-Modal**: Support image/audio processing through JSL
7. **Federated Execution**: Distribute JSL computation across multiple nodes
8. **Verification**: Formal verification of JSL programs for safety