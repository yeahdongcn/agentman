from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class MCPServer:
    """Represents an MCP server configuration."""

    name: str
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    transport: str = "stdio"
    url: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)

    def to_config_dict(self) -> Dict[str, Any]:
        """Convert to fastagent.config.yaml format."""
        config = {"transport": self.transport}

        if self.command:
            config["command"] = self.command
        if self.args:
            config["args"] = self.args
        if self.url:
            config["url"] = self.url
        if self.env:
            config["env"] = self.env

        return config


@dataclass
class Agent:
    """Represents an agent configuration."""

    name: str
    instruction: str = "You are a helpful agent."
    servers: List[str] = field(default_factory=list)
    model: Optional[str] = None
    use_history: bool = True
    human_input: bool = False

    def to_decorator_string(self, default_model: Optional[str] = None) -> str:
        """Generate the @fast.agent decorator string."""
        params = [f'name="{self.name}"', f'instruction="""{self.instruction}"""']

        if self.servers:
            servers_str = "[" + ", ".join(f'"{s}"' for s in self.servers) + "]"
            params.append(f"servers={servers_str}")

        if model_to_use := (self.model or default_model):
            params.append(f'model="{model_to_use}"')

        if not self.use_history:
            params.append("use_history=False")

        if self.human_input:
            params.append("human_input=True")

        return "@fast.agent(\n    " + ",\n    ".join(params) + "\n)"


@dataclass
class Router:
    """Represents a router workflow."""

    name: str
    agents: List[str] = field(default_factory=list)
    model: Optional[str] = None
    instruction: Optional[str] = None

    def to_decorator_string(self, default_model: Optional[str] = None) -> str:
        """Generate the @fast.router decorator string."""
        params = [f'name="{self.name}"']

        if self.agents:
            agents_str = "[" + ", ".join(f'"{a}"' for a in self.agents) + "]"
            params.append(f"agents={agents_str}")

        if model_to_use := (self.model or default_model):
            params.append(f'model="{model_to_use}"')

        if self.instruction:
            params.append(f'instruction="""{self.instruction}"""')

        return "@fast.router(\n    " + ",\n    ".join(params) + "\n)"


@dataclass
class Chain:
    """Represents a chain workflow."""

    name: str
    sequence: List[str] = field(default_factory=list)
    instruction: Optional[str] = None
    cumulative: bool = False
    continue_with_final: bool = True

    def to_decorator_string(self) -> str:
        """Generate the @fast.chain decorator string."""
        params = [f'name="{self.name}"']

        if self.sequence:
            sequence_str = "[" + ", ".join(f'"{a}"' for a in self.sequence) + "]"
            params.append(f"sequence={sequence_str}")

        if self.instruction:
            params.append(f'instruction="""{self.instruction}"""')

        if self.cumulative:
            params.append("cumulative=True")

        if not self.continue_with_final:
            params.append("continue_with_final=False")

        return "@fast.chain(\n    " + ",\n    ".join(params) + "\n)"


@dataclass
class Orchestrator:
    """Represents an orchestrator workflow."""

    name: str
    agents: List[str] = field(default_factory=list)
    model: Optional[str] = None
    instruction: Optional[str] = None
    plan_type: str = "full"
    max_iterations: int = 5
    human_input: bool = False

    def to_decorator_string(self, default_model: Optional[str] = None) -> str:
        """Generate the @fast.orchestrator decorator string."""
        params = []
        params.append(f'name="{self.name}"')

        if self.agents:
            agents_str = "[" + ", ".join(f'"{a}"' for a in self.agents) + "]"
            params.append(f"agents={agents_str}")

        model_to_use = self.model or default_model
        if model_to_use:
            params.append(f'model="{model_to_use}"')

        if self.instruction:
            params.append(f'instruction="""{self.instruction}"""')

        if self.plan_type != "full":
            params.append(f'plan_type="{self.plan_type}"')

        if self.max_iterations != 5:
            params.append(f"max_iterations={self.max_iterations}")

        if self.human_input:
            params.append("human_input=True")

        return "@fast.orchestrator(\n    " + ",\n    ".join(params) + "\n)"


@dataclass
class SecretValue:
    """Represents a secret with an inline value."""

    name: str
    value: str


@dataclass
class SecretContext:
    """Represents a secret context that contains multiple key-value pairs."""

    name: str
    values: Dict[str, str] = field(default_factory=dict)


# Type alias for secrets that can be strings, values, or contexts
SecretType = Union[str, SecretValue, SecretContext]


@dataclass
class AgentfileConfig:
    """Represents the complete Agentfile configuration."""

    base_image: str = "fast-agent:latest"
    default_model: Optional[str] = None
    servers: Dict[str, MCPServer] = field(default_factory=dict)
    agents: Dict[str, Agent] = field(default_factory=dict)
    routers: Dict[str, Router] = field(default_factory=dict)
    chains: Dict[str, Chain] = field(default_factory=dict)
    orchestrators: Dict[str, Orchestrator] = field(default_factory=dict)
    secrets: List[SecretType] = field(default_factory=list)
    expose_ports: List[int] = field(default_factory=list)
    cmd: List[str] = field(default_factory=lambda: ["python", "agent.py"])


class AgentfileParser:
    """Parser for Agentfile format."""

    def __init__(self):
        self.config = AgentfileConfig()
        self.current_context = None
        self.current_item = None

    def parse_file(self, filepath: str) -> AgentfileConfig:
        """Parse an Agentfile and return the configuration."""
        with open(filepath, 'r') as f:
            content = f.read()
        return self.parse_content(content)

    def parse_content(self, content: str) -> AgentfileConfig:
        """Parse Agentfile content and return the configuration."""
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            try:
                self._parse_line(line)
            except Exception as e:
                raise ValueError(f"Error parsing line {line_num}: {line}\n{str(e)}")

        return self.config

    def _parse_line(self, line: str):
        """Parse a single line of the Agentfile."""
        # Split by whitespace but handle quoted strings
        parts = self._split_respecting_quotes(line)
        if not parts:
            return

        instruction = parts[0].upper()

        if instruction == "FROM":
            self._handle_from(parts)
        elif instruction == "MODEL":
            self._handle_model(parts)
        elif instruction == "SERVER":
            self._handle_server(parts)
        elif instruction == "MCP_SERVER":
            self._handle_server(parts)  # Alias for SERVER
        elif instruction == "AGENT":
            self._handle_agent(parts)
        elif instruction == "ROUTER":
            self._handle_router(parts)
        elif instruction == "CHAIN":
            self._handle_chain(parts)
        elif instruction == "ORCHESTRATOR":
            self._handle_orchestrator(parts)
        elif instruction == "SECRET":
            self._handle_secret(parts)
        elif instruction == "EXPOSE":
            self._handle_expose(parts)
        elif instruction == "CMD":
            self._handle_cmd(parts)
        elif instruction in [
            "COMMAND",
            "ARGS",
            "INSTRUCTION",
            "SERVERS",
            "AGENTS",
            "SEQUENCE",
            "TRANSPORT",
            "URL",
            "ENV",
            "USE_HISTORY",
            "HUMAN_INPUT",
            "PLAN_TYPE",
            "MAX_ITERATIONS",
            "CUMULATIVE",
            "API_KEY",
            "BASE_URL",
        ]:
            self._handle_sub_instruction(instruction, parts)
        else:
            raise ValueError(f"Unknown instruction: {instruction}")

    def _split_respecting_quotes(self, line: str) -> List[str]:
        """Split line by whitespace but respect quoted strings."""
        parts = []
        current = ""
        in_quotes = False
        quote_char = None

        i = 0
        while i < len(line):
            char = line[i]

            if not in_quotes and char in ['"', "'"]:
                in_quotes = True
                quote_char = char
                current += char
            elif in_quotes and char == quote_char:
                in_quotes = False
                quote_char = None
                current += char
            elif not in_quotes and char.isspace():
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
            i += 1

        if current:
            parts.append(current)

        return parts

    def _unquote(self, s: str) -> str:
        """Remove quotes from a string if present."""
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ['"', "'"]:
            return s[1:-1]
        return s

    def _handle_from(self, parts: List[str]):
        """Handle FROM instruction."""
        if len(parts) < 2:
            raise ValueError("FROM requires a base image")
        self.config.base_image = self._unquote(parts[1])
        self.current_context = None

    def _handle_model(self, parts: List[str]):
        """Handle MODEL instruction."""
        if len(parts) < 2:
            raise ValueError("MODEL requires a model name")
        self.config.default_model = self._unquote(parts[1])
        self.current_context = None

    def _handle_server(self, parts: List[str]):
        """Handle SERVER instruction."""
        if len(parts) < 2:
            raise ValueError("SERVER requires a server name")
        name = self._unquote(parts[1])
        self.config.servers[name] = MCPServer(name=name)
        self.current_context = "server"
        self.current_item = name

    def _handle_agent(self, parts: List[str]):
        """Handle AGENT instruction."""
        if len(parts) < 2:
            raise ValueError("AGENT requires an agent name")
        name = self._unquote(parts[1])
        self.config.agents[name] = Agent(name=name)
        self.current_context = "agent"
        self.current_item = name

    def _handle_router(self, parts: List[str]):
        """Handle ROUTER instruction."""
        if len(parts) < 2:
            raise ValueError("ROUTER requires a router name")
        name = self._unquote(parts[1])
        self.config.routers[name] = Router(name=name)
        self.current_context = "router"
        self.current_item = name

    def _handle_chain(self, parts: List[str]):
        """Handle CHAIN instruction."""
        if len(parts) < 2:
            raise ValueError("CHAIN requires a chain name")
        name = self._unquote(parts[1])
        self.config.chains[name] = Chain(name=name)
        self.current_context = "chain"
        self.current_item = name

    def _handle_orchestrator(self, parts: List[str]):
        """Handle ORCHESTRATOR instruction."""
        if len(parts) < 2:
            raise ValueError("ORCHESTRATOR requires an orchestrator name")
        name = self._unquote(parts[1])
        self.config.orchestrators[name] = Orchestrator(name=name)
        self.current_context = "orchestrator"
        self.current_item = name

    def _handle_secret(self, parts: List[str]):
        """Handle SECRET instruction.

        Supports multiple formats:
        - SECRET ANTHROPIC_API_KEY (simple reference)
        - SECRET ANTHROPIC_API_KEY <<real_api_key>> (inline value)
        - SECRET GENERIC (context for multiple values)
        """
        if len(parts) < 2:
            raise ValueError("SECRET requires a secret name")

        secret_name = self._unquote(parts[1])

        # Check if it's an inline value: SECRET KEY value
        if len(parts) >= 3:
            value = ' '.join(parts[2:])  # Join all remaining parts as the value
            secret = SecretValue(name=secret_name, value=self._unquote(value))
            self.config.secrets.append(secret)
            self.current_context = None
        # Check if it's a context (no value, will be populated with sub-instructions)
        elif len(parts) == 2:
            # Check if this is meant to be a context by looking ahead or if it's a simple reference
            # For now, treat single names as contexts if they match known patterns
            if secret_name.upper() in ['GENERIC', 'CUSTOM', 'SERVER', 'PROVIDER']:
                secret = SecretContext(name=secret_name)
                self.config.secrets.append(secret)
                self.current_context = "secret"
                self.current_item = secret_name
            else:
                # Simple secret reference - check if it already exists
                if not any(
                    isinstance(s, str) and s == secret_name or hasattr(s, 'name') and s.name == secret_name
                    for s in self.config.secrets
                ):
                    self.config.secrets.append(secret_name)
                self.current_context = None
        else:
            raise ValueError("Invalid SECRET format. Use: SECRET NAME or SECRET NAME value")

    def _handle_secret_sub_instruction(self, instruction: str, parts: List[str]):
        """Handle sub-instructions for SECRET context (key-value pairs)."""
        if not self.current_item:
            raise ValueError("SECRET sub-instruction without active secret context")

        # Find the current secret context
        secret_context = None
        for secret in self.config.secrets:
            if isinstance(secret, SecretContext) and secret.name == self.current_item:
                secret_context = secret
                break

        if not secret_context:
            raise ValueError(f"Secret context {self.current_item} not found")

        # Handle key-value pairs like: API_KEY your_key_here
        if len(parts) >= 2:
            key = parts[0].upper()
            value = ' '.join(parts[1:])
            secret_context.values[key] = self._unquote(value)
        else:
            raise ValueError("SECRET context requires KEY VALUE format")

    def _handle_expose(self, parts: List[str]):
        """Handle EXPOSE instruction."""
        if len(parts) < 2:
            raise ValueError("EXPOSE requires a port number")
        try:
            port = int(parts[1])
            if port not in self.config.expose_ports:
                self.config.expose_ports.append(port)
        except ValueError:
            raise ValueError(f"Invalid port number: {parts[1]}")
        self.current_context = None

    def _handle_cmd(self, parts: List[str]):
        """Handle CMD instruction."""
        if len(parts) < 2:
            raise ValueError("CMD requires at least one argument")
        # Handle both array format and simple format
        if parts[1].startswith('[') and parts[-1].endswith(']'):
            # Array format: CMD ["python", "agent.py"]
            cmd_str = ' '.join(parts[1:])
            # Simple JSON-like parsing
            cmd_str = cmd_str.strip('[]')
            self.config.cmd = [self._unquote(item.strip()) for item in cmd_str.split(',')]
        else:
            # Simple format: CMD python agent.py
            self.config.cmd = [self._unquote(part) for part in parts[1:]]
        self.current_context = None

    def _handle_sub_instruction(self, instruction: str, parts: List[str]):
        """Handle sub-instructions that modify the current context item."""
        if not self.current_context:
            # Special case: if we're not in a context but this looks like a key-value pair
            # for a secret context, try to handle it
            if self.current_item and any(
                isinstance(s, SecretContext) and s.name == self.current_item for s in self.config.secrets
            ):
                self.current_context = "secret"
                self._handle_secret_sub_instruction(instruction, parts)
                return
            else:
                raise ValueError(f"{instruction} can only be used within a context (SERVER, AGENT, etc.)")

        if self.current_context == "server":
            self._handle_server_sub_instruction(instruction, parts)
        elif self.current_context == "agent":
            self._handle_agent_sub_instruction(instruction, parts)
        elif self.current_context == "router":
            self._handle_router_sub_instruction(instruction, parts)
        elif self.current_context == "chain":
            self._handle_chain_sub_instruction(instruction, parts)
        elif self.current_context == "orchestrator":
            self._handle_orchestrator_sub_instruction(instruction, parts)
        elif self.current_context == "secret":
            self._handle_secret_sub_instruction(instruction, parts)

    def _handle_server_sub_instruction(self, instruction: str, parts: List[str]):
        """Handle sub-instructions for SERVER context."""
        server = self.config.servers[self.current_item]

        if instruction == "COMMAND":
            if len(parts) < 2:
                raise ValueError("COMMAND requires a command")
            server.command = self._unquote(parts[1])
        elif instruction == "ARGS":
            if len(parts) < 2:
                raise ValueError("ARGS requires at least one argument")
            server.args = [self._unquote(part) for part in parts[1:]]
        elif instruction == "TRANSPORT":
            if len(parts) < 2:
                raise ValueError("TRANSPORT requires a transport type")
            transport = self._unquote(parts[1])
            if transport not in ["stdio", "sse", "http"]:
                raise ValueError(f"Invalid transport type: {transport}")
            server.transport = transport
        elif instruction == "URL":
            if len(parts) < 2:
                raise ValueError("URL requires a URL")
            server.url = self._unquote(parts[1])
        elif instruction == "ENV":
            if len(parts) < 3:
                raise ValueError("ENV requires KEY VALUE")
            key = self._unquote(parts[1])
            value = self._unquote(parts[2])
            server.env[key] = value

    def _handle_agent_sub_instruction(self, instruction: str, parts: List[str]):
        """Handle sub-instructions for AGENT context."""
        agent = self.config.agents[self.current_item]

        if instruction == "INSTRUCTION":
            if len(parts) < 2:
                raise ValueError("INSTRUCTION requires instruction text")
            agent.instruction = self._unquote(' '.join(parts[1:]))
        elif instruction == "SERVERS":
            if len(parts) < 2:
                raise ValueError("SERVERS requires at least one server name")
            agent.servers = [self._unquote(part) for part in parts[1:]]
        elif instruction == "MODEL":
            if len(parts) < 2:
                raise ValueError("MODEL requires a model name")
            agent.model = self._unquote(parts[1])
        elif instruction == "USE_HISTORY":
            if len(parts) < 2:
                raise ValueError("USE_HISTORY requires true/false")
            agent.use_history = self._unquote(parts[1]).lower() in ['true', '1', 'yes']
        elif instruction == "HUMAN_INPUT":
            if len(parts) < 2:
                raise ValueError("HUMAN_INPUT requires true/false")
            agent.human_input = self._unquote(parts[1]).lower() in ['true', '1', 'yes']

    def _handle_router_sub_instruction(self, instruction: str, parts: List[str]):
        """Handle sub-instructions for ROUTER context."""
        router = self.config.routers[self.current_item]

        if instruction == "AGENTS":
            if len(parts) < 2:
                raise ValueError("AGENTS requires at least one agent name")
            router.agents = [self._unquote(part) for part in parts[1:]]
        elif instruction == "MODEL":
            if len(parts) < 2:
                raise ValueError("MODEL requires a model name")
            router.model = self._unquote(parts[1])
        elif instruction == "INSTRUCTION":
            if len(parts) < 2:
                raise ValueError("INSTRUCTION requires instruction text")
            router.instruction = self._unquote(' '.join(parts[1:]))

    def _handle_chain_sub_instruction(self, instruction: str, parts: List[str]):
        """Handle sub-instructions for CHAIN context."""
        chain = self.config.chains[self.current_item]

        if instruction == "SEQUENCE":
            if len(parts) < 2:
                raise ValueError("SEQUENCE requires at least one agent name")
            chain.sequence = [self._unquote(part) for part in parts[1:]]
        elif instruction == "INSTRUCTION":
            if len(parts) < 2:
                raise ValueError("INSTRUCTION requires instruction text")
            chain.instruction = self._unquote(' '.join(parts[1:]))
        elif instruction == "CUMULATIVE":
            if len(parts) < 2:
                raise ValueError("CUMULATIVE requires true/false")
            chain.cumulative = self._unquote(parts[1]).lower() in ['true', '1', 'yes']
        elif instruction == "CONTINUE_WITH_FINAL":
            if len(parts) < 2:
                raise ValueError("CONTINUE_WITH_FINAL requires true/false")
            chain.continue_with_final = self._unquote(parts[1]).lower() in ['true', '1', 'yes']

    def _handle_orchestrator_sub_instruction(self, instruction: str, parts: List[str]):
        """Handle sub-instructions for ORCHESTRATOR context."""
        orchestrator = self.config.orchestrators[self.current_item]

        if instruction == "AGENTS":
            if len(parts) < 2:
                raise ValueError("AGENTS requires at least one agent name")
            orchestrator.agents = [self._unquote(part) for part in parts[1:]]
        elif instruction == "MODEL":
            if len(parts) < 2:
                raise ValueError("MODEL requires a model name")
            orchestrator.model = self._unquote(parts[1])
        elif instruction == "INSTRUCTION":
            if len(parts) < 2:
                raise ValueError("INSTRUCTION requires instruction text")
            orchestrator.instruction = self._unquote(' '.join(parts[1:]))
        elif instruction == "PLAN_TYPE":
            if len(parts) < 2:
                raise ValueError("PLAN_TYPE requires a plan type")
            plan_type = self._unquote(parts[1])
            if plan_type not in ["full", "iterative"]:
                raise ValueError(f"Invalid plan type: {plan_type}")
            orchestrator.plan_type = plan_type
        elif instruction == "MAX_ITERATIONS":
            if len(parts) < 2:
                raise ValueError("MAX_ITERATIONS requires a number")
            try:
                orchestrator.max_iterations = int(parts[1])
            except ValueError:
                raise ValueError(f"Invalid number for MAX_ITERATIONS: {parts[1]}")
        elif instruction == "HUMAN_INPUT":
            if len(parts) < 2:
                raise ValueError("HUMAN_INPUT requires true/false")
            orchestrator.human_input = self._unquote(parts[1]).lower() in ['true', '1', 'yes']
