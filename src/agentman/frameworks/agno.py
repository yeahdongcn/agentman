"""Agno framework implementation for AgentMan."""

import os
from typing import List, Dict, Any, Set

from .base import BaseFramework
from agentman.agentfile_parser import Agent # Corrected import


class AgnoFramework(BaseFramework):
    """Framework implementation for Agno."""

    def _get_model_import_path(self, model_id: str) -> str:
        """Determines the import path for a given model ID."""
        model_lower = model_id.lower()
        if "anthropic" in model_lower or "claude" in model_lower:
            return "agno.models.anthropic.Claude"
        elif "openai" in model_lower or "gpt" in model_lower:
            return "agno.models.openai.OpenAILike"
        elif "/" in model_lower:  # ollama/llama3, groq/mixtral etc.
            # For now, these are often OpenAILike compatible
            return "agno.models.openai.OpenAILike"
        # Add more mappings as Agno supports more specific model classes
        return "agno.models.openai.OpenAILike" # Default fallback

    def _get_tool_import_path_and_init_str(self, server_name: str, server_config: Any = None) -> tuple[str, str]:
        """Determines the import path and initialization string for a server/tool."""
        # This mapping should be expanded based on Agno's available tools
        # and how they map to Agentfile server types.
        if server_name in ["web_search", "search", "browser"]:
            return "agno.tools.duckduckgo.DuckDuckGoTools", "DuckDuckGoTools()"
        elif server_name in ["finance", "yfinance", "stock"]:
            # Example: YFinanceTools can take parameters
            # We might need to parse server_config if it contains tool-specific settings
            return "agno.tools.yfinance.YFinanceTools", "YFinanceTools(stock_price=True, analyst_recommendations=True)"
        elif server_name in ["file", "filesystem"]:
            return "agno.tools.file.FileTools", "FileTools()"
        elif server_name in ["shell", "terminal"]:
            return "agno.tools.shell.ShellTools", "ShellTools()"
        elif server_name in ["python", "code"]:
            return "agno.tools.python.PythonTools", "PythonTools()"
        # Default or unknown server
        return "", ""


    def build_agent_content(self) -> str:
        """Build the Python agent file content for Agno framework using programmatic object creation."""

        script_lines: List[str] = []
        imports: Set[str] = {
            "import os",
            "from agno.agent import Agent",
            "from dotenv import load_dotenv",
            "from agno.tools.reasoning import ReasoningTools", # Always include
        }

        has_multiple_agents = len(self.config.agents) > 1
        if has_multiple_agents:
            imports.add("from agno.team.team import Team")

        agent_definitions: List[str] = []
        agent_var_names: List[str] = []

        default_model_str = self.config.default_model or "anthropic/claude-3-sonnet-20241022" # Sensible default

        for agent_config in self.config.agents.values():
            agent_var_name = f"{agent_config.name.lower().replace('-', '_')}_agent"
            agent_var_names.append(agent_var_name)

            agent_params: Dict[str, Any] = {
                "name": agent_config.name,
                "instructions": agent_config.instruction,
                "markdown": True, # Default from previous logic
                "add_datetime_to_instructions": True, # Default from previous logic
                "add_history_to_messages": agent_config.use_history,
                "human_input": agent_config.human_input,
            }
            if has_multiple_agents:
                 agent_params["role"] = f"Handle {agent_config.name.lower().replace('-', ' ')} requests"


            # Model
            current_model_str = agent_config.model or default_model_str
            model_import_path = self._get_model_import_path(current_model_str)
            model_class_name = model_import_path.split('.')[-1]
            imports.add(f"from {'.'.join(model_import_path.split('.')[:-1])} import {model_class_name}")

            model_init_params = [f'id="{current_model_str}"']
            if model_class_name == "OpenAILike":
                 model_init_params.append('api_key=os.getenv("OPENAI_API_KEY")')
                 model_init_params.append('base_url=os.getenv("OPENAI_BASE_URL")')
                 if "/" in current_model_str: # e.g. ollama/llama3
                    provider = current_model_str.split('/')[0].upper()
                    model_init_params = [
                        f'id="{current_model_str}"',
                        f'api_key=os.getenv("{provider}_API_KEY")',
                        f'base_url=os.getenv("{provider}_BASE_URL")'
                    ]
            agent_params["model"] = f"{model_class_name}({', '.join(model_init_params)})"


            # Tools
            agent_tools_str: List[str] = ["ReasoningTools(add_instructions=True)"] # Always add
            for server_name in agent_config.servers:
                # server_config_obj = self.config.servers.get(server_name) # If server specific config is needed
                tool_import_path, tool_init_str = self._get_tool_import_path_and_init_str(server_name)
                if tool_import_path and tool_init_str:
                    tool_class_name = tool_import_path.split('.')[-1]
                    imports.add(f"from {'.'.join(tool_import_path.split('.')[:-1])} import {tool_class_name}")
                    agent_tools_str.append(tool_init_str)

            if agent_tools_str:
                 agent_params["tools"] = f"[{', '.join(agent_tools_str)}]"

            # Construct agent definition string
            agent_def = f"{agent_var_name} = Agent(\n"
            for key, value in agent_params.items():
                if isinstance(value, str) and (key == "model" or key == "tools" or not value.startswith('"')):
                    # For model and tools, value is already code. For others, add quotes if not present.
                    # Special handling for instructions to be multi-line string
                    if key == "instructions":
                        agent_def += f'    {key}="""{value}""",\n'
                    else:
                        agent_def += f"    {key}={value},\n"
                elif isinstance(value, bool):
                     agent_def += f"    {key}={value},\n" # Booleans don't need quotes
                else:
                    agent_def += f'    {key}="{value}",\n'
            agent_def += ")"
            agent_definitions.append(f"# Agent: {agent_config.name}\n{agent_def}\n")

        # Add sorted imports to script
        script_lines.extend(sorted(list(imports)))
        script_lines.append("\n# Load environment variables from .env file")
        script_lines.append("load_dotenv()\n")

        # Add agent definitions
        script_lines.extend(agent_definitions)

        # Team definition if multiple agents
        main_entity_var_name = ""
        if has_multiple_agents:
            team_var_name = "agentteam" # Default team name, matching test expectation
            main_entity_var_name = team_var_name

            team_model_str = self.config.agents.values().__iter__().__next__().model or default_model_str # Use first agent's model or default
            team_model_import_path = self._get_model_import_path(team_model_str)
            team_model_class_name = team_model_import_path.split('.')[-1]
            # Ensure model import is present (might be redundant if already added by an agent)
            imports.add(f"from {'.'.join(team_model_import_path.split('.')[:-1])} import {team_model_class_name}")


            team_model_init_params = [f'id="{team_model_str}"']
            if team_model_class_name == "OpenAILike":
                 team_model_init_params.append('api_key=os.getenv("OPENAI_API_KEY")')
                 team_model_init_params.append('base_url=os.getenv("OPENAI_BASE_URL")')
                 if "/" in team_model_str:
                    provider = team_model_str.split('/')[0].upper()
                    team_model_init_params = [
                        f'id="{team_model_str}"',
                        f'api_key=os.getenv("{provider}_API_KEY")',
                        f'base_url=os.getenv("{provider}_BASE_URL")'
                    ]

            team_params = {
                "name": "AgentTeam",
                "mode": "'coordinate'", # Default mode
                "model": f"{team_model_class_name}({', '.join(team_model_init_params)})",
                "members": f"[{', '.join(agent_var_names)}]",
                "tools": "[ReasoningTools(add_instructions=True)]", # Default team tools
                "instructions": """[
                    'Collaborate to provide comprehensive responses',
                    'Consider multiple perspectives and expertise areas',
                    'Present findings in a structured, easy-to-follow format',
                    'Only output the final consolidated response',
                ]""",
                "markdown": True,
                "show_members_responses": True,
                "enable_agentic_context": True,
                "add_datetime_to_instructions": True,
                "success_criteria": "'The team has provided a complete and accurate response.'",
            }
            team_def = f"{team_var_name} = Team(\n"
            for key, value in team_params.items():
                if isinstance(value, str) and (value.startswith("[") or value.startswith("'") or value.startswith('"""') or "agno.models" in value or "Tools(" in value):
                    team_def += f"    {key}={value},\n"
                elif isinstance(value, bool):
                    team_def += f"    {key}={value},\n"
                else:
                    team_def += f'    {key}="{value}",\n'
            team_def += ")\n"
            script_lines.append("# Multi-Agent Team\n" + team_def)
        elif agent_var_names:
            main_entity_var_name = agent_var_names[0]

        # Main function
        script_lines.append("def main() -> None:")
        if self.has_prompt_file:
            script_lines.extend([
                "    # Check if prompt.txt exists and load its content",
                "    prompt_content = None",
                "    if os.path.exists('prompt.txt'):",
                "        with open('prompt.txt', 'r', encoding='utf-8') as f:",
                "            prompt_content = f.read().strip()",
                "",
                "    if prompt_content:",
                f"        {main_entity_var_name}.print_response(prompt_content, stream=True, show_full_reasoning=True, stream_intermediate_steps=True)",
                "    else:",
                f"        {main_entity_var_name}.print_response('Hello! How can I help you today?', stream=True, show_full_reasoning=True, stream_intermediate_steps=True)",
            ])
        else:
            script_lines.append(f"    {main_entity_var_name}.print_response('Hello! How can I help you today?', stream=True, show_full_reasoning=True, stream_intermediate_steps=True)")

        if not main_entity_var_name: # No agents defined
            script_lines.append("    print('No agents defined in Agentfile.')")


        script_lines.extend([
            "",
            'if __name__ == "__main__":',
            "    main()",
        ])

        return "\n".join(script_lines)

    def get_requirements(self) -> List[str]:
        """Get requirements for Agno framework with enhanced tool support."""
        requirements = ["agno>=1.6.0"]

        # Add model-specific requirements
        all_models = set()
        if self.config.default_model:
            all_models.add(self.config.default_model)

        # Collect all agent models
        for agent in self.config.agents.values():
            if agent.model:
                all_models.add(agent.model)

        # Add requirements based on model types
        for model in all_models:
            model_lower = model.lower()
            if "anthropic" in model_lower or "claude" in model_lower:
                requirements.append("anthropic")
            elif "openai" in model_lower or "gpt" in model_lower:
                requirements.append("openai")
            elif "groq" in model_lower:
                requirements.append("groq")
            elif "/" in model:
                # Custom OpenAI-like model - add openai for OpenAILike class
                requirements.append("openai")
                # Add specific provider requirements if known
                provider = model.split("/")[0].lower()
                if provider == "groq":
                    requirements.append("groq")
                elif provider == "together":
                    requirements.append("together")
                elif provider == "anthropic":
                    requirements.append("anthropic")
            else:
                # Default case - use OpenAILike
                requirements.append("openai")
                requirements.append("anthropic")

        # Add tool-specific requirements based on servers
        tool_requirements = {
            # Search and web tools
            "web_search": ["duckduckgo-search"],
            "search": ["duckduckgo-search"],
            "browser": ["duckduckgo-search"],
            "google": ["google-search-results"],
            # Finance tools
            "finance": ["yfinance"],
            "yfinance": ["yfinance"],
            "stock": ["yfinance"],
            # File and system tools
            "file": [],  # Built into agno
            "filesystem": [],  # Built into agno
            "shell": [],  # Built into agno
            "python": [],  # Built into agno
            # Database tools
            "postgres": ["psycopg2-binary", "sqlalchemy"],
            "sqlite": ["sqlalchemy"],
            "database": ["sqlalchemy"],
            # Communication tools
            "email": ["smtplib"],  # Usually built-in
            "slack": ["slack-sdk"],
            "discord": ["discord.py"],
            # Advanced features
            "knowledge": ["lancedb", "tantivy"],
            "vector": ["lancedb", "tantivy"],
            "storage": ["sqlalchemy"],
            "memory": ["sqlalchemy"],
        }

        # Check global MCP servers
        for server_name in self.config.servers.keys():
            server_reqs = tool_requirements.get(server_name, [])
            requirements.extend(server_reqs)

        # Check individual agent servers
        for agent in self.config.agents.values():
            for server_name in agent.servers:
                server_reqs = tool_requirements.get(server_name, [])
                requirements.extend(server_reqs)

        # Always include core advanced features
        requirements.extend([
            # Core MCP support
            "mcp",
            # Environment file support
            "python-dotenv",
            # Optional but commonly used packages
            "sqlalchemy",  # For storage and memory
            "lancedb",     # For knowledge and vector databases
            "tantivy",     # For hybrid search
        ])

        # Multi-agent scenarios get additional dependencies
        if len(self.config.agents) > 1:
            requirements.extend([
                "asyncio",  # Usually built-in but explicit for clarity
            ])

        return requirements

    def generate_config_files(self) -> None:
        """Generate Agno-specific configuration files."""
        self._ensure_output_dir()
        self._generate_env_file()

    def _generate_env_file(self):
        """Generate .env template file for Agno framework."""
        env_lines = [
            "# Agno Environment Configuration",
            "# WARNING: Keep this file secure and never commit to version control",
            "",
            "# API Keys - uncomment and add your keys",
        ]

        # Add environment variables for custom model providers
        custom_providers = self.get_custom_model_providers()
        if custom_providers:
            env_lines.extend(["", "# Custom Model Provider Configuration"])
            for provider in sorted(custom_providers):
                provider_upper = provider.upper()
                env_lines.extend([
                    f"# {provider_upper}_API_KEY=your-{provider}-api-key",
                    f"# {provider_upper}_BASE_URL=your-{provider}-base-url",
                ])

        # Process secrets to generate environment variables
        for secret in self.config.secrets:
            if isinstance(secret, str):
                if secret in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", "GOOGLE_API_KEY"]:
                    env_lines.append(f"# {secret}=your-key-here")
                else:
                    env_lines.append(f"# {secret}=your-value-here")
            elif hasattr(secret, 'value'):
                # SecretValue with inline value
                env_lines.append(f"{secret.name}={secret.value}")
            elif hasattr(secret, 'values'):
                # SecretContext with multiple key-value pairs
                env_lines.append(f"# {secret.name.upper()} configuration")
                for key, value in secret.values.items():
                    env_lines.append(f"{secret.name.upper()}_{key}={value}")

        env_file = self.output_dir / ".env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(env_lines) + "\n")

    def get_dockerfile_config_lines(self) -> List[str]:
        """Get Agno-specific Dockerfile configuration lines."""
        return ["COPY .env ."]
