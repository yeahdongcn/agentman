# 🤖 Agentman: A tool for building and managing AI agents

<p align="center">
<a href="https://pypi.org/project/agentman-mcp/"><img src="https://img.shields.io/pypi/v/agentman-mcp?color=%2334D058&label=pypi" alt="PyPI version" /></a>
<a href="https://pypi.org/project/agentman-mcp/"><img src="https://img.shields.io/pypi/pyversions/agentman-mcp.svg?color=brightgreen" alt="Python versions" /></a>
<a href="https://github.com/yeahdongcn/agentman/issues"><img src="https://img.shields.io/github/issues-raw/yeahdongcn/agentman" alt="GitHub Issues" /></a>
<a href="https://pepy.tech/projects/agentman-mcp"><img alt="Pepy Total Downloads" src="https://img.shields.io/pepy/dt/agentman-mcp?label=pypi%20%7C%20downloads&color=brightgreen"/></a>
<a href="https://github.com/yeahdongcn/agentman/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/agentman-mcp?color=brightgreen" alt="License" /></a>
</p>

---

**Agentman** is a powerful Docker-like tool for building, managing, and deploying AI agents using the Model Context Protocol (MCP). With its intuitive `Agentfile` syntax, you can define complex multi-agent workflows and deploy them as containerized applications with a single command.

> [!TIP]
> **AI-Driven Development**: This project showcases the future of software development - almost entirely coded by Claude Sonnet 4 + AI Agents, demonstrating how AI can handle complex architecture design, implementation, comprehensive testing, and documentation.

## Get Started

Install the agentman package and start building AI agents in minutes:

```bash
pip install agentman-mcp                    # Install agentman
agentman build .                            # Build agent from Agentfile
agentman run --from-agentfile -t my-agent . # Build and run agent
```

## 🧠 Framework Support

Agentman supports two powerful AI agent frameworks:

### [**FastAgent**](https://github.com/evalstate/fast-agent) (Default)
- **Decorator-based approach** with `@fast.agent()` and `@fast.chain()`
- **MCP-first design** with seamless tool integration
- **Production-ready** with comprehensive logging and monitoring
- **Configuration**: Uses `fastagent.config.yaml` and `fastagent.secrets.yaml`

### [**Agno**](https://github.com/agno-agi/agno)
- **Class-based approach** with `Agent()` and `Team()`
- **Multi-model support** for OpenAI, Anthropic, and more
- **Rich tool ecosystem** with built-in integrations
- **Configuration**: Uses environment variables via `.env` file

**Switch between frameworks:**
```dockerfile
FRAMEWORK fast-agent  # Default
FRAMEWORK agno        # Alternative framework
```

### Prerequisites

- **Python 3.10+** installed on your system
- **Docker** installed and running
- **Basic understanding** of AI agents and MCP concepts

### Your First Agent

Create a URL-to-social-media content pipeline in under 5 minutes:

**1. Create a new directory:**
```bash
mkdir my-first-agent && cd my-first-agent
```

**2. Create an Agentfile:**
```dockerfile
FROM yeahdongcn/agentman-base:latest
MODEL generic.qwen3:latest

SECRET GENERIC
API_KEY ollama
BASE_URL http://host.docker.internal:11434/v1

MCP_SERVER fetch
COMMAND uvx
ARGS mcp-server-fetch
TRANSPORT stdio

AGENT url_fetcher
INSTRUCTION Given a URL, provide a complete and comprehensive summary
SERVERS fetch

AGENT social_media
INSTRUCTION Write a 280 character social media post for any given text. Respond only with the post, never use hashtags.

CHAIN post_writer
SEQUENCE url_fetcher social_media

CMD ["python", "agent.py"]
```

**3. Build and run:**
```bash
agentman run --from-agentfile -t my-first-agent .
```

**4. Test your agent** by providing a URL when prompted!

### Adding Default Prompts

Make your agent start automatically with predefined tasks:

```bash
echo "Fetch and summarize https://github.com/yeahdongcn/agentman and create a social media post about it." > prompt.txt
agentman run --from-agentfile -t my-agent-with-prompt .
```

Your agent will now automatically execute this prompt on startup! 🎉

## Overview

> [!IMPORTANT]
> Agentman leverages the [FastAgent](https://github.com/evalstate/fast-agent) framework as its foundation, providing robust agent infrastructure and seamless MCP integration. Both Anthropic (Claude family) and OpenAI (GPT-4 family) models are fully supported.

**`agentman`** enables you to create and deploy sophisticated AI agents and workflows in minutes. It is the first Docker-like framework with complete end-to-end MCP (Model Context Protocol) support, bringing familiar containerization concepts to AI agent development.

The simple declarative `Agentfile` syntax lets you concentrate on composing your prompts and MCP servers to build effective agents, while Agentman handles the complex orchestration, containerization, and deployment automatically.

### Key Capabilities

- **🐳 Docker-compatible Interface**: Familiar `build` and `run` commands with container-like semantics
- **📝 Declarative Configuration**: Define agents, workflows, and dependencies in simple `Agentfile` format
- **🔗 Multi-Agent Orchestration**: Support for chains, routers, parallel execution, and complex workflows
- **🔌 Native MCP Integration**: Built-in support for Model Context Protocol servers with zero configuration
- **📄 Intelligent Prompt Loading**: Automatically detect and load default prompts from `prompt.txt` files
- **🚀 Production-Ready Deployment**: Generate optimized Docker containers with all dependencies
- **🔐 Secure Secrets Management**: Environment-based secret handling with templating support
- **🧪 Comprehensive Testing**: 91%+ test coverage ensuring reliability and maintainability

### Agent Application Development

Prompts and configurations that define your Agent Applications are stored in simple files, with minimal boilerplate, enabling simple management and version control.

Chat with individual Agents and Components before, during and after workflow execution to tune and diagnose your application. Agents can request human input to get additional context for task completion.

Simple model selection makes testing Model <-> MCP Server interaction painless.

## 🚀 Quick Demo

Want to see Agentman in action? Watch our demonstration:

### fast-agent - Post Writer

[![Demo](https://img.youtube.com/vi/P4bRllSbNX8/0.jpg)](https://www.youtube.com/watch?v=P4bRllSbNX8)

### Agno - GitHub Profile Summary

[![Demo](https://img.youtube.com/vi/UP3Vmij89Yo/0.jpg)](https://www.youtube.com/watch?v=UP3Vmij89Yo)

**What you'll see:**
- Creating an `Agentfile` with multi-agent workflow
- Building and running the agent with one command
- Real-time agent execution with URL fetching and social media post generation

## 📖 Detailed Usage

### Building Agents

Build agent applications from an Agentfile using Docker-like syntax:

```bash
# Build in current directory
agentman build .

# Build with custom Agentfile and output directory
agentman build -f MyAgentfile -o my-output .

# Build and create Docker image
agentman build --build-docker -t my-agent:v1.0 .
```

**Generated files include:**
- **`agent.py`** - Main agent application with runtime logic
- **`fastagent.config.yaml`** - FastAgent configuration and workflow definitions
- **`fastagent.secrets.yaml`** - Secrets template for environment variables
- **`Dockerfile`** - Optimized container definition with multi-stage builds
- **`requirements.txt`** - Python dependencies (auto-generated from MCP servers)
- **`.dockerignore`** - Docker build optimization (excludes unnecessary files)
- **`prompt.txt`** - Default prompt file (copied if exists in source directory)

### Running Agents

Deploy and run agent containers with flexible options:

```bash
# Run existing image
agentman run my-agent:latest

# Build from Agentfile and run (recommended for development)
agentman run --from-agentfile --path ./my-project

# Interactive mode with port forwarding
agentman run -it -p 8080:8080 my-agent:latest

# Auto-remove container when done
agentman run --rm my-agent:latest
```

## 🏗️ Agentfile Reference

The `Agentfile` uses a Docker-like syntax to define your agent applications. Here's a comprehensive reference:

### Base Configuration

```dockerfile
FROM yeahdongcn/agentman-base:latest   # Base image
FRAMEWORK fast-agent                   # AI framework (fast-agent or agno)
MODEL anthropic/claude-3-sonnet        # Default model for agents
EXPOSE 8080                            # Expose ports
CMD ["python", "agent.py"]             # Container startup command
```

### Framework Configuration

Choose between supported AI agent frameworks:

```dockerfile
FRAMEWORK fast-agent  # Default: FastAgent framework
FRAMEWORK agno        # Alternative: Agno framework
```

**Framework Differences:**

| Feature | FastAgent | Agno |
|---------|-----------|------|
| **API Style** | Decorator-based (`@fast.agent()`) | Class-based (`Agent()`) |
| **Configuration** | YAML files | Environment variables |
| **Model Support** | MCP-optimized models | Multi-provider support |
| **Tool Integration** | MCP-first | Rich ecosystem |
| **Use Case** | Production MCP workflows | Research & experimentation |

### MCP Servers

Define external MCP servers that provide tools and capabilities:

```dockerfile
MCP_SERVER filesystem
COMMAND uvx
ARGS mcp-server-filesystem
TRANSPORT stdio
ENV PATH_PREFIX /app/data
```

### Agent Definitions

Create individual agents with specific roles and capabilities:

```dockerfile
AGENT assistant
INSTRUCTION You are a helpful AI assistant specialized in data analysis
SERVERS filesystem brave
MODEL anthropic/claude-3-sonnet
USE_HISTORY true
HUMAN_INPUT false
```

### Workflow Orchestration

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
PLAN_ITERATIONS 5
HUMAN_INPUT true
```

### Secrets Management

Secure handling of API keys and sensitive configuration:

```dockerfile
# Environment variable references
SECRET OPENAI_API_KEY
SECRET ANTHROPIC_API_KEY

# Inline values (for development only)
SECRET DATABASE_URL postgresql://localhost:5432/mydb

# Grouped secrets with multiple values
SECRET CUSTOM_API
API_KEY your_key_here
BASE_URL https://api.example.com
TIMEOUT 30
```

### Default Prompt Support

Agentman automatically detects and integrates `prompt.txt` files, providing zero-configuration default prompts for your agents.

#### 🌟 **Key Features**
- **🔍 Automatic Detection**: Simply place a `prompt.txt` file in your project root
- **🐳 Docker Integration**: Automatically copied into containers during build
- **🔄 Runtime Loading**: Agent checks for and loads prompt content at startup
- **⚡ Zero Configuration**: No Agentfile modifications required

#### 📋 **How It Works**

1. **Build Time**: Agentman scans your project directory for `prompt.txt`
2. **Container Build**: If found, the file is automatically copied to the Docker image
3. **Runtime**: Generated agent checks for the file and loads its content
4. **Execution**: Prompt content is passed to `await agent(prompt_content)` at startup

#### 📁 **Project Structure Example**

```
my-agent/
├── Agentfile                # Agent configuration
├── prompt.txt              # ← Your default prompt (auto-loaded)
└── agent/                  # ← Generated output directory
    ├── agent.py            #   Generated agent with prompt loading logic
    ├── prompt.txt          #   ← Copied during build process
    ├── Dockerfile          #   Contains COPY prompt.txt instruction
    └── requirements.txt    #   Python dependencies
```

#### 💡 **Example Prompts**

**Task-Specific Prompt:**
```text
Analyze the latest GitHub releases for security vulnerabilities and generate a summary report.
```

**User-Specific Prompt:**
```text
I am a GitHub user with the username "yeahdongcn" and I need help updating my GitHub profile information.
```

**Complex Workflow Prompt:**
```text
Process the following workflow:
1. Clone the repository https://github.com/ollama/ollama
2. Checkout the latest release tag
3. Analyze the changelog for breaking changes
4. Generate a migration guide
```

#### 🛠️ **Generated Logic**

When `prompt.txt` exists, Agentman automatically generates this logic in your `agent.py`:

```python
import os

# Check for default prompt file
prompt_file = "prompt.txt"
if os.path.exists(prompt_file):
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read().strip()
    if prompt_content:
        await agent(prompt_content)
```

This ensures your agent automatically executes the default prompt when the container starts.

## 🎯 Example Projects

### 1. GitHub Profile Manager (with Default Prompt)

A comprehensive GitHub profile management agent that automatically loads a default prompt.

**Project Structure:**
```
github-profile-manager/
├── Agentfile
├── prompt.txt          # Default prompt automatically loaded
└── agent/              # Generated files
    ├── agent.py
    ├── prompt.txt      # Copied during build
    └── ...
```

**prompt.txt:**
```text
I am a GitHub user with the username "yeahdongcn" and I need help updating my GitHub profile information.
```

**Key Features:**
- Multi-agent chain for profile data collection, generation, and updating
- Automatic prompt loading from `prompt.txt`
- Integration with GitHub MCP server and fetch capabilities

### 2. GitHub Repository Maintainer

A specialized agent for maintaining GitHub repositories with automated release management.

**Project Structure:**
```
github-maintainer/
├── Agentfile
├── prompt.txt          # Default task: "Clone https://github.com/ollama/ollama and checkout the latest release tag."
└── agent/              # Generated files
```

**Key Features:**
- Release checking and validation
- Repository cloning and management
- Automated maintenance workflows

### 3. URL-to-Social Content Pipeline

A simple yet powerful content processing chain for social media.

**Project Structure:**
```
chain-ollama/
├── Agentfile
└── agent/              # Generated files
```

**Key Features:**
- URL content fetching and summarization
- Social media post generation (280 characters, no hashtags)
- Sequential agent chain processing

### 4. Advanced Multi-Agent System

Example of a more complex multi-agent system with routers and orchestrators:

```dockerfile
FROM yeahdongcn/agentman-base:latest
MODEL anthropic/claude-3-sonnet

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

## 📁 Project Structure

```
agentman/
├── src/agentman/           # Core source code
│   ├── __init__.py
│   ├── cli.py             # Command-line interface
│   ├── agent_builder.py   # Agent building logic
│   ├── agentfile_parser.py # Agentfile parsing
│   └── common.py          # Shared utilities
├── examples/              # Example projects
│   ├── github-profile-manager/
│   ├── github-maintainer/
│   ├── chain-ollama/
│   └── chain-aliyun/
├── tests/                 # Comprehensive test suite
├── docker/               # Docker base images
└── README.md             # This file
```

## 🏗️ Building from Source

```bash
git clone https://github.com/yeahdongcn/agentman.git
cd agentman

# Install
make install
```

## 🧪 Testing

Agentman includes comprehensive test suites with high coverage:

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov
```

### Test Coverage
- **91%+ overall coverage** across core modules
- **Agent Builder**: Comprehensive tests for agent generation and Docker integration
- **Agentfile Parser**: Complete syntax parsing and validation tests
- **Prompt.txt Support**: Full coverage of automatic prompt detection and loading
- **Dockerfile Generation**: Tests for container build optimization

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

- **Python**: 3.10+ (supports 3.10, 3.11, 3.12, 3.13)
- **Docker**: Required for containerization and running agents
- **Operating System**: Unix-like systems (Linux, macOS, WSL2)
- **Memory**: 2GB+ RAM recommended for multi-agent workflows
- **Storage**: 1GB+ available space for base images and dependencies

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **🤖 AI-Powered Development**: This project showcases the future of software development - almost entirely coded by Claude Sonnet 4 + AI Agents, demonstrating how AI can handle complex architecture design, implementation, comprehensive testing, and documentation
- **🏗️ Built on [FastAgent](https://github.com/evalstate/fast-agent)**: Agentman leverages the fast-agent framework as its foundation, providing robust agent infrastructure and seamless MCP integration
- **🐳 Inspired by [Podman](https://github.com/containers/podman)**: Just as Podman provides a Docker-compatible interface for containers, Agentman brings familiar containerization concepts to AI agent management
- **🧪 Test-Driven Excellence**: Achieved 91%+ test coverage through AI-driven test generation, ensuring reliability and maintainability
- **🌟 Community-Driven**: Built with the vision of making AI agent development accessible to everyone

---

<div align="center">

**🚀 Ready to revolutionize your AI workflows?**

**[Get Started](#get-started)** • **[View Examples](#-example-projects)** • **[Contribute](#-contributing)**

*Join thousands of developers building the future with AI agents* ✨

[![GitHub stars](https://img.shields.io/github/stars/yeahdongcn/agentman?style=social)](https://github.com/yeahdongcn/agentman)
[![PyPI downloads](https://img.shields.io/pypi/dm/agentman-mcp?color=blue)](https://pypi.org/project/agentman-mcp/)

</div>
