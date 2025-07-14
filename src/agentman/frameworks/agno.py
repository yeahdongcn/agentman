"""Agno framework implementation for AgentMan."""

from typing import List

from .base import BaseFramework


class AgnoFramework(BaseFramework):
    """Framework implementation for Agno."""

    def build_agent_content(self) -> str:
        """Build the Python agent file content for Agno framework."""
        lines = []

        # Determine if we need advanced features
        has_multiple_agents = len(self.config.agents) > 1
        has_servers = bool(self.config.servers)

        # Enhanced imports based on features needed
        imports = [
            "import os",
            "from agno.agent import Agent",
        ]

        # Add dotenv import for loading .env files
        imports.append("from dotenv import load_dotenv")
        imports.append("")
        imports.append("# Load environment variables from .env file")
        imports.append("load_dotenv()")
        imports.append("")

        # Model imports
        default_model = self.config.default_model or ""
        if "anthropic" in default_model.lower() or "claude" in default_model.lower():
            imports.append("from agno.models.anthropic import Claude")
        elif "openai" in default_model.lower() or "gpt" in default_model.lower():
            imports.append("from agno.models.openai import OpenAILike")
        elif "/" in default_model:
            # Custom model with provider prefix (e.g., "ollama/llama3", "groq/mixtral")
            imports.append("from agno.models.openai import OpenAILike")

        # Check agent models to determine what imports we need
        for agent in self.config.agents.values():
            agent_model = agent.model or default_model
            if agent_model:
                if "anthropic" in agent_model.lower() or "claude" in agent_model.lower():
                    if "from agno.models.anthropic import Claude" not in imports:
                        imports.append("from agno.models.anthropic import Claude")
                elif "openai" in agent_model.lower() or "gpt" in agent_model.lower():
                    if "from agno.models.openai import OpenAILike" not in imports:
                        imports.append("from agno.models.openai import OpenAILike")
                elif "/" in agent_model:
                    # Custom model with provider prefix
                    if "from agno.models.openai import OpenAILike" not in imports:
                        imports.append("from agno.models.openai import OpenAILike")

        if not any("anthropic" in imp or "openai" in imp for imp in imports):
            # Default to both if model is not specified or unclear
            imports.extend(
                [
                    "from agno.models.openai import OpenAILike",
                    "from agno.models.anthropic import Claude",
                ]
            )

        # Tool imports based on servers
        tool_imports = []
        if has_servers:
            # Map server types to appropriate tools
            for server_name, _ in self.config.servers.items():
                if server_name in ["web_search", "search", "browser"]:
                    tool_imports.append("from agno.tools.duckduckgo import DuckDuckGoTools")
                elif server_name in ["finance", "yfinance", "stock"]:
                    tool_imports.append("from agno.tools.yfinance import YFinanceTools")
                elif server_name in ["file", "filesystem"]:
                    tool_imports.append("from agno.tools.file import FileTools")
                elif server_name in ["shell", "terminal"]:
                    tool_imports.append("from agno.tools.shell import ShellTools")
                elif server_name in ["python", "code"]:
                    tool_imports.append("from agno.tools.python import PythonTools")

        # Remove duplicates and add to imports
        for tool_import in sorted(set(tool_imports)):
            imports.append(tool_import)

        # Team imports if multiple agents
        if has_multiple_agents:
            imports.append("from agno.team.team import Team")

        # Advanced feature imports (always include for better examples)
        imports.extend(
            [
                "from agno.tools.reasoning import ReasoningTools",
                "# Optional: Uncomment for advanced features",
                "# from agno.storage.sqlite import SqliteStorage",
                "# from agno.memory.v2.db.sqlite import SqliteMemoryDb",
                "# from agno.memory.v2.memory import Memory",
                "# from agno.knowledge.url import UrlKnowledge",
                "# from agno.vectordb.lancedb import LanceDb",
            ]
        )

        lines.extend(imports + [""])

        # Generate agents with enhanced capabilities
        agent_vars = []
        for agent in self.config.agents.values():
            agent_var = f"{agent.name.lower().replace('-', '_')}_agent"
            agent_vars.append((agent_var, agent))

            lines.extend(
                [
                    f"# Agent: {agent.name}",
                    f"{agent_var} = Agent(",
                    f'    name="{agent.name}",',
                    f'    instructions="""{agent.instruction}""",',
                ]
            )

            # Add role if we have multiple agents
            if has_multiple_agents:
                role = f"Handle {agent.name.lower().replace('-', ' ')} requests"
                lines.append(f'    role="{role}",')

            # Add model
            model = agent.model or self.config.default_model
            if model:
                model_code = self._generate_model_code(model)
                lines.append(f'    {model_code}')

            # Enhanced tools based on servers
            tools = []
            if agent.servers:
                for server_name in agent.servers:
                    if server_name in ["web_search", "search", "browser"]:
                        tools.append("DuckDuckGoTools()")
                    elif server_name in ["finance", "yfinance", "stock"]:
                        tools.append("YFinanceTools(stock_price=True, analyst_recommendations=True)")
                    elif server_name in ["file", "filesystem"]:
                        tools.append("FileTools()")
                    elif server_name in ["shell", "terminal"]:
                        tools.append("ShellTools()")
                    elif server_name in ["python", "code"]:
                        tools.append("PythonTools()")

            # Always add reasoning tools for better performance
            tools.append("ReasoningTools(add_instructions=True)")

            if tools:
                tools_str = ", ".join(tools)
                lines.append(f'    tools=[{tools_str}],')

            # Add other properties
            if not agent.use_history:
                lines.append("    add_history_to_messages=False,")
            else:
                lines.append("    add_history_to_messages=True,")

            if agent.human_input:
                lines.append("    human_input=True,")

            # Enhanced agent properties
            lines.extend(
                [
                    "    markdown=True,",
                    "    add_datetime_to_instructions=True,",
                    "    # Optional: Enable advanced features",
                    "    # storage=SqliteStorage(table_name='agent_sessions', db_file='tmp/agent.db'),",
                    "    # memory=Memory(model=Claude(id='claude-sonnet-4-20250514'), db=SqliteMemoryDb()),",
                    "    # enable_agentic_memory=True,",
                    ")",
                    "",
                ]
            )

        # Team creation for multi-agent scenarios
        if has_multiple_agents:
            team_name = "AgentTeam"
            lines.extend(
                [
                    "# Multi-Agent Team",
                    f"{team_name.lower()} = Team(",
                    f'    name="{team_name}",',
                    "    mode='coordinate',  # or 'sequential' for ordered execution",
                ]
            )

            # Use the first agent's model for team coordination
            if agent_vars:
                first_model = agent_vars[0][1].model or self.config.default_model
                model_code = self._generate_model_code(first_model)
                lines.append(f'    {model_code}')

            # Add all agents as team members
            member_vars = [var for var, _ in agent_vars]
            members_str = ", ".join(member_vars)
            lines.append(f'    members=[{members_str}],')

            lines.extend(
                [
                    "    tools=[ReasoningTools(add_instructions=True)],",
                    "    instructions=[",
                    "        'Collaborate to provide comprehensive responses',",
                    "        'Consider multiple perspectives and expertise areas',",
                    "        'Present findings in a structured, easy-to-follow format',",
                    "        'Only output the final consolidated response',",
                    "    ],",
                    "    markdown=True,",
                    "    show_members_responses=True,",
                    "    enable_agentic_context=True,",
                    "    add_datetime_to_instructions=True,",
                    "    success_criteria='The team has provided a complete and accurate response.',",
                    ")",
                    "",
                ]
            )

        # Main function and execution logic
        lines.extend(self._generate_main_function(has_multiple_agents, agent_vars))

        lines.extend(
            [
                "",
                'if __name__ == "__main__":',
                "    main()",
            ]
        )

        return "\n".join(lines)

    def _generate_model_code(self, model: str) -> str:
        """Generate the appropriate model instantiation code for Agno framework."""
        if not model:
            return 'model=Claude(id="anthropic/claude-3-sonnet-20241022"),'

        model_lower = model.lower()

        # Anthropic models
        if "anthropic" in model_lower or "claude" in model_lower:
            return f'model=Claude(id="{model}"),'

        # OpenAI models
        if "openai" in model_lower or "gpt" in model_lower:
            model_code = 'model=OpenAILike(\n'
            model_code += f'        id="{model}",\n'
            model_code += '        api_key=os.getenv("OPENAI_API_KEY"),\n'
            model_code += '        base_url=os.getenv("OPENAI_BASE_URL"),\n'
            model_code += '    ),'
            return model_code

        # Custom OpenAI-like models (with provider prefix)
        if "/" in model:
            provider, _ = model.split("/", 1)
            provider_upper = provider.upper()

            # Generate OpenAILike model with custom configuration
            model_code = 'model=OpenAILike(\n'
            model_code += f'        id="{model}",\n'
            model_code += f'        api_key=os.getenv("{provider_upper}_API_KEY"),\n'
            model_code += f'        base_url=os.getenv("{provider_upper}_BASE_URL"),\n'
            model_code += '    ),'
            return model_code

        # Default to OpenAILike for unrecognized patterns
        # Check if we have OpenAI-like environment variables configured
        has_openai_config = any(
            (isinstance(secret, str) and secret in ["OPENAI_API_KEY", "OPENAI_BASE_URL"])
            or (hasattr(secret, 'name') and secret.name in ["OPENAI_API_KEY", "OPENAI_BASE_URL"])
            for secret in self.config.secrets
        )

        if has_openai_config:
            # Use OpenAI environment variables for custom models
            model_code = 'model=OpenAILike(\n'
            model_code += f'        id="{model}",\n'
            model_code += '        api_key=os.getenv("OPENAI_API_KEY"),\n'
            model_code += '        base_url=os.getenv("OPENAI_BASE_URL"),\n'
            model_code += '    ),'
            return model_code

        return f'model=OpenAILike(id="{model}"),'

    def _generate_main_function(self, has_multiple_agents: bool, agent_vars: list) -> List[str]:
        """Generate the main function and execution logic."""
        lines = ["def main() -> None:"]

        # Handle prompt file loading
        if self.has_prompt_file:
            lines.extend(
                [
                    "    # Check if prompt.txt exists and load its content",
                    "    import os",
                    "    prompt_file = 'prompt.txt'",
                    "    if os.path.exists(prompt_file):",
                    "        with open(prompt_file, 'r', encoding='utf-8') as f:",
                    "            prompt_content = f.read().strip()",
                ]
            )

        # Enhanced execution logic
        if has_multiple_agents:
            # Use team for multi-agent scenarios
            team_name = "AgentTeam"
            if self.has_prompt_file:
                lines.extend(
                    [
                        "        if prompt_content:",
                        f"            {team_name.lower()}.print_response(",
                        "                prompt_content,",
                        "                stream=True,",
                        "                show_full_reasoning=True,",
                        "                stream_intermediate_steps=True,",
                        "            )",
                        "        else:",
                        f"            {team_name.lower()}.print_response(",
                        "                'Hello! How can our team help you today?',",
                        "                stream=True,",
                        "                show_full_reasoning=True,",
                        "                stream_intermediate_steps=True,",
                        "            )",
                        "    else:",
                        f"        {team_name.lower()}.print_response(",
                        "            'Hello! How can our team help you today?',",
                        "            stream=True,",
                        "            show_full_reasoning=True,",
                        "            stream_intermediate_steps=True,",
                        "        )",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"    {team_name.lower()}.print_response(",
                        "        'Hello! How can our team help you today?',",
                        "        stream=True,",
                        "        show_full_reasoning=True,",
                        "        stream_intermediate_steps=True,",
                        "    )",
                    ]
                )

        elif agent_vars:
            # Single agent scenario with enhanced features
            primary_agent_var, _ = agent_vars[0]
            if self.has_prompt_file:
                lines.extend(
                    [
                        "        if prompt_content:",
                        f"            {primary_agent_var}.print_response(",
                        "                prompt_content,",
                        "                stream=True,",
                        "                show_full_reasoning=True,",
                        "                stream_intermediate_steps=True,",
                        "            )",
                        "        else:",
                        f"            {primary_agent_var}.print_response(",
                        "                'Hello! How can I help you today?',",
                        "                stream=True,",
                        "                show_full_reasoning=True,",
                        "                stream_intermediate_steps=True,",
                        "            )",
                        "    else:",
                        f"        {primary_agent_var}.print_response(",
                        "            'Hello! How can I help you today?',",
                        "            stream=True,",
                        "            show_full_reasoning=True,",
                        "            stream_intermediate_steps=True,",
                        "        )",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"    {primary_agent_var}.print_response(",
                        "        'Hello! How can I help you today?',",
                        "        stream=True,",
                        "        show_full_reasoning=True,",
                        "        stream_intermediate_steps=True,",
                        "    )",
                    ]
                )
        else:
            lines.extend(
                [
                    "    print('No agents defined')",
                ]
            )

        return lines

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
        requirements.extend(
            [
                # Core MCP support
                "mcp",
                # Environment file support
                "python-dotenv",
                # Optional but commonly used packages
                "sqlalchemy",  # For storage and memory
                "lancedb",  # For knowledge and vector databases
                "tantivy",  # For hybrid search
            ]
        )

        # Multi-agent scenarios get additional dependencies
        if len(self.config.agents) > 1:
            requirements.extend(
                [
                    "asyncio",  # Usually built-in but explicit for clarity
                ]
            )

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
                env_lines.extend(
                    [
                        f"# {provider_upper}_API_KEY=your-{provider}-api-key",
                        f"# {provider_upper}_BASE_URL=your-{provider}-base-url",
                    ]
                )

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
