"""
Unit tests for yaml_parser module.

Tests cover all aspects of the AgentfileYamlParser including:
- Basic YAML parsing functionality
- Schema validation
- Format detection
- Error handling
- All configuration sections (base, mcp_servers, agent, command, secrets, etc.)
"""

import pytest
import tempfile
import os
from pathlib import Path

from agentman.yaml_parser import (
    AgentfileYamlParser,
    detect_yaml_format,
    parse_agentfile,
)
from agentman.agentfile_parser import (
    AgentfileConfig,
    MCPServer,
    Agent,
    SecretValue,
    SecretContext,
)


class TestAgentfileYamlParser:
    """Test suite for AgentfileYamlParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AgentfileYamlParser()

    def test_init(self):
        """Test parser initialization."""
        assert self.parser.config is not None
        assert isinstance(self.parser.config, AgentfileConfig)
        assert self.parser.config.base_image == "yeahdongcn/agentman-base:latest"
        assert self.parser.config.secrets == []
        assert self.parser.config.servers == {}
        assert self.parser.config.agents == {}

    def test_parse_content_basic(self):
        """Test parsing basic YAML Agentfile content."""
        content = """
apiVersion: v1
kind: Agent

base:
  image: python:3.11-slim
  model: gpt-4
  framework: fast-agent

command: [python, agent.py]

expose:
  - 8080
"""
        config = self.parser.parse_content(content)

        assert config.base_image == "python:3.11-slim"
        assert config.default_model == "gpt-4"
        assert config.framework == "fast-agent"
        assert config.cmd == ["python", "agent.py"]
        assert config.expose_ports == [8080]

    def test_parse_content_with_mcp_servers(self):
        """Test parsing YAML with MCP servers."""
        content = """
apiVersion: v1
kind: Agent

mcp_servers:
  - name: filesystem
    command: uv
    args: [tool, run, mcp-server-filesystem, /tmp]
    transport: stdio
    env:
      PATH: /usr/local/bin
      DEBUG: "true"
  - name: web_search
    command: uvx
    args: [mcp-server-fetch]
    transport: stdio

agent:
  name: assistant
  servers: [filesystem, web_search]
"""
        config = self.parser.parse_content(content)

        assert len(config.servers) == 2
        assert "filesystem" in config.servers
        assert "web_search" in config.servers
        
        fs_server = config.servers["filesystem"]
        assert fs_server.name == "filesystem"
        assert fs_server.command == "uv"
        assert fs_server.args == ["tool", "run", "mcp-server-filesystem", "/tmp"]
        assert fs_server.transport == "stdio"
        assert fs_server.env == {"PATH": "/usr/local/bin", "DEBUG": "true"}

        web_server = config.servers["web_search"]
        assert web_server.name == "web_search"
        assert web_server.command == "uvx"
        assert web_server.args == ["mcp-server-fetch"]
        assert web_server.transport == "stdio"

    def test_parse_content_with_agent(self):
        """Test parsing YAML with agent configuration."""
        content = """
apiVersion: v1
kind: Agent

agent:
  name: gmail_assistant
  instruction: |
    You are a helpful assistant that can manage Gmail.
    Use the Gmail API to read, send, and organize emails.
  servers: [gmail, fetch]
  model: gpt-4
  use_history: true
  human_input: false
  default: true
"""
        config = self.parser.parse_content(content)

        assert len(config.agents) == 1
        assert "gmail_assistant" in config.agents
        
        agent = config.agents["gmail_assistant"]
        assert agent.name == "gmail_assistant"
        assert "You are a helpful assistant that can manage Gmail." in agent.instruction
        assert agent.servers == ["gmail", "fetch"]
        assert agent.model == "gpt-4"
        assert agent.use_history is True
        assert agent.human_input is False
        assert agent.default is True

    def test_parse_content_with_secrets(self):
        """Test parsing YAML with various secret formats."""
        content = """
apiVersion: v1
kind: Agent

secrets:
  - SIMPLE_SECRET
  - name: INLINE_SECRET
    value: secret-value-123
  - name: OPENAI_CONFIG
    values:
      API_KEY: sk-test123
      BASE_URL: https://api.openai.com/v1
"""
        config = self.parser.parse_content(content)

        assert len(config.secrets) == 3
        
        # Simple secret reference
        assert config.secrets[0] == "SIMPLE_SECRET"
        
        # Inline secret value
        inline_secret = config.secrets[1]
        assert isinstance(inline_secret, SecretValue)
        assert inline_secret.name == "INLINE_SECRET"
        assert inline_secret.value == "secret-value-123"
        
        # Secret context
        context_secret = config.secrets[2]
        assert isinstance(context_secret, SecretContext)
        assert context_secret.name == "OPENAI_CONFIG"
        assert context_secret.values == {
            "API_KEY": "sk-test123",
            "BASE_URL": "https://api.openai.com/v1"
        }

    def test_parse_content_with_dockerfile_instructions(self):
        """Test parsing YAML with additional dockerfile instructions."""
        content = """
apiVersion: v1
kind: Agent

dockerfile:
  - instruction: RUN
    args: [apt-get, update]
  - instruction: ENV
    args: [PYTHONPATH=/app]
  - instruction: COPY
    args: [., /app]
"""
        config = self.parser.parse_content(content)

        assert len(config.dockerfile_instructions) == 3
        
        run_instruction = config.dockerfile_instructions[0]
        assert run_instruction.instruction == "RUN"
        assert run_instruction.args == ["apt-get", "update"]
        
        env_instruction = config.dockerfile_instructions[1]
        assert env_instruction.instruction == "ENV"
        assert env_instruction.args == ["PYTHONPATH=/app"]
        
        copy_instruction = config.dockerfile_instructions[2]
        assert copy_instruction.instruction == "COPY"
        assert copy_instruction.args == [".", "/app"]

    def test_parse_file(self):
        """Test parsing YAML Agentfile from file."""
        content = """
apiVersion: v1
kind: Agent

base:
  image: python:3.11-slim
  model: gpt-4

agent:
  name: test_agent
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(content)
            f.flush()

            try:
                config = self.parser.parse_file(f.name)
                assert config.base_image == "python:3.11-slim"
                assert config.default_model == "gpt-4"
                assert "test_agent" in config.agents
            finally:
                os.unlink(f.name)

    def test_parse_file_not_exists(self):
        """Test parsing from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file("/non/existent/file.yml")

    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML raises error."""
        content = """
apiVersion: v1
kind: Agent
invalid_yaml: [unclosed list
"""
        with pytest.raises(ValueError, match="Invalid YAML format"):
            self.parser.parse_content(content)

    def test_parse_invalid_api_version(self):
        """Test parsing with invalid API version raises error."""
        content = """
apiVersion: v2
kind: Agent
"""
        with pytest.raises(ValueError, match="Unsupported API version"):
            self.parser.parse_content(content)

    def test_parse_invalid_kind(self):
        """Test parsing with invalid kind raises error."""
        content = """
apiVersion: v1
kind: InvalidKind
"""
        with pytest.raises(ValueError, match="Unsupported kind"):
            self.parser.parse_content(content)

    def test_parse_invalid_framework(self):
        """Test parsing with invalid framework raises error."""
        content = """
apiVersion: v1
kind: Agent

base:
  framework: invalid-framework
"""
        with pytest.raises(ValueError, match="Unsupported framework"):
            self.parser.parse_content(content)

    def test_parse_missing_agent_name(self):
        """Test parsing with missing agent name raises error."""
        content = """
apiVersion: v1
kind: Agent

agent:
  instruction: Test instruction
"""
        with pytest.raises(ValueError, match="Agent must have a 'name' field"):
            self.parser.parse_content(content)

    def test_parse_missing_server_name(self):
        """Test parsing with missing server name raises error."""
        content = """
apiVersion: v1
kind: Agent

mcp_servers:
  - command: test
"""
        with pytest.raises(ValueError, match="MCP server must have a 'name' field"):
            self.parser.parse_content(content)

    def test_empty_yaml_file(self):
        """Test parsing empty YAML file."""
        config = self.parser.parse_content("")
        assert config.base_image == "yeahdongcn/agentman-base:latest"
        assert len(config.secrets) == 0
        assert len(config.servers) == 0
        assert len(config.agents) == 0

    def test_parse_complete_example(self):
        """Test parsing a complete YAML Agentfile example."""
        content = """
apiVersion: v1
kind: Agent

base:
  image: ghcr.io/o3-cloud/pai/base:latest
  model: gpt-4.1
  framework: fast-agent

mcp_servers:
  - name: gmail
    command: npx
    args: [-y, "@gongrzhe/server-gmail-autoauth-mcp"]
    transport: stdio
    
  - name: fetch
    command: uvx
    args: [mcp-server-fetch]
    transport: stdio

agent:
  name: gmail_actions
  instruction: |
    You are a productivity assistant with access to my Gmail inbox.
    Using my personal context, perform the following tasks:
    1. Only analyze and classify all emails currently in my inbox.
    2. Assign appropriate labels to each email based on inferred categories.
    3. Archive each email to keep my inbox clean.
  servers: [gmail, fetch]
  use_history: true
  human_input: false
  default: true

command: [python, agent.py, -p, prompt.txt, --agent, gmail_actions]

secrets:
  - GMAIL_API_KEY
  - name: OPENAI_CONFIG
    values:
      API_KEY: your-openai-api-key
      BASE_URL: https://api.openai.com/v1

expose:
  - 8080

dockerfile:
  - instruction: RUN
    args: [apt-get, update, "&&", apt-get, install, -y, curl]
  - instruction: ENV
    args: [PYTHONPATH=/app]
"""
        config = self.parser.parse_content(content)

        # Verify base configuration
        assert config.base_image == "ghcr.io/o3-cloud/pai/base:latest"
        assert config.default_model == "gpt-4.1"
        assert config.framework == "fast-agent"

        # Verify MCP servers
        assert len(config.servers) == 2
        assert "gmail" in config.servers
        assert "fetch" in config.servers

        # Verify agent
        assert len(config.agents) == 1
        assert "gmail_actions" in config.agents
        agent = config.agents["gmail_actions"]
        assert agent.default is True
        assert agent.servers == ["gmail", "fetch"]

        # Verify command
        assert config.cmd == ["python", "agent.py", "-p", "prompt.txt", "--agent", "gmail_actions"]

        # Verify secrets
        assert len(config.secrets) == 2
        assert config.secrets[0] == "GMAIL_API_KEY"

        # Verify expose
        assert config.expose_ports == [8080]

        # Verify dockerfile instructions
        assert len(config.dockerfile_instructions) == 2


class TestFormatDetection:
    """Test suite for format detection functionality."""

    def test_detect_yaml_format_by_extension(self):
        """Test detecting YAML format by file extension."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("apiVersion: v1\nkind: Agent\n")
            f.flush()

            try:
                assert detect_yaml_format(f.name) is True
            finally:
                os.unlink(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("apiVersion: v1\nkind: Agent\n")
            f.flush()

            try:
                assert detect_yaml_format(f.name) is True
            finally:
                os.unlink(f.name)

    def test_detect_yaml_format_by_content(self):
        """Test detecting YAML format by content structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("apiVersion: v1\nkind: Agent\n")
            f.flush()

            try:
                assert detect_yaml_format(f.name) is True
            finally:
                os.unlink(f.name)

    def test_detect_dockerfile_format(self):
        """Test detecting Dockerfile format."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("FROM python:3.11-slim\nMODEL gpt-4\n")
            f.flush()

            try:
                assert detect_yaml_format(f.name) is False
            finally:
                os.unlink(f.name)

    def test_detect_empty_file(self):
        """Test detecting format for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("")
            f.flush()

            try:
                assert detect_yaml_format(f.name) is False
            finally:
                os.unlink(f.name)

    def test_parse_agentfile_auto_detect(self):
        """Test parse_agentfile with auto-detection."""
        # Test YAML format
        yaml_content = """
apiVersion: v1
kind: Agent

base:
  image: python:3.11-slim
  model: gpt-4

agent:
  name: test_agent
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                config = parse_agentfile(f.name)
                assert config.base_image == "python:3.11-slim"
                assert config.default_model == "gpt-4"
                assert "test_agent" in config.agents
            finally:
                os.unlink(f.name)

        # Test Dockerfile format
        dockerfile_content = """
FROM python:3.11-slim
MODEL gpt-4

AGENT test_agent
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(dockerfile_content)
            f.flush()

            try:
                config = parse_agentfile(f.name)
                assert config.base_image == "python:3.11-slim"
                assert config.default_model == "gpt-4"
                assert "test_agent" in config.agents
            finally:
                os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__])