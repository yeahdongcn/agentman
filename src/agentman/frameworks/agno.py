"""Agno framework implementation for AgentMan."""

from typing import List

from .base import BaseFramework
from .agno_builder import AgnoFrameworkConfig, AgnoCodeGenerator, AgnoConfigBuilder, AgnoAgentConfig, AgnoTeamConfig


class AgnoFramework(BaseFramework):
    """Framework implementation for Agno."""

    def build_agent_content(self) -> str:
        """Build the Python agent file content for Agno framework."""

        # Create configuration builder
        builder = AgnoConfigBuilder()

        # Create main framework configuration
        framework_config = AgnoFrameworkConfig(has_prompt_file=self.has_prompt_file)

        # Build agent configurations
        agent_vars = []
        for agent in self.config.agents.values():
            agent_var = f"{agent.name.lower().replace('-', '_')}_agent"
            agent_vars.append(agent_var)

            # Build model configuration
            model = agent.model or self.config.default_model
            model_config = builder.build_model_config(model)

            # Build tools
            tools = builder.build_tools_for_servers(agent.servers)

            # Add tool imports
            framework_config.tool_imports.update(builder.get_tool_imports(tools))

            # Create role if multiple agents
            role = None
            if len(self.config.agents) > 1:
                role = f"Handle {agent.name.lower().replace('-', ' ')} requests"

            # Create agent configuration
            agent_config = AgnoAgentConfig(
                name=agent.name,
                variable_name=agent_var,
                instruction=agent.instruction,
                role=role,
                model_config=model_config,
                tools=tools,
                use_history=agent.use_history,
                human_input=agent.human_input,
            )

            framework_config.agents.append(agent_config)

        # Create team if multiple agents
        if len(self.config.agents) > 1:
            team_name = "agentteam"

            # Use first agent's model for team coordination
            team_model = None
            if framework_config.agents:
                team_model = framework_config.agents[0].model_config

            team_config = AgnoTeamConfig(
                name="AgentTeam",
                variable_name=team_name,
                mode="coordinate",
                agent_variables=agent_vars,
                model_config=team_model,
            )

            framework_config.team = team_config

        # Generate code using structured builder
        generator = AgnoCodeGenerator(framework_config)
        return generator.generate_complete_code()

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
