# JSL Integrations

This directory contains various integrations for JSL (JSON Serializable Language). Each integration is kept separate from the main codebase to maintain clarity while exploring different use cases and platforms.

## Available Integrations

### fastapi/
**FastAPI Web Service for JSL Execution**
- REST API for submitting JSL programs
- Program upload and management
- Pauseable/resumable execution endpoints
- Resource budget configuration (gas metering)
- Session management for stateful execution
- WebSocket support for real-time execution monitoring

### mcp/
**Model Context Protocol (MCP) Integration**
- Bridge JSL with AI/LLM systems
- Tool definitions for LLMs to execute JSL
- Context management for AI assistants
- Capability-based security for AI interactions

### jupyter/
**Jupyter Notebook Integration**
- JSL kernel for Jupyter notebooks
- Magic commands for JSL execution
- Interactive visualization of JSL data structures
- Integration with pandas/numpy for data science workflows

### vscode/
**Visual Studio Code Extension**
- Syntax highlighting for JSL
- IntelliSense/autocomplete
- Inline execution and debugging
- Integrated REPL

### langchain/
**LangChain Integration**
- JSL as a tool for LangChain agents
- Custom chains for JSL program generation
- Memory management using JSL's serializable state

### web/
**Web Browser Integration**
- JavaScript/TypeScript client library
- WebAssembly runtime for browser execution
- React/Vue/Angular components for JSL

### cli/
**Enhanced CLI Tools**
- Advanced REPL features
- Script management utilities
- Performance profiling tools
- Migration tools from other languages

### docker/
**Docker Integration**
- Containerized JSL runtime
- Multi-stage builds for optimized images
- Docker Compose examples for distributed JSL

### kubernetes/
**Kubernetes Integration**
- Kubernetes operators for JSL workloads
- CRDs for JSL program definitions
- Horizontal pod autoscaling based on resource usage
- Service mesh integration for distributed execution

### repl/
**Advanced REPL Features**
- Rich terminal UI (using textual/rich)
- History management and search
- Multi-line editing
- Export/import sessions

## Contributing

Each integration should maintain its own README with:
1. Installation instructions
2. Usage examples
3. API documentation
4. Test coverage
5. Performance considerations

## Status

Most integrations are currently placeholders. Priority order for implementation:
1. **fastapi** - Demonstrates network-native capabilities
2. **mcp** - AI/LLM integration
3. **jupyter** - Data science workflows
4. **vscode** - Developer experience