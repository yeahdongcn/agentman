"""
Unit tests for agentfile_parser module.

Tests cover all aspects of the AgentfileParser including:
- Basic parsing functionality
- All instruction types (FROM, MODEL, SECRET, EXPOSE, etc.)
- Server definitions
- Agent definitions
- Workflow definitions (ROUTER, CHAIN, ORCHESTRATOR)
- Secret handling (simple, inline values, contexts)
- Error handling and validation
"""

import pytest
import tempfile
import os

from agentman.agentfile_parser import (
    AgentfileParser,
    AgentfileConfig,
    MCPServer,
    Agent,
    Router,
    Chain,
    Orchestrator,
    SecretValue,
    SecretContext
)


class TestAgentfileParser:
    """Test suite for AgentfileParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AgentfileParser()

    def test_init(self):
        """Test parser initialization."""
        assert self.parser.config is not None
        assert isinstance(self.parser.config, AgentfileConfig)
        assert self.parser.config.base_image == "fast-agent:latest"
        assert self.parser.config.secrets == []
        assert self.parser.config.servers == {}
        assert self.parser.config.agents == {}

    def test_parse_content_basic(self):
        """Test parsing basic Agentfile content."""
        content = """
FROM python:3.11-slim
MODEL anthropic/claude-3-sonnet-20241022
EXPOSE 8080
CMD ["agentman", "run"]
"""
        config = self.parser.parse_content(content)

        assert config.base_image == "python:3.11-slim"
        assert config.default_model == "anthropic/claude-3-sonnet-20241022"
        assert config.expose_ports == [8080]
        assert config.cmd == ["agentman", "run"]

    def test_parse_content_with_secrets(self):
        """Test parsing content with secrets."""
        content = """
        FROM my-base-image
        MODEL gpt-4
        SECRET my_secret
        """
        config = self.parser.parse_content(content)
        assert config.base_image == "my-base-image"
        assert config.default_model == "gpt-4"
        assert len(config.secrets) == 1

    def test_parse_content_with_server(self):
        """Test parsing Agentfile with server definition."""
        content = """
FROM python:3.11-slim
SERVER filesystem
    COMMAND uv
    ARGS tool run mcp-server-filesystem /tmp
    TRANSPORT stdio
"""
        config = self.parser.parse_content(content)

        assert len(config.servers) == 1
        assert "filesystem" in config.servers
        server = config.servers["filesystem"]
        assert server.name == "filesystem"
        assert server.command == "uv"
        assert server.args == ["tool", "run", "mcp-server-filesystem", "/tmp"]
        assert server.transport == "stdio"

    def test_parse_file(self):
        """Test parsing Agentfile from file."""
        content = """
FROM python:3.11-slim
MODEL anthropic/claude-3-sonnet-20241022
EXPOSE 8080
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.agentfile', delete=False) as f:
            f.write(content)
            f.flush()

            try:
                config = self.parser.parse_file(f.name)
                assert config.base_image == "python:3.11-slim"
                assert config.default_model == "anthropic/claude-3-sonnet-20241022"
                assert config.expose_ports == [8080]
            finally:
                os.unlink(f.name)

    def test_parse_file_not_exists(self):
        """Test parsing from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file("/non/existent/file")

    def test_empty_agentfile(self):
        """Test parsing empty Agentfile."""
        config = self.parser.parse_content("")
        assert config.base_image == "fast-agent:latest"
        assert len(config.secrets) == 0
        assert len(config.servers) == 0
        assert len(config.agents) == 0

    def test_comments_and_whitespace(self):
        """Test parsing with comments and extra whitespace."""
        content = """
# This is a comment
FROM python:3.11-slim

# Another comment
MODEL anthropic/claude-3-sonnet-20241022

    # Indented comment
EXPOSE 8080

"""
        config = self.parser.parse_content(content)
        assert config.base_image == "python:3.11-slim"
        assert config.default_model == "anthropic/claude-3-sonnet-20241022"
        assert config.expose_ports == [8080]


class TestDataClasses:
    """Test suite for data classes used by AgentfileParser."""

    def test_mcp_server_creation(self):
        """Test MCPServer data class creation."""
        server = MCPServer(
            name="test",
            command="uv",
            args=["tool", "run"],
            transport="stdio",
            url="http://localhost",
            env={"KEY": "value"}
        )
        assert server.name == "test"
        assert server.command == "uv"
        assert server.args == ["tool", "run"]
        assert server.transport == "stdio"
        assert server.url == "http://localhost"
        assert server.env == {"KEY": "value"}

    def test_agent_creation(self):
        """Test Agent data class creation."""
        agent = Agent(
            name="assistant",
            instruction="You are helpful",
            servers=["filesystem"],
            model="anthropic/claude-3-sonnet-20241022",
            use_history=True,
            human_input=False
        )
        assert agent.name == "assistant"
        assert agent.instruction == "You are helpful"
        assert agent.servers == ["filesystem"]
        assert agent.model == "anthropic/claude-3-sonnet-20241022"
        assert agent.use_history is True
        assert agent.human_input is False

    def test_secret_value_creation(self):
        """Test SecretValue data class creation."""
        secret = SecretValue(name="API_KEY", value="test-value")
        assert secret.name == "API_KEY"
        assert secret.value == "test-value"

    def test_secret_context_creation(self):
        """Test SecretContext data class creation."""
        secret = SecretContext(
            name="GENERIC",
            values={"API_KEY": "value", "BASE_URL": "url"}
        )
        assert secret.name == "GENERIC"
        assert secret.values == {"API_KEY": "value", "BASE_URL": "url"}

    def test_router_creation(self):
        """Test Router data class creation."""
        router = Router(
            name="multi_agent",
            agents=["agent1", "agent2"],
            model="anthropic/claude-3-sonnet-20241022",
            instruction="Route requests"
        )
        assert router.name == "multi_agent"
        assert router.agents == ["agent1", "agent2"]
        assert router.model == "anthropic/claude-3-sonnet-20241022"
        assert router.instruction == "Route requests"

    def test_chain_creation(self):
        """Test Chain data class creation."""
        chain = Chain(
            name="sequential",
            sequence=["agent1", "agent2"],
            instruction="Process sequentially"
        )
        assert chain.name == "sequential"
        assert chain.sequence == ["agent1", "agent2"]
        assert chain.instruction == "Process sequentially"

    def test_orchestrator_creation(self):
        """Test Orchestrator data class creation."""
        orchestrator = Orchestrator(
            name="complex",
            agents=["agent1", "agent2"],
            model="anthropic/claude-3-sonnet-20241022",
            instruction="Orchestrate agents"
        )
        assert orchestrator.name == "complex"
        assert orchestrator.agents == ["agent1", "agent2"]
        assert orchestrator.model == "anthropic/claude-3-sonnet-20241022"
        assert orchestrator.instruction == "Orchestrate agents"

    def test_agentfile_config_creation(self):
        """Test AgentfileConfig data class creation."""
        config = AgentfileConfig(
            base_image="python:3.11-slim",
            default_model="anthropic/claude-3-sonnet-20241022",
            secrets=["API_KEY"],
            expose_ports=[8080],
            cmd=["python", "app.py"],
            servers={},
            agents={},
        )
        assert config.base_image == "python:3.11-slim"
        assert config.default_model == "anthropic/claude-3-sonnet-20241022"
        assert config.secrets == ["API_KEY"]
        assert config.expose_ports == [8080]
        assert config.cmd == ["python", "app.py"]
        assert config.servers == {}
        assert config.agents == {}


if __name__ == "__main__":
    pytest.main([__file__])
