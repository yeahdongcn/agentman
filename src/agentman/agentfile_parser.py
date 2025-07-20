"""Agentfile parser module for parsing Agentfile configurations."""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


def expand_env_vars(value: str) -> str:
    """
    Expand environment variables in a string.

    Supports both ${VAR} and $VAR syntax.
    If environment variable is not found, returns the original placeholder.

    Args:
        value: String that may contain environment variable references

    Returns:
        String with environment variables expanded
    """
    if not isinstance(value, str):
        return value

    # Pattern to match ${VAR} or $VAR (where VAR is alphanumeric + underscore)
    pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)'

    def replace_var(match):
        # Get the variable name from either group
        var_name = match.group(1) or match.group(2)
        env_value = os.environ.get(var_name)
        if env_value is not None:
            return env_value
            # Return the original placeholder if env var not found
        return match.group(0)

    return re.sub(pattern, replace_var, value)


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
class OutputFormat:
    """Represents output format configuration for an agent."""

    type: str  # "json_schema" or "schema_file"
    schema: Optional[Dict[str, Any]] = None  # For inline JSON Schema as YAML
    file: Optional[str] = None  # For external schema file reference


@dataclass
class Agent:
    """Represents an agent configuration."""

    name: str
    instruction: str = "You are a helpful agent."
    servers: List[str] = field(default_factory=list)
    model: Optional[str] = None
    use_history: bool = True
    human_input: bool = False
    default: bool = False
    output_format: Optional[OutputFormat] = None

    def to_decorator_string(self, default_model: Optional[str] = None, base_path: Optional[str] = None) -> str:
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

        if self.default:
            params.append("default=True")

        # Add response_format if output_format is specified
        if self.output_format:
            request_params = self._generate_request_params(base_path)
            if request_params:
                params.append(f"request_params={request_params}")

        return "@fast.agent(\n    " + ",\n    ".join(params) + "\n)"

    def _generate_request_params(self, base_path: Optional[str] = None) -> Optional[str]:
        """Generate RequestParams with response_format from output_format."""
        if not self.output_format:
            return None

        if self.output_format.type == "json_schema" and self.output_format.schema:
            # Convert JSON Schema to OpenAI response_format structure
            schema = self.output_format.schema
            model_name = self._get_model_name_from_schema(schema)

            response_format = {"type": "json_schema", "json_schema": {"name": model_name, "schema": schema}}

            return f"RequestParams(response_format={response_format})"

        elif self.output_format.type == "schema_file" and self.output_format.file:
            # Load and convert external schema file
            return self._generate_request_params_from_file(base_path)

        return None

    def _generate_request_params_from_file(self, base_path: Optional[str] = None) -> str:
        """Generate RequestParams by loading schema from external file."""
        import json
        import os
        import yaml

        file_path = self.output_format.file

        # Resolve relative paths relative to the Agentfile location
        if not os.path.isabs(file_path) and base_path:
            file_path = os.path.join(base_path, file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    schema = json.load(f)
                elif file_path.endswith(('.yaml', '.yml')):
                    schema = yaml.safe_load(f)
                else:
                    return f"# Error: Unsupported schema file format: {file_path}"

            model_name = self._get_model_name_from_schema(schema)
            response_format = {"type": "json_schema", "json_schema": {"name": model_name, "schema": schema}}

            return f"RequestParams(response_format={response_format})"

        except (FileNotFoundError, json.JSONDecodeError, yaml.YAMLError) as e:
            return f"# Error loading schema file {file_path}: {e}"

    def _get_model_name_from_schema(self, schema: Dict[str, Any]) -> str:
        """Generate a model name from the agent name or schema title."""
        if isinstance(schema, dict) and "title" in schema:
            return schema["title"]

        # Convert agent name to PascalCase for model name
        words = self.name.replace("-", "_").replace(" ", "_").split("_")
        model_name = "".join(word.capitalize() for word in words if word)
        return f"{model_name}Model"


@dataclass
class Router:
    """Represents a router workflow."""

    name: str
    agents: List[str] = field(default_factory=list)
    model: Optional[str] = None
    instruction: Optional[str] = None
    default: bool = False

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

        if self.default:
            params.append("default=True")

        return "@fast.router(\n    " + ",\n    ".join(params) + "\n)"


@dataclass
class Chain:
    """Represents a chain workflow."""

    name: str
    sequence: List[str] = field(default_factory=list)
    instruction: Optional[str] = None
    cumulative: bool = False
    continue_with_final: bool = True
    default: bool = False

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

        if self.default:
            params.append("default=True")

        return "@fast.chain(\n    " + ",\n    ".join(params) + "\n)"


@dataclass
class Orchestrator:
    """Represents an orchestrator workflow."""

    name: str
    agents: List[str] = field(default_factory=list)
    model: Optional[str] = None
    instruction: Optional[str] = None
    plan_type: str = "full"
    plan_iterations: int = 5
    human_input: bool = False
    default: bool = False

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

        if self.plan_iterations != 5:
            params.append(f"plan_iterations={self.plan_iterations}")

        if self.human_input:
            params.append("human_input=True")

        if self.default:
            params.append("default=True")

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
class DockerfileInstruction:
    """Represents a Dockerfile instruction."""

    instruction: str
    args: List[str]

    def to_dockerfile_line(self) -> str:
        """Convert to Dockerfile line format."""
        if self.instruction in ["CMD", "ENTRYPOINT"] and len(self.args) > 1:
            # Handle array format for CMD/ENTRYPOINT
            args_str = json.dumps(self.args)
            return f"{self.instruction} {args_str}"
        return f"{self.instruction} {' '.join(self.args)}"


@dataclass
class AgentfileConfig:
    """Represents the complete Agentfile configuration."""

    base_image: str = "yeahdongcn/agentman-base:latest"
    default_model: Optional[str] = None
    framework: str = "fast-agent"  # "fast-agent" or "agno"
    servers: Dict[str, MCPServer] = field(default_factory=dict)
    agents: Dict[str, Agent] = field(default_factory=dict)
    routers: Dict[str, Router] = field(default_factory=dict)
    chains: Dict[str, Chain] = field(default_factory=dict)
    orchestrators: Dict[str, Orchestrator] = field(default_factory=dict)
    secrets: List[SecretType] = field(default_factory=list)
    expose_ports: List[int] = field(default_factory=list)
    cmd: List[str] = field(default_factory=lambda: ["python", "agent.py"])
    dockerfile_instructions: List[DockerfileInstruction] = field(default_factory=list)


class AgentfileParser:
    """Parser for Agentfile format."""

    def __init__(self, base_path: Optional[str] = None):
        self.config = AgentfileConfig()
        self.current_context = None
        self.current_item = None
        self.base_path = base_path

    def parse_file(self, filepath: str) -> AgentfileConfig:
        """Parse an Agentfile and return the configuration."""
        # Store the directory containing the Agentfile for resolving relative paths
        import os

        self.base_path = os.path.dirname(os.path.abspath(filepath))

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_content(content)

    def parse_content(self, content: str) -> AgentfileConfig:
        """Parse Agentfile content and return the configuration."""
        lines = content.split('\n')

        # Pre-process lines to handle multi-line continuations with backslash
        processed_lines = []
        current_line = ""
        continued_start_line_num = None

        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()  # Remove trailing whitespace but keep leading

            # Skip empty lines and comments if not part of a continuation
            if not current_line and (not line or line.lstrip().startswith('#')):
                continue

            # Check for line continuation
            if line.endswith('\\'):
                # Remove the backslash and add to current line with a space
                if not current_line:
                    # This is the start of a new continued line, so record the starting line number
                    continued_start_line_num = line_num
                current_line += f"{line[:-1].rstrip()} "
            else:
                # Complete the line
                current_line += line
                if current_line.strip():  # Only add non-empty lines
                    # Use the real start line number for continued instructions
                    if continued_start_line_num is not None:
                        processed_lines.append((continued_start_line_num, current_line.strip()))
                        continued_start_line_num = None
                    else:
                        processed_lines.append((line_num, current_line.strip()))
                current_line = ""

        # Handle any remaining line (shouldn't happen with proper syntax)
        if current_line.strip():
            # Use the real start line number for continued instructions if present
            if continued_start_line_num is not None:
                processed_lines.append((continued_start_line_num, current_line.strip()))
            else:
                processed_lines.append((len(lines), current_line.strip()))

        # Parse each processed line
        for line_num, line in processed_lines:
            try:
                self._parse_line(line)
            except Exception as e:
                raise ValueError(f"Error parsing line {line_num}: {line}\n{str(e)}") from e

        return self.config

    def _parse_line(self, line: str):
        """Parse a single line of the Agentfile."""
        # Split by whitespace but handle quoted strings
        parts = self._split_respecting_quotes(line)
        if not parts:
            return

        instruction = parts[0].upper()

        # Agentman-specific instructions (not Docker)
        if instruction == "MODEL":
            # Check if we're in a context that should handle MODEL as sub-instruction
            if self.current_context in ["agent"]:
                self._handle_sub_instruction(instruction, parts)
            else:
                self._handle_model(parts)
        elif instruction == "FRAMEWORK":
            self._handle_framework(parts)
        elif instruction in ["SERVER", "MCP_SERVER"]:
            self._handle_server(parts)
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
        # Dockerfile instructions - handle specially where needed
        elif instruction == "FROM":
            self._handle_from(parts)
            self._handle_dockerfile_instruction(instruction, parts)
        elif instruction == "EXPOSE":
            self._handle_expose(parts)
            self._handle_dockerfile_instruction(instruction, parts)
        elif instruction == "CMD":
            self._handle_cmd(parts)
            # Store the CMD instruction with the correctly parsed args
            dockerfile_instruction = DockerfileInstruction(instruction="CMD", args=self.config.cmd)
            self.config.dockerfile_instructions.append(dockerfile_instruction)
        elif instruction == "RUN":
            self._handle_dockerfile_instruction(instruction, parts)
        # All other Dockerfile instructions - store as-is
        elif instruction in [
            # Standard Dockerfile instructions
            "ARG",
            "ADD",
            "COPY",
            "ENTRYPOINT",
            "HEALTHCHECK",
            "LABEL",
            "MAINTAINER",
            "ONBUILD",
            "SHELL",
            "STOPSIGNAL",
            "USER",
            "VOLUME",
            "WORKDIR",
            # BuildKit instructions
            "MOUNT",
            "BUILDKIT",
        ]:
            self._handle_dockerfile_instruction(instruction, parts)
        # Sub-instructions for contexts
        elif instruction in [
            "COMMAND",
            "ARGS",
            "INSTRUCTION",
            "SERVERS",
            "AGENTS",
            "SEQUENCE",
            "TRANSPORT",
            "URL",
            "USE_HISTORY",
            "HUMAN_INPUT",
            "PLAN_TYPE",
            "PLAN_ITERATIONS",
            "CUMULATIVE",
            "API_KEY",
            "BASE_URL",
            "DEFAULT",
            "OUTPUT_FORMAT",
        ]:
            self._handle_sub_instruction(instruction, parts)
        # Handle ENV - could be Dockerfile instruction or sub-instruction
        elif instruction == "ENV":
            if self.current_context and self.current_context == "server":
                # It's a sub-instruction for SERVER context
                self._handle_sub_instruction(instruction, parts)
            else:
                # It's a Dockerfile instruction
                self._handle_dockerfile_instruction(instruction, parts)
        else:
            # Unknown instruction - treat as potential Dockerfile instruction
            # for forward compatibility
            self._handle_dockerfile_instruction(instruction, parts)

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

    def _handle_framework(self, parts: List[str]):
        """Handle FRAMEWORK instruction."""
        if len(parts) < 2:
            raise ValueError("FRAMEWORK requires a framework name")
        framework = self._unquote(parts[1]).lower()
        if framework not in ["fast-agent", "agno"]:
            raise ValueError(f"Unsupported framework: {framework}. Supported: fast-agent, agno")
        self.config.framework = framework
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
        - SECRET openai (context for multiple values)
        """
        if len(parts) < 2:
            raise ValueError("SECRET requires a secret name")

        secret_name = self._unquote(parts[1])

        # Check if it's an inline value: SECRET KEY value
        if len(parts) >= 3:
            value = ' '.join(parts[2:])  # Join all remaining parts as the value
            expanded_value = expand_env_vars(self._unquote(value))
            secret = SecretValue(name=secret_name, value=expanded_value)
            self.config.secrets.append(secret)
            self.current_context = None
        # Check if it's a context (no value, will be populated with sub-instructions)
        elif len(parts) == 2:
            # Check if a secret context with this name already exists
            existing_secret = next(
                (
                    secret
                    for secret in self.config.secrets
                    if isinstance(secret, SecretContext) and secret.name == secret_name
                ),
                None,
            )

            if existing_secret:
                # Reuse existing secret context
                self.current_context = "secret"
                self.current_item = secret_name
            else:
                # Create a new secret context - this will be used if subsequent
                # lines contain key-value pairs. If no key-value pairs follow,
                # it will be treated as a simple reference
                secret = SecretContext(name=secret_name)
                self.config.secrets.append(secret)
                self.current_context = "secret"
                self.current_item = secret_name
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
            key = instruction.upper()
            value = ' '.join(parts[1:])
            expanded_value = expand_env_vars(self._unquote(value))
            secret_context.values[key] = expanded_value
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
        except ValueError as exc:
            raise ValueError(f"Invalid port number: {parts[1]}") from exc
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

    def _handle_dockerfile_instruction(self, instruction: str, parts: List[str]):
        """Handle any generic Dockerfile instruction."""
        if len(parts) < 2:
            raise ValueError(f"{instruction} requires arguments")

        # Special handling for ENV instruction to support KEY=VALUE format
        if instruction == "ENV":
            # Handle both KEY VALUE and KEY=VALUE formats for Dockerfile ENV
            args = parts[1:]
            if len(args) == 1 and '=' in args[0]:
                # KEY=VALUE format - keep as single argument for Dockerfile
                dockerfile_args = args
            else:
                # KEY VALUE format or multiple args - keep as is
                dockerfile_args = args
        else:
            dockerfile_args = parts[1:]

        # Store all instructions for ordered generation
        dockerfile_instruction = DockerfileInstruction(instruction=instruction, args=dockerfile_args)
        self.config.dockerfile_instructions.append(dockerfile_instruction)
        self.current_context = None

    def _handle_sub_instruction(self, instruction: str, parts: List[str]):
        """Handle sub-instructions that modify the current context item."""
        if not self.current_context:
            # Special case: if we're not in a context but this looks like
            # a key-value pair for a secret context, try to handle it
            if self.current_item and any(
                isinstance(s, SecretContext) and s.name == self.current_item for s in self.config.secrets
            ):
                self.current_context = "secret"
                self._handle_secret_sub_instruction(instruction, parts)
                return
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
            if len(parts) < 2:
                raise ValueError("ENV requires KEY VALUE or KEY=VALUE")

            if len(parts) == 2:
                # Handle KEY=VALUE format
                env_part = parts[1]
                if '=' in env_part:
                    key, value = env_part.split('=', 1)  # Split only on first =
                    key = self._unquote(key)
                    value = self._unquote(value)
                    expanded_value = expand_env_vars(value)
                    server.env[key] = expanded_value
                else:
                    raise ValueError("ENV requires KEY VALUE or KEY=VALUE")
            elif len(parts) >= 3:
                # Handle KEY VALUE format
                key = self._unquote(parts[1])
                value = self._unquote(' '.join(parts[2:]))  # Join remaining parts as value
                expanded_value = expand_env_vars(value)
                server.env[key] = expanded_value
            else:
                raise ValueError("ENV requires KEY VALUE or KEY=VALUE")

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
        elif instruction == "DEFAULT":
            if len(parts) < 2:
                raise ValueError("DEFAULT requires true/false")
            agent.default = self._unquote(parts[1]).lower() in ['true', '1', 'yes']
        elif instruction == "OUTPUT_FORMAT":
            if len(parts) < 2:
                raise ValueError("OUTPUT_FORMAT requires a format type")
            format_type = self._unquote(parts[1])
            if format_type == "json_schema":
                if len(parts) < 3:
                    raise ValueError("OUTPUT_FORMAT json_schema requires a schema definition or file reference")
                schema_value = self._unquote(' '.join(parts[2:]))
                # Try to parse as inline YAML/JSON schema
                try:
                    import yaml

                    schema_dict = yaml.safe_load(schema_value)
                    agent.output_format = OutputFormat(type="json_schema", schema=schema_dict)
                except (ImportError, yaml.YAMLError):
                    # Fallback: treat as file reference if it looks like a path
                    if schema_value.endswith(('.json', '.yaml', '.yml')):
                        agent.output_format = OutputFormat(type="schema_file", file=schema_value)
                    else:
                        raise ValueError("OUTPUT_FORMAT json_schema requires valid YAML/JSON schema or file path")
            elif format_type == "schema_file":
                if len(parts) < 3:
                    raise ValueError("OUTPUT_FORMAT schema_file requires a file path")
                file_path = self._unquote(parts[2])
                if not file_path.endswith(('.json', '.yaml', '.yml')):
                    raise ValueError("OUTPUT_FORMAT schema_file must reference a .json, .yaml, or .yml file")
                agent.output_format = OutputFormat(type="schema_file", file=file_path)
            else:
                raise ValueError(f"Invalid OUTPUT_FORMAT type: {format_type}. Supported: json_schema, schema_file")

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
        elif instruction == "DEFAULT":
            if len(parts) < 2:
                raise ValueError("DEFAULT requires true/false")
            router.default = self._unquote(parts[1]).lower() in ['true', '1', 'yes']

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
        elif instruction == "DEFAULT":
            if len(parts) < 2:
                raise ValueError("DEFAULT requires true/false")
            chain.default = self._unquote(parts[1]).lower() in ['true', '1', 'yes']

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
        elif instruction == "PLAN_ITERATIONS":
            if len(parts) < 2:
                raise ValueError("PLAN_ITERATIONS requires a number")
            try:
                orchestrator.plan_iterations = int(parts[1])
            except ValueError as exc:
                raise ValueError(f"Invalid number for PLAN_ITERATIONS: {parts[1]}") from exc
        elif instruction == "HUMAN_INPUT":
            if len(parts) < 2:
                raise ValueError("HUMAN_INPUT requires true/false")
            orchestrator.human_input = self._unquote(parts[1]).lower() in ['true', '1', 'yes']
        elif instruction == "DEFAULT":
            if len(parts) < 2:
                raise ValueError("DEFAULT requires true/false")
            orchestrator.default = self._unquote(parts[1]).lower() in ['true', '1', 'yes']
