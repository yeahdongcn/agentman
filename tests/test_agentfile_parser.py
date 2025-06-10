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
        assert self.parser.config.base_image == "yeahdongcn/agentman-base:latest"
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
        assert config.base_image == "yeahdongcn/agentman-base:latest"
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

    def test_parse_content_with_secret_context_arbitrary_name(self):
        """Test parsing secret context with arbitrary names like 'openai'."""
        content = """
FROM yeahdongcn/agentman-base:latest
MODEL generic.qwen3:latest

SECRET openai
API_KEY sk-test123
BASE_URL https://api.openai.com/v1

SECRET anthropic
API_KEY claude-key
"""
        config = self.parser.parse_content(content)

        assert len(config.secrets) == 2

        # Find openai secret context
        openai_secret = None
        anthropic_secret = None
        for secret in config.secrets:
            if isinstance(secret, SecretContext):
                if secret.name == "openai":
                    openai_secret = secret
                elif secret.name == "anthropic":
                    anthropic_secret = secret

        assert openai_secret is not None
        assert anthropic_secret is not None

        # Check openai secret values
        assert openai_secret.values["API_KEY"] == "sk-test123"
        assert openai_secret.values["BASE_URL"] == "https://api.openai.com/v1"

        # Check anthropic secret values
        assert anthropic_secret.values["API_KEY"] == "claude-key"

    def _find_instruction_by_type(self, instructions, instruction_type):
        """Helper function to find instruction by type."""
        return next(
            (
                instruction
                for instruction in instructions
                if instruction.instruction == instruction_type
            ),
            None,
        )

    def test_parse_run_instruction_single_line(self):
        """Test parsing single-line RUN instruction."""
        content = """
FROM python:3.11-slim
RUN apt-get update
"""
        config = self.parser.parse_content(content)

        assert config.base_image == "python:3.11-slim"
        assert len(config.dockerfile_instructions) == 2  # FROM and RUN

        # Find the RUN instruction
        run_instruction = self._find_instruction_by_type(config.dockerfile_instructions, "RUN")

        assert run_instruction is not None
        assert run_instruction.instruction == "RUN"
        assert run_instruction.args == ["apt-get", "update"]
        assert run_instruction.to_dockerfile_line() == "RUN apt-get update"

    def test_parse_run_instruction_multiline(self):
        """Test parsing multi-line RUN instruction with backslash continuation."""
        content = """
FROM python:3.11-slim
RUN apt-get update && apt-get install -y \\
    wget \\
    curl \\
    && rm -rf /var/lib/apt/lists/*
"""
        config = self.parser.parse_content(content)

        assert config.base_image == "python:3.11-slim"
        assert len(config.dockerfile_instructions) == 2  # FROM and RUN

        # Find the RUN instruction
        run_instruction = self._find_instruction_by_type(config.dockerfile_instructions, "RUN")

        assert run_instruction is not None
        assert run_instruction.instruction == "RUN"

        # The multi-line command should be combined into a single line
        expected_command = "apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*"
        actual_command = " ".join(run_instruction.args)
        assert actual_command == expected_command

        # Test the Dockerfile line generation
        expected_dockerfile_line = f"RUN {expected_command}"
        assert run_instruction.to_dockerfile_line() == expected_dockerfile_line

    def test_parse_run_instruction_complex_multiline(self):
        """Test parsing complex multi-line RUN instruction like the one in the Agentfile."""
        content = """
FROM yeahdongcn/agentman-base:latest
RUN apt-get update && apt-get install -y \\
    wget \\
    && rm -rf /var/lib/apt/lists/*
"""
        config = self.parser.parse_content(content)

        assert config.base_image == "yeahdongcn/agentman-base:latest"
        assert len(config.dockerfile_instructions) == 2  # FROM and RUN

        # Find the RUN instruction
        run_instruction = self._find_instruction_by_type(config.dockerfile_instructions, "RUN")

        assert run_instruction is not None
        assert run_instruction.instruction == "RUN"

        # The multi-line command should be combined correctly
        expected_command = "apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*"
        actual_command = " ".join(run_instruction.args)
        assert actual_command == expected_command

    def _validate_instruction(self, instructions, index, expected_instruction, expected_args):
        """Helper function to validate a specific instruction."""
        actual = instructions[index]
        assert actual.instruction == expected_instruction
        if expected_instruction != "CMD":  # CMD has special handling
            assert actual.args == expected_args

    def test_parse_multiple_dockerfile_instructions(self):
        """Test parsing multiple Dockerfile instructions with RUN."""
        content = """
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "app.py"]
"""
        config = self.parser.parse_content(content)

        assert config.base_image == "python:3.11-slim"
        assert config.expose_ports == [8080]
        assert config.cmd == ["python", "app.py"]

        # Check that all Dockerfile instructions are captured in order
        expected_instructions = [
            ("FROM", ["python:3.11-slim"]),
            ("WORKDIR", ["/app"]),
            ("RUN", ["apt-get", "update"]),
            ("COPY", [".", "."]),
            ("RUN", ["pip", "install", "-r", "requirements.txt"]),
            ("EXPOSE", ["8080"]),
            ("CMD", ["python", "app.py"])
        ]

        assert len(config.dockerfile_instructions) == len(expected_instructions)

        # Validate each instruction using helper
        for i, (expected_instruction, expected_args) in enumerate(expected_instructions):
            self._validate_instruction(config.dockerfile_instructions, i, expected_instruction, expected_args)

    def test_parse_content_with_unknown_instruction(self):
        """Test parsing content with an unknown instruction (should be treated as Dockerfile instruction)."""
        content = """
FROM python:3.11-slim
UNKNOWN INSTRUCTION args
"""
        config = self.parser.parse_content(content)

        # Unknown instructions should be treated as Dockerfile instructions
        assert len(config.dockerfile_instructions) == 2  # FROM and UNKNOWN

        unknown_instruction = self._find_instruction_by_type(config.dockerfile_instructions, "UNKNOWN")

        assert unknown_instruction is not None
        assert unknown_instruction.instruction == "UNKNOWN"
        assert unknown_instruction.args == ["INSTRUCTION", "args"]

    def test_parse_content_without_from_instruction(self):
        """Test parsing content without FROM instruction (should still work)."""
        content = """
MODEL anthropic/claude-3-sonnet-20241022
EXPOSE 8080
"""
        config = self.parser.parse_content(content)

        # Should not raise an error - FROM is not strictly required anymore
        assert config.default_model == "anthropic/claude-3-sonnet-20241022"
        assert config.expose_ports == [8080]
        assert len(config.dockerfile_instructions) == 1  # EXPOSE

    def test_parse_content_with_duplicate_secret(self):
        """Test parsing content with duplicate secret definitions."""
        content = """
FROM yeahdongcn/agentman-base:latest

SECRET my_secret
API_KEY sk-test123

SECRET my_secret
BASE_URL https://api.openai.com/v1
"""
        config = self.parser.parse_content(content)

        assert len(config.secrets) == 1  # Only one secret should be created
        secret = config.secrets[0]
        assert secret.name == "my_secret"
        assert secret.values["API_KEY"] == "sk-test123"
        assert secret.values["BASE_URL"] == "https://api.openai.com/v1"


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
