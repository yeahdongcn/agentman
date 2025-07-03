# Agentfile Docker Buildx Frontend

This is a custom Docker Buildx frontend that allows you to build Docker images directly from Agentfile syntax, without needing to manually convert them to Dockerfiles first.

## What is this?

Docker Buildx supports custom frontends through the `# syntax=` directive. This frontend acts as a translator that:
1. Parses Agentfile syntax
2. Converts it to appropriate Dockerfile instructions
3. Generates configuration files for agents, MCP servers, etc.
4. Builds the final Docker image

## Architecture

```
Agentfile -> Custom Frontend (Go) -> Generated Dockerfile -> Docker Image
```

The frontend is written in Go because:
- Docker and BuildKit are written in Go
- Better performance and integration with Docker ecosystem
- Access to BuildKit's Low Level Builder (LLB) API

## Features

### Supported Agentfile Instructions

- **FROM**: Base image specification
- **FRAMEWORK**: Agent framework (agno, fast-agent)
- **MODEL**: Default model specification
- **SECRET**: Secret/environment variable management
- **MCP_SERVER**: MCP server definitions with sub-instructions:
  - COMMAND, ARGS, TRANSPORT, URL, ENV
- **AGENT**: Agent definitions with sub-instructions:
  - INSTRUCTION, SERVERS, MODEL, USE_HISTORY, HUMAN_INPUT, DEFAULT
- **ROUTER**: Router definitions with sub-instructions:
  - AGENTS, MODEL, INSTRUCTION, DEFAULT
- **EXPOSE**: Port exposure
- **CMD**: Container start command
- All standard Dockerfile instructions (RUN, COPY, ENV, etc.)

### What the Frontend Does

1. **Parses Agentfile syntax** including:
   - Multi-line instructions with backslash continuation
   - Quoted strings and arguments
   - Context-aware sub-instructions

2. **Generates configuration files**:
   - `/app/config/mcp_servers.json` - MCP server configurations
   - `/app/config/agents.json` - Agent definitions
   - `/app/config/routers.json` - Router configurations

3. **Creates framework-specific code**:
   - AGNO: Generates AGNO-compatible agent code
   - Fast-Agent: Generates Fast-Agent-compatible code

4. **Handles secrets as build arguments**:
   - Converts SECRET instructions to ARG instructions
   - Supports both named secrets and secret with values

## Installation

### Option 1: Build locally
```bash
cd agentfile-frontend
go build -o agentfile-frontend main.go
```

### Option 2: Build Docker image
```bash
docker build -t agentfile-frontend .
```

### Option 3: Use as BuildKit frontend (Future)
Once published to a registry:
```dockerfile
# syntax=yeahdongcn/agentfile-frontend:latest
# Your Agentfile content here...
```

## Usage

### Basic Usage
```bash
# Parse and convert Agentfile to Dockerfile
./agentfile-frontend /path/to/Agentfile

# Or with Go
go run main.go /path/to/Agentfile
```

### Example Output
Given this Agentfile:
```agentfile
FROM yeahdongcn/agentman-base:latest
FRAMEWORK agno
MODEL deepseek/deepseek-chat

SECRET DEEPSEEK_API_KEY
SECRET OPENAI_API_KEY

MCP_SERVER web_search
COMMAND uvx
ARGS mcp-server-duckduckgo
TRANSPORT stdio

AGENT assistant
INSTRUCTION You are a helpful AI assistant.
SERVERS web_search
MODEL deepseek/deepseek-chat

CMD ["python", "agent.py"]
```

The frontend generates:
```dockerfile
# syntax=agentfile-frontend
# Generated from Agentfile

FROM yeahdongcn/agentman-base:latest

# Secrets as build arguments
ARG DEEPSEEK_API_KEY
ARG OPENAI_API_KEY

# Generate agent configuration
RUN mkdir -p /app/config
RUN echo '{"web_search": {...}}' > /app/config/mcp_servers.json
RUN echo '{"assistant": {...}}' > /app/config/agents.json

# Generate framework-specific code
RUN echo 'Generating AGNO agent code...' && \
    echo 'import agno' > /app/agent.py && \
    echo 'print("AGNO agent started")' >> /app/agent.py

WORKDIR /app

# Start command
CMD ["python","agent.py"]
```

## Integration with Docker Buildx

### Current Status
This frontend currently works as a standalone translator. To use it with Docker Buildx as a true frontend, you would need to:

1. **Publish the frontend image** to a container registry
2. **Implement BuildKit LLB integration** (more complex)
3. **Use the syntax directive**:
   ```dockerfile
   # syntax=your-registry/agentfile-frontend:latest
   ```

### Future Enhancements

1. **Full BuildKit Integration**:
   - Implement proper BuildKit frontend protocol
   - Support all BuildKit features (mount, secrets, etc.)
   - Better error handling and progress reporting

2. **Advanced Features**:
   - Multi-stage builds
   - Build-time secret injection
   - Cross-platform builds
   - Build caching optimization

3. **IDE Integration**:
   - VS Code extension for Agentfile syntax highlighting
   - Language server for IntelliSense
   - Real-time validation

## Development

### Project Structure
```
agentfile-frontend/
├── main.go              # Main parser and generator
├── go.mod              # Go module definition
├── Dockerfile          # Frontend container image
└── README.md          # This file
```

### Key Components

1. **AgentfileParser**: Parses Agentfile syntax into structured data
2. **generateDockerfile()**: Converts parsed data to Dockerfile
3. **Context Management**: Handles nested instructions (AGENT -> INSTRUCTION)
4. **Quote Handling**: Properly parses quoted strings and arguments

### Testing
```bash
# Test with different Agentfile examples
go run main.go ../examples/agno-example/Agentfile
go run main.go ../examples/agno-advanced/Agentfile
go run main.go ../examples/github-maintainer/Agentfile
```

## Benefits

1. **Simplified Workflow**: Write Agentfiles directly, no manual conversion
2. **Type Safety**: Compile-time validation of Agentfile syntax
3. **Consistency**: Standardized output format
4. **Extensibility**: Easy to add new instructions and features
5. **Docker Integration**: Seamless integration with existing Docker workflows

## Limitations

1. **Not yet a true BuildKit frontend**: Requires additional work for full integration
2. **Limited error handling**: Basic error reporting
3. **No incremental builds**: Regenerates everything on each build
4. **No advanced BuildKit features**: No support for secrets, mounts, etc.

## Contributing

1. Add new instruction support in `parseLine()`
2. Implement corresponding handlers
3. Update `generateDockerfile()` for new features
4. Add tests for new functionality

## License

[Same as parent project]
