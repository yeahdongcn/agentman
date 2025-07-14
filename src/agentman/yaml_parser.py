"""YAML parser module for parsing Agentfile configurations in YAML format."""

import yaml
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from agentman.agentfile_parser import (
    AgentfileConfig,
    MCPServer,
    Agent,
    Router,
    Chain,
    Orchestrator,
    SecretValue,
    SecretContext,
    SecretType,
    DockerfileInstruction,
)


class AgentfileYamlParser:
    """Parser for YAML format Agentfile configurations."""

    def __init__(self):
        self.config = AgentfileConfig()

    def parse_file(self, filepath: str) -> AgentfileConfig:
        """Parse a YAML Agentfile and return the configuration."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_content(content)

    def parse_content(self, content: str) -> AgentfileConfig:
        """Parse YAML Agentfile content and return the configuration."""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}") from e

        if not data:
            return self.config

        # Validate API version and kind
        api_version = data.get('apiVersion', 'v1')
        kind = data.get('kind', 'Agent')
        
        if api_version != 'v1':
            raise ValueError(f"Unsupported API version: {api_version}. Only 'v1' is supported.")
        
        if kind != 'Agent':
            raise ValueError(f"Unsupported kind: {kind}. Only 'Agent' is supported.")

        # Parse base configuration
        self._parse_base(data.get('base', {}))
        
        # Parse MCP servers
        self._parse_mcp_servers(data.get('mcp_servers', []))
        
        # Parse agent configuration
        self._parse_agent(data.get('agent', {}))
        
        # Parse command
        self._parse_command(data.get('command', []))
        
        # Parse secrets if they exist
        self._parse_secrets(data.get('secrets', []))
        
        # Parse expose ports if they exist
        self._parse_expose_ports(data.get('expose', []))
        
        # Parse additional dockerfile instructions if they exist
        self._parse_dockerfile_instructions(data.get('dockerfile', []))

        return self.config

    def _parse_base(self, base_config: Dict[str, Any]):
        """Parse base configuration."""
        if 'image' in base_config:
            self.config.base_image = base_config['image']
        
        if 'model' in base_config:
            self.config.default_model = base_config['model']
        
        if 'framework' in base_config:
            framework = base_config['framework'].lower()
            if framework not in ['fast-agent', 'agno']:
                raise ValueError(f"Unsupported framework: {framework}. Supported: fast-agent, agno")
            self.config.framework = framework

    def _parse_mcp_servers(self, servers_config: List[Dict[str, Any]]):
        """Parse MCP servers configuration."""
        for server_config in servers_config:
            if 'name' not in server_config:
                raise ValueError("MCP server must have a 'name' field")
            
            name = server_config['name']
            server = MCPServer(name=name)
            
            if 'command' in server_config:
                server.command = server_config['command']
            
            if 'args' in server_config:
                args = server_config['args']
                if isinstance(args, list):
                    server.args = args
                else:
                    raise ValueError("MCP server 'args' must be a list")
            
            if 'transport' in server_config:
                transport = server_config['transport']
                if transport not in ['stdio', 'sse', 'http']:
                    raise ValueError(f"Invalid transport type: {transport}")
                server.transport = transport
            
            if 'url' in server_config:
                server.url = server_config['url']
            
            if 'env' in server_config:
                env = server_config['env']
                if isinstance(env, dict):
                    server.env = env
                else:
                    raise ValueError("MCP server 'env' must be a dictionary")
            
            self.config.servers[name] = server

    def _parse_agent(self, agent_config: Dict[str, Any]):
        """Parse agent configuration."""
        if not agent_config:
            return
        
        if 'name' not in agent_config:
            raise ValueError("Agent must have a 'name' field")
        
        name = agent_config['name']
        agent = Agent(name=name)
        
        if 'instruction' in agent_config:
            agent.instruction = agent_config['instruction']
        
        if 'servers' in agent_config:
            servers = agent_config['servers']
            if isinstance(servers, list):
                agent.servers = servers
            else:
                raise ValueError("Agent 'servers' must be a list")
        
        if 'model' in agent_config:
            agent.model = agent_config['model']
        
        if 'use_history' in agent_config:
            agent.use_history = bool(agent_config['use_history'])
        
        if 'human_input' in agent_config:
            agent.human_input = bool(agent_config['human_input'])
        
        if 'default' in agent_config:
            agent.default = bool(agent_config['default'])
        
        self.config.agents[name] = agent

    def _parse_command(self, command_config: List[str]):
        """Parse command configuration."""
        if command_config:
            if isinstance(command_config, list):
                self.config.cmd = command_config
            else:
                raise ValueError("Command must be a list")

    def _parse_secrets(self, secrets_config: List[Union[str, Dict[str, Any]]]):
        """Parse secrets configuration."""
        for secret_config in secrets_config:
            if isinstance(secret_config, str):
                # Simple secret reference
                self.config.secrets.append(secret_config)
            elif isinstance(secret_config, dict):
                if 'name' not in secret_config:
                    raise ValueError("Secret must have a 'name' field")
                
                name = secret_config['name']
                
                if 'value' in secret_config:
                    # Inline secret value
                    secret = SecretValue(name=name, value=secret_config['value'])
                    self.config.secrets.append(secret)
                elif 'values' in secret_config:
                    # Secret context with multiple values
                    values = secret_config['values']
                    if isinstance(values, dict):
                        secret = SecretContext(name=name, values=values)
                        self.config.secrets.append(secret)
                    else:
                        raise ValueError("Secret 'values' must be a dictionary")
                else:
                    # Simple secret reference
                    self.config.secrets.append(name)
            else:
                raise ValueError("Secret must be a string or dictionary")

    def _parse_expose_ports(self, expose_config: List[int]):
        """Parse expose ports configuration."""
        for port in expose_config:
            if isinstance(port, int):
                if port not in self.config.expose_ports:
                    self.config.expose_ports.append(port)
            else:
                raise ValueError("Expose port must be an integer")

    def _parse_dockerfile_instructions(self, dockerfile_config: List[Dict[str, Any]]):
        """Parse additional dockerfile instructions."""
        for instruction_config in dockerfile_config:
            if 'instruction' not in instruction_config or 'args' not in instruction_config:
                raise ValueError("Dockerfile instruction must have 'instruction' and 'args' fields")
            
            instruction = instruction_config['instruction'].upper()
            args = instruction_config['args']
            
            if isinstance(args, list):
                dockerfile_instruction = DockerfileInstruction(instruction=instruction, args=args)
                self.config.dockerfile_instructions.append(dockerfile_instruction)
            else:
                raise ValueError("Dockerfile instruction 'args' must be a list")


def detect_yaml_format(filepath: str) -> bool:
    """Detect if a file is in YAML format based on extension or content."""
    path = Path(filepath)
    
    # Check file extension
    if path.suffix.lower() in ['.yml', '.yaml']:
        return True
    
    # Check content for YAML structure
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return False
            
            # Try to parse as YAML
            data = yaml.safe_load(content)
            
            # Check if it has YAML Agentfile structure
            if isinstance(data, dict) and 'apiVersion' in data and 'kind' in data:
                return True
            
            return False
    except (yaml.YAMLError, IOError, UnicodeDecodeError):
        return False


def parse_agentfile(filepath: str) -> AgentfileConfig:
    """Parse an Agentfile in either YAML or Dockerfile format."""
    from agentman.agentfile_parser import AgentfileParser
    
    if detect_yaml_format(filepath):
        parser = AgentfileYamlParser()
        return parser.parse_file(filepath)
    else:
        parser = AgentfileParser()
        return parser.parse_file(filepath)