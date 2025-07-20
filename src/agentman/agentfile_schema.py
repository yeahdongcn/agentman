"""JSON Schema for validating YAML Agentfile configurations."""

import json
from typing import Any, Dict

try:
    import jsonschema
except ImportError:
    jsonschema = None

# JSON Schema for YAML Agentfile format
AGENTFILE_YAML_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["apiVersion", "kind"],
    "properties": {
        "apiVersion": {"type": "string", "const": "v1", "description": "API version, currently only 'v1' is supported"},
        "kind": {
            "type": "string",
            "const": "Agent",
            "description": "Resource kind, currently only 'Agent' is supported",
        },
        "base": {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base Docker image",
                    "default": "ghcr.io/o3-cloud/pai/base:latest",
                },
                "model": {
                    "type": "string",
                    "description": "Default model to use for agents",
                    "examples": ["gpt-4", "anthropic/claude-3-sonnet-20241022"],
                },
                "framework": {
                    "type": "string",
                    "enum": ["fast-agent", "agno"],
                    "description": "Framework to use for agent development",
                    "default": "fast-agent",
                },
            },
            "additionalProperties": False,
        },
        "mcp_servers": {
            "type": "array",
            "description": "List of MCP (Model Context Protocol) servers",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Unique name for the MCP server"},
                    "command": {"type": "string", "description": "Command to run the MCP server"},
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments to pass to the command",
                    },
                    "transport": {
                        "type": "string",
                        "enum": ["stdio", "sse", "http"],
                        "default": "stdio",
                        "description": "Transport method for the MCP server",
                    },
                    "url": {"type": "string", "description": "URL for HTTP/SSE transport"},
                    "env": {
                        "type": "object",
                        "patternProperties": {"^[A-Z_][A-Z0-9_]*$": {"type": "string"}},
                        "additionalProperties": False,
                        "description": "Environment variables for the MCP server",
                    },
                },
                "additionalProperties": False,
            },
        },
        "agents": {
            "type": "array",
            "description": "List of agents",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Name of the agent"},
                    "instruction": {
                        "type": "string",
                        "description": "Instructions for the agent",
                        "default": "You are a helpful agent.",
                    },
                    "servers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of MCP server names this agent can use",
                    },
                    "model": {"type": "string", "description": "Model to use for this agent (overrides base model)"},
                    "use_history": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether the agent should use conversation history",
                    },
                    "human_input": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether the agent should prompt for human input",
                    },
                    "default": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether this is the default agent",
                    },
                    "output_format": {
                        "oneOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["json_schema"],
                                        "description": "Format type for output validation",
                                    },
                                    "schema": {"type": "object", "description": "Inline JSON Schema as YAML object"},
                                },
                                "required": ["type", "schema"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["schema_file"],
                                        "description": "Reference to external schema file",
                                    },
                                    "file": {
                                        "type": "string",
                                        "description": "Path to external schema file (.json or .yaml/.yml)",
                                    },
                                },
                                "required": ["type", "file"],
                                "additionalProperties": False,
                            },
                        ],
                        "description": "Output format specification for structured data validation",
                    },
                },
                "additionalProperties": False,
            },
        },
        "command": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Default command to run in the container",
            "default": ["python", "agent.py"],
        },
        "entrypoint": {
            "type": "array", 
            "items": {"type": "string"},
            "description": "Entrypoint command for the container"
        },
        "secrets": {
            "type": "array",
            "description": "List of secrets the agent needs",
            "items": {
                "oneOf": [
                    {"type": "string", "description": "Simple secret reference"},
                    {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string", "description": "Name of the secret"},
                            "value": {"type": "string", "description": "Inline secret value"},
                            "values": {
                                "type": "object",
                                "patternProperties": {"^[A-Z_][A-Z0-9_]*$": {"type": "string"}},
                                "additionalProperties": False,
                                "description": "Multiple key-value pairs for secret context",
                            },
                        },
                        "additionalProperties": False,
                        "not": {"allOf": [{"required": ["value"]}, {"required": ["values"]}]},
                    },
                ]
            },
        },
        "expose": {
            "type": "array",
            "items": {"type": "integer", "minimum": 1, "maximum": 65535},
            "description": "List of ports to expose",
        },
        "dockerfile": {
            "type": "array",
            "description": "Additional Dockerfile instructions",
            "items": {
                "type": "object",
                "required": ["instruction", "args"],
                "properties": {
                    "instruction": {"type": "string", "description": "Dockerfile instruction (e.g., RUN, COPY, ENV)"},
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments for the instruction",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


def validate_yaml_agentfile(data: Dict[str, Any]) -> bool:
    """Validate YAML Agentfile data against the schema."""
    if jsonschema is None:
        # If jsonschema is not available, skip validation
        return True

    try:
        jsonschema.validate(data, AGENTFILE_YAML_SCHEMA)
        return True
    except jsonschema.exceptions.ValidationError:
        return False


def get_schema_as_json() -> str:
    """Get the schema as a JSON string."""
    return json.dumps(AGENTFILE_YAML_SCHEMA, indent=2)


def get_example_yaml() -> str:
    """Get an example YAML Agentfile."""
    return """apiVersion: v1
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

agents:
  - name: gmail_actions
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
    output_format:
      type: json_schema
      schema:
        type: object
        properties:
          summary:
            type: string
            description: Brief summary of actions taken
          emails_processed:
            type: integer
            description: Number of emails processed
          labels_applied:
            type: array
            items:
              type: object
              properties:
                email_subject:
                  type: string
                label:
                  type: string
                reason:
                  type: string
        required: [summary, emails_processed, labels_applied]

  - name: data_analyzer
    instruction: Analyze data and generate structured reports
    servers: [fetch]
    output_format:
      type: schema_file
      file: ./schemas/analysis_output.yaml

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
    args: [apt-get, update, &&, apt-get, install, -y, curl]
  - instruction: ENV
    args: [PYTHONPATH=/app]
"""
