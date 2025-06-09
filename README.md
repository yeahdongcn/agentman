# 🤖 Agentman: A tool for building and managing AI agents

[![PyPI version](https://img.shields.io/pypi/v/agentman-mcp.svg)](https://pypi.org/project/agentman-mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/agentman-mcp.svg)](https://pypi.org/project/agentman-mcp/)
[![GitHub Issues](https://img.shields.io/github/issues/yeahdongcn/agentman.svg)](https://github.com/yeahdongcn/agentman/issues)
[![Pepy Total Downloads](https://img.shields.io/pepy/dt/agentman-mcp?label=pypi%20%7C%20downloads)](https://pepy.tech/projects/agentman-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Agentman is a powerful Docker-like tool for building, managing, and deploying AI agents using the Model Context Protocol (MCP). With its intuitive `Agentfile` syntax, you can define complex multi-agent workflows and deploy them as containerized applications with a single command.

> 🤖 **AI-Driven Development**: This project is almost entirely coded by Claude Sonnet 4 + AI Agents, showcasing the power of AI-assisted software development. From architecture design to comprehensive testing, AI has been the primary developer, demonstrating the future of collaborative human-AI programming.

## 📦 Installation

```bash
pip install agentman-mcp
```

## ✨ Features

- **🐳 Docker-like Interface**: Familiar `build` and `run` commands with Docker-compatible syntax
- **📝 Declarative Configuration**: Define agents, workflows, and dependencies in simple `Agentfile` format
- **🔗 Multi-Agent Workflows**: Support for chains, routers, and orchestrators
- **🔌 MCP Integration**: Built-in support for Model Context Protocol servers
- **🚀 One-Command Deploy**: Build and run containerized agents instantly
- **🔐 Secure Secrets Management**: Environment-based secret handling
- **🎯 Production Ready**: Generate complete Docker environments with all dependencies

## 🚀 Quick Start

### Installation

```bash
pip install agentman-mcp
```

### 30-Second Demo

Create a simple URL-to-social-media agent in 3 steps:

1. **Create an Agentfile:**
```dockerfile
# Agentfile
FROM yeahdongcn/agentman:base
MODEL generic.qwen3:latest

SECRET GENERIC
API_KEY ollama
BASE_URL http://host.docker.internal:11434/v1

# Fetch MCP server for URL fetching
MCP_SERVER fetch
COMMAND uvx
ARGS mcp-server-fetch
TRANSPORT stdio

# URL fetcher agent
AGENT url_fetcher
INSTRUCTION Given a URL, provide a complete and comprehensive summary
SERVERS fetch

# Social media post writer agent
AGENT social_media
INSTRUCTION Write a 280 character social media post for any given text. Respond only with the post, never use hashtags.

# Chain that connects url_fetcher -> social_media
CHAIN post_writer
SEQUENCE url_fetcher social_media

CMD ["python", "agent.py"]
```

2. **Build and run:**
```bash
agentman run --from-agentfile -t my-agent .
```

3. **Your AI agent is now running!** 🎉

[![Demo](https://img.youtube.com/vi/P4bRllSbNX8/0.jpg)](https://www.youtube.com/watch?v=P4bRllSbNX8)

## 📖 Detailed Usage

### Building Agents

Build agent files from an Agentfile (Docker-like syntax):

```bash
# Build in current directory
agentman build .

# Build with custom Agentfile and output
agentman build -f MyAgentfile -o my-output .

# Build and create Docker image
agentman build --build-docker -t my-agent:v1.0 .
```

Generated files include:
- `agent.py` - Main agent application
- `fastagent.config.yaml` - FastAgent configuration
- `fastagent.secrets.yaml` - Secrets template
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies
- `.dockerignore` - Docker build optimization

### Running Agents

Run existing images or build-and-run from Agentfile:

```bash
# Run existing image
agentman run my-agent:latest

# Build from Agentfile and run
agentman run --from-agentfile --path ./my-project

# Interactive mode with port forwarding
agentman run -it -p 8080:8080 my-agent:latest

# Auto-remove container when done
agentman run --rm my-agent:latest
```

## 🏗️ Agentfile Reference

### Base Configuration

```dockerfile
FROM yeahdongcn/agentman:base     # Base image
MODEL anthropic/claude-3-sonnet   # Default model for agents
EXPOSE 8080                       # Expose ports
CMD ["python", "agent.py"]        # Container startup command
```

### MCP Servers

```dockerfile
MCP_SERVER filesystem
COMMAND uvx
ARGS mcp-server-filesystem
TRANSPORT stdio
ENV PATH_PREFIX /app/data
```

### Agents

```dockerfile
AGENT assistant
INSTRUCTION You are a helpful AI assistant specialized in data analysis
SERVERS filesystem brave
MODEL anthropic/claude-3-sonnet
USE_HISTORY true
HUMAN_INPUT false
```

### Workflows

**Chains** (Sequential processing):
```dockerfile
CHAIN data_pipeline
SEQUENCE data_loader data_processor data_exporter
CUMULATIVE true
```

**Routers** (Conditional routing):
```dockerfile
ROUTER query_router
AGENTS sql_agent api_agent file_agent
INSTRUCTION Route queries based on data source type
```

**Orchestrators** (Complex coordination):
```dockerfile
ORCHESTRATOR project_manager
AGENTS developer tester deployer
PLAN_TYPE iterative
MAX_ITERATIONS 5
HUMAN_INPUT true
```

### Secrets Management

```dockerfile
# Simple references
SECRET OPENAI_API_KEY
SECRET ANTHROPIC_API_KEY

# Inline values (for development)
SECRET DATABASE_URL postgresql://localhost:5432/mydb

# Grouped secrets
SECRET CUSTOM_API
API_KEY your_key_here
BASE_URL https://api.example.com
TIMEOUT 30
```

## 🎯 Example Projects

### 1. Content Processing Pipeline
```dockerfile
FROM yeahdongcn/agentman:base
MODEL anthropic/claude-3-sonnet

MCP_SERVER brave
COMMAND uvx
ARGS mcp-server-brave-search

AGENT researcher
INSTRUCTION Research topics and gather comprehensive information
SERVERS brave

AGENT writer
INSTRUCTION Transform research into engaging blog posts

AGENT editor
INSTRUCTION Review and improve content for clarity and engagement

CHAIN content_pipeline
SEQUENCE researcher writer editor
```

### 2. Customer Support System
```dockerfile
FROM yeahdongcn/agentman:base
MODEL anthropic/claude-3-haiku

MCP_SERVER database
COMMAND uvx
ARGS mcp-server-postgres

AGENT classifier
INSTRUCTION Classify customer inquiries by type and urgency
SERVERS database

AGENT support_agent
INSTRUCTION Provide helpful customer support responses
SERVERS database

AGENT escalation_agent
INSTRUCTION Handle complex issues requiring human intervention
HUMAN_INPUT true

ROUTER support_router
AGENTS support_agent escalation_agent
INSTRUCTION Route based on inquiry complexity and urgency
```

### 3. Data Analysis Workflow
```dockerfile
FROM yeahdongcn/agentman:base
MODEL anthropic/claude-3-sonnet

MCP_SERVER filesystem
COMMAND uvx
ARGS mcp-server-filesystem

AGENT data_loader
INSTRUCTION Load and validate data from various sources
SERVERS filesystem

AGENT analyst
INSTRUCTION Perform statistical analysis and generate insights
SERVERS filesystem

AGENT visualizer
INSTRUCTION Create charts and visual representations
SERVERS filesystem

ORCHESTRATOR data_science_lead
AGENTS data_loader analyst visualizer
PLAN_TYPE full
INSTRUCTION Coordinate comprehensive data analysis projects
```

## 🔧 Advanced Configuration

### Custom Base Images

```dockerfile
FROM python:3.11-slim
MODEL openai/gpt-4

# Your custom setup...
RUN apt-get update && apt-get install -y curl

AGENT custom_agent
INSTRUCTION Specialized agent with custom environment
```

### Environment Variables

```dockerfile
MCP_SERVER api_server
COMMAND python
ARGS -m my_custom_server
ENV API_TIMEOUT 30
ENV RETRY_COUNT 3
ENV DEBUG_MODE false
```

### Multi-Model Setup

```dockerfile
AGENT fast_responder
MODEL anthropic/claude-3-haiku
INSTRUCTION Handle quick queries

AGENT deep_thinker
MODEL anthropic/claude-3-opus
INSTRUCTION Handle complex analysis tasks
```

## 🏗️ Building from Source

```bash
git clone https://github.com/yeahdongcn/agentman.git
cd agentman

# Install development dependencies
pip install -e ".[dev]"

# Run tests
make test

# Run with coverage
make test-coverage

# Format code
make format
```

## 🧪 Testing

Agentman includes comprehensive test suites:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agentman tests/

# Run specific test modules
pytest tests/test_agent_builder.py
pytest tests/test_agentfile_parser.py
```

The project maintains high test coverage with 91%+ coverage for core modules.

## 🤝 Contributing

We welcome contributions! This project serves as a showcase of AI-driven development, being almost entirely coded by Claude Sonnet 4 + AI Agents. This demonstrates how AI can handle complex software development tasks including architecture design, implementation, testing, and documentation.

### Development Workflow

1. **Fork and clone** the repository
2. **Create a feature branch** from `main`
3. **Write tests** for new functionality (AI-generated tests achieve 91%+ coverage)
4. **Ensure tests pass** with `make test`
5. **Format code** with `make format`
6. **Submit a pull request** with clear description

### Areas for Contribution

- 🔌 New MCP server integrations
- 🤖 Additional agent workflow patterns
- 📚 Documentation and examples
- 🧪 Test coverage improvements
- 🐛 Bug fixes and optimizations

## 📋 System Requirements

- Python 3.10+
- Docker (for containerization)
- Unix-like system (Linux, macOS, WSL2)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **🤖 AI-Powered Development**: Almost entirely coded by Claude Sonnet 4 + AI Agents, demonstrating the future of collaborative human-AI software development
- **🏗️ Built on [Fast-Agent](https://github.com/evalstate/fast-agent)**: This project heavily relies on the fast-agent framework as its foundation, providing the core agent infrastructure and MCP integration
- **🐳 Inspired by [Podman](https://github.com/containers/podman)**: The name "Agentman" is inspired by Podman, the container engine that provides a Docker-compatible command-line interface. Like Podman for containers, Agentman aims to provide an intuitive, powerful CLI for AI agent management
- Inspired by Docker's intuitive command-line interface
- Comprehensive testing and documentation generated through AI assistance
- Achieved 91%+ test coverage through AI-driven test generation

---

**Ready to build your first AI agent?** Start with our [Quick Start](#-quick-start) guide and join the growing community of AI agent developers! 🚀
