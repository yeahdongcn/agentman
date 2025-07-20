"""YAML parser module for parsing Agentfile configurations in YAML format."""

from pathlib import Path
from typing import Any, Dict, List, Union

import yaml

from agentman.agentfile_parser import (
    Agent,
    AgentfileConfig,
    AgentfileParser,
    Chain,
    DockerfileInstruction,
    MCPServer,
    Orchestrator,
    OutputFormat,
    Router,
    SecretContext,
    SecretValue,
    expand_env_vars,
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

        # Parse agents configuration - convert single agent to agents array
        agents_to_parse = []

        if 'agent' in data:
            # Single agent configuration - treat as array with one agent
            agents_to_parse.append(data['agent'])

        if 'agents' in data:
            # Multiple agents configuration
            agents_to_parse.extend(data['agents'])

        # Parse all agents
        self._parse_agents(agents_to_parse)

        # Parse routers, chains, and orchestrators
        self._parse_routers(data.get('routers', []))
        self._parse_chains(data.get('chains', []))
        self._parse_orchestrators(data.get('orchestrators', []))

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
                    # Expand environment variables in values
                    expanded_env = {}
                    for key, value in env.items():
                        expanded_env[key] = expand_env_vars(value)
                    server.env = expanded_env
                else:
                    raise ValueError("MCP server 'env' must be a dictionary")

            self.config.servers[name] = server

    def _parse_agents(self, agents_config: List[Dict[str, Any]]):
        """Parse agents configuration."""
        for agent_config in agents_config:
            self._parse_agent(agent_config)

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

        if 'output_format' in agent_config:
            output_format_config = agent_config['output_format']
            if not isinstance(output_format_config, dict):
                raise ValueError("Agent 'output_format' must be an object")

            if 'type' not in output_format_config:
                raise ValueError("Agent 'output_format' must have a 'type' field")

            format_type = output_format_config['type']

            if format_type == 'json_schema':
                if 'schema' not in output_format_config:
                    raise ValueError("Agent 'output_format' with type 'json_schema' must have a 'schema' field")
                schema = output_format_config['schema']
                if not isinstance(schema, dict):
                    raise ValueError("Agent 'output_format' schema must be an object")
                agent.output_format = OutputFormat(type='json_schema', schema=schema)
            elif format_type == 'schema_file':
                if 'file' not in output_format_config:
                    raise ValueError("Agent 'output_format' with type 'schema_file' must have a 'file' field")
                file_path = output_format_config['file']
                if not isinstance(file_path, str):
                    raise ValueError("Agent 'output_format' file must be a string")
                if not file_path.endswith(('.json', '.yaml', '.yml')):
                    raise ValueError("Agent 'output_format' file must reference a .json, .yaml, or .yml file")
                agent.output_format = OutputFormat(type='schema_file', file=file_path)
            else:
                raise ValueError(f"Invalid output_format type: {format_type}. Supported: json_schema, schema_file")

        self.config.agents[name] = agent

    def _parse_routers(self, routers_config: List[Dict[str, Any]]):
        """Parse routers configuration."""
        for router_config in routers_config:
            if 'name' not in router_config:
                raise ValueError("Router must have a 'name' field")

            name = router_config['name']
            router = Router(name=name)

            if 'agents' in router_config:
                agents = router_config['agents']
                if isinstance(agents, list):
                    router.agents = agents
                else:
                    raise ValueError("Router 'agents' must be a list")

            if 'model' in router_config:
                router.model = router_config['model']

            if 'instruction' in router_config:
                router.instruction = router_config['instruction']

            if 'default' in router_config:
                router.default = bool(router_config['default'])

            self.config.routers[name] = router

    def _parse_chains(self, chains_config: List[Dict[str, Any]]):
        """Parse chains configuration."""
        for chain_config in chains_config:
            if 'name' not in chain_config:
                raise ValueError("Chain must have a 'name' field")

            name = chain_config['name']
            chain = Chain(name=name)

            if 'sequence' in chain_config:
                sequence = chain_config['sequence']
                if isinstance(sequence, list):
                    chain.sequence = sequence
                else:
                    raise ValueError("Chain 'sequence' must be a list")

            if 'instruction' in chain_config:
                chain.instruction = chain_config['instruction']

            if 'cumulative' in chain_config:
                chain.cumulative = bool(chain_config['cumulative'])

            if 'continue_with_final' in chain_config:
                chain.continue_with_final = bool(chain_config['continue_with_final'])

            if 'default' in chain_config:
                chain.default = bool(chain_config['default'])

            self.config.chains[name] = chain

    def _parse_orchestrators(self, orchestrators_config: List[Dict[str, Any]]):
        """Parse orchestrators configuration."""
        for orchestrator_config in orchestrators_config:
            if 'name' not in orchestrator_config:
                raise ValueError("Orchestrator must have a 'name' field")

            name = orchestrator_config['name']
            orchestrator = Orchestrator(name=name)

            if 'agents' in orchestrator_config:
                agents = orchestrator_config['agents']
                if isinstance(agents, list):
                    orchestrator.agents = agents
                else:
                    raise ValueError("Orchestrator 'agents' must be a list")

            if 'model' in orchestrator_config:
                orchestrator.model = orchestrator_config['model']

            if 'instruction' in orchestrator_config:
                orchestrator.instruction = orchestrator_config['instruction']

            if 'plan_type' in orchestrator_config:
                plan_type = orchestrator_config['plan_type']
                if plan_type not in ["full", "iterative"]:
                    raise ValueError(f"Invalid plan type: {plan_type}")
                orchestrator.plan_type = plan_type

            if 'plan_iterations' in orchestrator_config:
                orchestrator.plan_iterations = int(orchestrator_config['plan_iterations'])

            if 'human_input' in orchestrator_config:
                orchestrator.human_input = bool(orchestrator_config['human_input'])

            if 'default' in orchestrator_config:
                orchestrator.default = bool(orchestrator_config['default'])

            self.config.orchestrators[name] = orchestrator

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
                    expanded_value = expand_env_vars(secret_config['value'])
                    secret = SecretValue(name=name, value=expanded_value)
                    self.config.secrets.append(secret)
                elif 'values' in secret_config:
                    # Secret context with multiple values
                    values = secret_config['values']
                    if isinstance(values, dict):
                        # Expand environment variables in values
                        expanded_values = {}
                        for key, value in values.items():
                            expanded_values[key] = expand_env_vars(value)
                        secret = SecretContext(name=name, values=expanded_values)
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
    if detect_yaml_format(filepath):
        parser = AgentfileYamlParser()
        return parser.parse_file(filepath)

    parser = AgentfileParser()
    return parser.parse_file(filepath)
