"""Conversion utilities for Agentfile formats."""

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from agentman.agentfile_parser import (
    AgentfileConfig,
    AgentfileParser,
    SecretContext,
    SecretValue,
)
from agentman.yaml_parser import AgentfileYamlParser, detect_yaml_format, parse_agentfile


def dockerfile_to_yaml(dockerfile_path: str, yaml_path: str) -> None:
    """Convert a Dockerfile-format Agentfile to YAML format."""
    # Parse the Dockerfile format
    parser = AgentfileParser()
    config = parser.parse_file(dockerfile_path)

    # Convert to YAML format
    yaml_data = config_to_yaml_dict(config)

    # Write to YAML file
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, indent=2)


def yaml_to_dockerfile(yaml_path: str, dockerfile_path: str) -> None:
    """Convert a YAML-format Agentfile to Dockerfile format."""
    # Parse the YAML format
    parser = AgentfileYamlParser()
    config = parser.parse_file(yaml_path)

    # Convert to Dockerfile format
    dockerfile_content = config_to_dockerfile_content(config)

    # Write to Dockerfile format
    with open(dockerfile_path, 'w', encoding='utf-8') as f:
        f.write(dockerfile_content)


def config_to_yaml_dict(config: AgentfileConfig) -> Dict[str, Any]:
    """Convert AgentfileConfig to YAML dictionary."""
    yaml_data = {"apiVersion": "v1", "kind": "Agent"}

    # Base configuration
    base_config = {}
    if config.base_image != "yeahdongcn/agentman-base:latest":
        base_config["image"] = config.base_image
    if config.default_model:
        base_config["model"] = config.default_model
    if config.framework != "fast-agent":
        base_config["framework"] = config.framework

    if base_config:
        yaml_data["base"] = base_config

    # MCP servers
    if config.servers:
        mcp_servers = []
        for server in config.servers.values():
            server_dict = {"name": server.name}
            if server.command:
                server_dict["command"] = server.command
            if server.args:
                server_dict["args"] = server.args
            if server.transport != "stdio":
                server_dict["transport"] = server.transport
            if server.url:
                server_dict["url"] = server.url
            if server.env:
                server_dict["env"] = server.env
            mcp_servers.append(server_dict)
        yaml_data["mcp_servers"] = mcp_servers

    # Agent configuration
    if config.agents:
        agents_list = []
        for agent in config.agents.values():
            agent_dict = {"name": agent.name}
            if agent.instruction != "You are a helpful agent.":
                agent_dict["instruction"] = agent.instruction
            if agent.servers:
                agent_dict["servers"] = agent.servers
            if agent.model:
                agent_dict["model"] = agent.model
            if not agent.use_history:
                agent_dict["use_history"] = agent.use_history
            if agent.human_input:
                agent_dict["human_input"] = agent.human_input
            if agent.default:
                agent_dict["default"] = agent.default
            agents_list.append(agent_dict)

        yaml_data["agents"] = agents_list

    # Routers
    if config.routers:
        routers_list = []
        for router in config.routers.values():
            router_dict = {"name": router.name}
            if router.agents:
                router_dict["agents"] = router.agents
            if router.model:
                router_dict["model"] = router.model
            if router.instruction:
                router_dict["instruction"] = router.instruction
            if router.default:
                router_dict["default"] = router.default
            routers_list.append(router_dict)
        yaml_data["routers"] = routers_list

    # Chains
    if config.chains:
        chains_list = []
        for chain in config.chains.values():
            chain_dict = {"name": chain.name}
            if chain.sequence:
                chain_dict["sequence"] = chain.sequence
            if chain.instruction:
                chain_dict["instruction"] = chain.instruction
            if chain.cumulative:
                chain_dict["cumulative"] = chain.cumulative
            if not chain.continue_with_final:
                chain_dict["continue_with_final"] = chain.continue_with_final
            if chain.default:
                chain_dict["default"] = chain.default
            chains_list.append(chain_dict)
        yaml_data["chains"] = chains_list

    # Orchestrators
    if config.orchestrators:
        orchestrators_list = []
        for orchestrator in config.orchestrators.values():
            orchestrator_dict = {"name": orchestrator.name}
            if orchestrator.agents:
                orchestrator_dict["agents"] = orchestrator.agents
            if orchestrator.model:
                orchestrator_dict["model"] = orchestrator.model
            if orchestrator.instruction:
                orchestrator_dict["instruction"] = orchestrator.instruction
            if orchestrator.plan_type != "full":
                orchestrator_dict["plan_type"] = orchestrator.plan_type
            if orchestrator.plan_iterations != 5:
                orchestrator_dict["plan_iterations"] = orchestrator.plan_iterations
            if orchestrator.human_input:
                orchestrator_dict["human_input"] = orchestrator.human_input
            if orchestrator.default:
                orchestrator_dict["default"] = orchestrator.default
            orchestrators_list.append(orchestrator_dict)
        yaml_data["orchestrators"] = orchestrators_list

    # Command
    if config.cmd != ["python", "agent.py"]:
        yaml_data["command"] = config.cmd

    # Secrets
    if config.secrets:
        secrets_list = []
        for secret in config.secrets:
            if isinstance(secret, str):
                secrets_list.append(secret)
            elif isinstance(secret, SecretValue):
                secrets_list.append({"name": secret.name, "value": secret.value})
            elif isinstance(secret, SecretContext):
                secrets_list.append({"name": secret.name, "values": secret.values})
        yaml_data["secrets"] = secrets_list

    # Expose ports
    if config.expose_ports:
        yaml_data["expose"] = config.expose_ports

    # Dockerfile instructions
    if config.dockerfile_instructions:
        dockerfile_list = []
        for instruction in config.dockerfile_instructions:
            if instruction.instruction not in ["FROM", "CMD"]:  # Skip instructions handled elsewhere
                dockerfile_list.append({"instruction": instruction.instruction, "args": instruction.args})
        if dockerfile_list:
            yaml_data["dockerfile"] = dockerfile_list

    return yaml_data


def config_to_dockerfile_content(config: AgentfileConfig) -> str:
    """Convert AgentfileConfig to Dockerfile format content."""
    lines = []

    # FROM instruction
    lines.append(f"FROM {config.base_image}")

    # Framework
    if config.framework != "fast-agent":
        lines.append(f"FRAMEWORK {config.framework}")

    # Model
    if config.default_model:
        lines.append(f"MODEL {config.default_model}")

    lines.append("")  # Empty line for readability

    # Secrets
    for secret in config.secrets:
        if isinstance(secret, str):
            lines.append(f"SECRET {secret}")
        elif isinstance(secret, SecretValue):
            lines.append(f"SECRET {secret.name} {secret.value}")
        elif isinstance(secret, SecretContext):
            lines.append(f"SECRET {secret.name}")
            for key, value in secret.values.items():
                lines.append(f"{key} {value}")

    if config.secrets:
        lines.append("")  # Empty line for readability

    # Servers
    for server in config.servers.values():
        lines.append(f"MCP_SERVER {server.name}")
        if server.command:
            lines.append(f"COMMAND {server.command}")
        if server.args:
            args_str = " ".join(server.args)
            lines.append(f"ARGS {args_str}")
        if server.transport != "stdio":
            lines.append(f"TRANSPORT {server.transport}")
        if server.url:
            lines.append(f"URL {server.url}")
        for key, value in server.env.items():
            lines.append(f"ENV {key} {value}")
        lines.append("")  # Empty line for readability

    # Agents
    for agent in config.agents.values():
        lines.append(f"AGENT {agent.name}")
        if agent.instruction != "You are a helpful agent.":
            lines.append(f"INSTRUCTION {agent.instruction}")
        if agent.servers:
            servers_str = " ".join(agent.servers)
            lines.append(f"SERVERS {servers_str}")
        if agent.model:
            lines.append(f"MODEL {agent.model}")
        if not agent.use_history:
            lines.append("USE_HISTORY false")
        if agent.human_input:
            lines.append("HUMAN_INPUT true")
        if agent.default:
            lines.append("DEFAULT true")
        lines.append("")  # Empty line for readability

    # Routers
    for router in config.routers.values():
        lines.append(f"ROUTER {router.name}")
        if router.agents:
            agents_str = " ".join(router.agents)
            lines.append(f"AGENTS {agents_str}")
        if router.model:
            lines.append(f"MODEL {router.model}")
        if router.instruction:
            lines.append(f"INSTRUCTION {router.instruction}")
        if router.default:
            lines.append("DEFAULT true")
        lines.append("")  # Empty line for readability

    # Chains
    for chain in config.chains.values():
        lines.append(f"CHAIN {chain.name}")
        if chain.sequence:
            sequence_str = " ".join(chain.sequence)
            lines.append(f"SEQUENCE {sequence_str}")
        if chain.instruction:
            lines.append(f"INSTRUCTION {chain.instruction}")
        if chain.cumulative:
            lines.append("CUMULATIVE true")
        if not chain.continue_with_final:
            lines.append("CONTINUE_WITH_FINAL false")
        if chain.default:
            lines.append("DEFAULT true")
        lines.append("")  # Empty line for readability

    # Orchestrators
    for orchestrator in config.orchestrators.values():
        lines.append(f"ORCHESTRATOR {orchestrator.name}")
        if orchestrator.agents:
            agents_str = " ".join(orchestrator.agents)
            lines.append(f"AGENTS {agents_str}")
        if orchestrator.model:
            lines.append(f"MODEL {orchestrator.model}")
        if orchestrator.instruction:
            lines.append(f"INSTRUCTION {orchestrator.instruction}")
        if orchestrator.plan_type != "full":
            lines.append(f"PLAN_TYPE {orchestrator.plan_type}")
        if orchestrator.plan_iterations != 5:
            lines.append(f"PLAN_ITERATIONS {orchestrator.plan_iterations}")
        if orchestrator.human_input:
            lines.append("HUMAN_INPUT true")
        if orchestrator.default:
            lines.append("DEFAULT true")
        lines.append("")  # Empty line for readability

    # Dockerfile instructions
    for instruction in config.dockerfile_instructions:
        if instruction.instruction not in ["FROM", "CMD"]:
            lines.append(instruction.to_dockerfile_line())

    # Expose ports
    for port in config.expose_ports:
        lines.append(f"EXPOSE {port}")

    # CMD instruction
    if config.cmd != ["python", "agent.py"]:
        if len(config.cmd) == 1:
            lines.append(f"CMD {config.cmd[0]}")
        else:
            lines.append(f"CMD {json.dumps(config.cmd)}")

    return "\n".join(lines) + "\n"


def convert_agentfile(input_path: str, output_path: str, target_format: str = "auto") -> None:
    """Convert an Agentfile between formats.

    Args:
        input_path: Path to the input Agentfile
        output_path: Path to write the converted Agentfile
        target_format: Target format ("yaml", "dockerfile", or "auto" to infer from output extension)
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Determine target format
    if target_format == "auto":
        if output_path.suffix.lower() in ['.yml', '.yaml']:
            target_format = "yaml"
        else:
            target_format = "dockerfile"

    # Determine source format
    is_yaml_source = detect_yaml_format(str(input_path))

    if is_yaml_source and target_format == "yaml":
        raise ValueError("Input and output formats are both YAML")
    if not is_yaml_source and target_format == "dockerfile":
        raise ValueError("Input and output formats are both Dockerfile")

    # Convert based on source and target formats
    if is_yaml_source and target_format == "dockerfile":
        yaml_to_dockerfile(str(input_path), str(output_path))
    elif not is_yaml_source and target_format == "yaml":
        dockerfile_to_yaml(str(input_path), str(output_path))
    else:
        raise ValueError(f"Unsupported conversion: {is_yaml_source} -> {target_format}")

    print(f"✅ Converted {input_path} to {output_path} ({target_format} format)")


def validate_agentfile(filepath: str) -> bool:
    """Validate an Agentfile in either format.

    Args:
        filepath: Path to the Agentfile to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        config = parse_agentfile(filepath)

        # Basic validation
        if not config.base_image:
            print("❌ Validation failed: Missing base image")
            return False

        if not config.agents:
            print("❌ Validation failed: No agents defined")
            return False

        # Check that all agent servers are defined
        for agent in config.agents.values():
            for server_name in agent.servers:
                if server_name not in config.servers:
                    print(f"❌ Validation failed: Agent '{agent.name}' references undefined server '{server_name}'")
                    return False

        print("✅ Agentfile is valid")
        return True

    except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
        print(f"❌ Validation failed: {e}")
        return False
