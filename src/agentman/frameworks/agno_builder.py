"""Agno framework builder using structured configuration."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path


@dataclass
class AgnoModelConfig:
    """Configuration for Agno model instances."""

    model_type: str  # "claude", "openai", "custom"
    model_id: str
    provider: Optional[str] = None
    api_key_env: Optional[str] = None
    base_url_env: Optional[str] = None


@dataclass
class AgnoToolConfig:
    """Configuration for Agno tool instances."""

    tool_class: str
    import_path: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgnoAgentConfig:
    """Configuration for Agno agent instances."""

    name: str
    variable_name: str
    instruction: str
    role: Optional[str] = None
    model_config: Optional[AgnoModelConfig] = None
    tools: List[AgnoToolConfig] = field(default_factory=list)
    use_history: bool = True
    human_input: bool = False
    enhanced_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgnoTeamConfig:
    """Configuration for Agno team instances."""

    name: str
    variable_name: str
    mode: str = "coordinate"
    agent_variables: List[str] = field(default_factory=list)
    model_config: Optional[AgnoModelConfig] = None
    tools: List[AgnoToolConfig] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    enhanced_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgnoFrameworkConfig:
    """Structured configuration for Agno framework."""

    agents: List[AgnoAgentConfig] = field(default_factory=list)
    team: Optional[AgnoTeamConfig] = None
    has_prompt_file: bool = False
    required_imports: Set[str] = field(default_factory=set)
    tool_imports: Set[str] = field(default_factory=set)


class AgnoCodeGenerator:
    """Generate Agno code using structured configuration."""

    def __init__(self, config: AgnoFrameworkConfig):
        self.config = config

    def generate_imports(self) -> List[str]:
        """Generate import statements based on configuration."""
        imports = [
            "import os",
            "from agno.agent import Agent",
            "",
            "# Load environment variables from .env file",
            "from dotenv import load_dotenv",
            "load_dotenv()",
            "",
        ]

        # Add model imports
        model_imports = set()
        for agent in self.config.agents:
            if agent.model_config:
                if agent.model_config.model_type == "claude":
                    model_imports.add("from agno.models.anthropic import Claude")
                elif agent.model_config.model_type in ["openai", "custom"]:
                    model_imports.add("from agno.models.openai import OpenAILike")

        if self.config.team and self.config.team.model_config:
            if self.config.team.model_config.model_type == "claude":
                model_imports.add("from agno.models.anthropic import Claude")
            elif self.config.team.model_config.model_type in ["openai", "custom"]:
                model_imports.add("from agno.models.openai import OpenAILike")

        # Add default imports if no specific models found
        if not model_imports:
            model_imports.update(
                [
                    "from agno.models.openai import OpenAILike",
                    "from agno.models.anthropic import Claude",
                ]
            )

        imports.extend(sorted(model_imports))

        # Add tool imports
        if self.config.tool_imports:
            imports.extend(sorted(self.config.tool_imports))

        # Add team import if needed
        if self.config.team:
            imports.append("from agno.team.team import Team")

        # Add reasoning tools import (always included)
        imports.extend(
            [
                "from agno.tools.reasoning import ReasoningTools",
                "# Optional: Uncomment for advanced features",
                "# from agno.storage.sqlite import SqliteStorage",
                "# from agno.memory.v2.db.sqlite import SqliteMemoryDb",
                "# from agno.memory.v2.memory import Memory",
                "# from agno.knowledge.url import UrlKnowledge",
                "# from agno.vectordb.lancedb import LanceDb",
                "",
            ]
        )

        return imports

    def generate_agent_definitions(self) -> List[str]:
        """Generate agent definition code."""
        lines = []

        for agent in self.config.agents:
            lines.extend(self._generate_single_agent(agent))
            lines.append("")

        return lines

    def generate_team_definition(self) -> List[str]:
        """Generate team definition if needed."""
        if not self.config.team:
            return []

        lines = [
            "# Multi-Agent Team",
            f"{self.config.team.variable_name} = Team(",
            f'    name="{self.config.team.name}",',
            f"    mode='{self.config.team.mode}',  # or 'sequential' for ordered execution",
        ]

        # Add model configuration
        if self.config.team.model_config:
            model_code = self._generate_model_instantiation(self.config.team.model_config)
            lines.append(f"    {model_code}")

        # Add team members
        if self.config.team.agent_variables:
            members_str = ", ".join(self.config.team.agent_variables)
            lines.append(f"    members=[{members_str}],")

        # Add tools
        if self.config.team.tools:
            tools_list = [self._generate_tool_instantiation(tool) for tool in self.config.team.tools]
            tools_str = ", ".join(tools_list)
            lines.append(f"    tools=[{tools_str}],")
        else:
            lines.append("    tools=[ReasoningTools(add_instructions=True)],")

        # Add instructions
        if self.config.team.instructions:
            lines.append("    instructions=[")
            for instruction in self.config.team.instructions:
                lines.append(f'        "{instruction}",')
            lines.append("    ],")
        else:
            lines.extend(
                [
                    "    instructions=[",
                    "        'Collaborate to provide comprehensive responses',",
                    "        'Consider multiple perspectives and expertise areas',",
                    "        'Present findings in a structured, easy-to-follow format',",
                    "        'Only output the final consolidated response',",
                    "    ],",
                ]
            )

        # Add enhanced properties
        for key, value in self.config.team.enhanced_properties.items():
            if isinstance(value, str):
                lines.append(f'    {key}="{value}",')
            else:
                lines.append(f"    {key}={value},")

        # Add default enhanced properties
        lines.extend(
            [
                "    markdown=True,",
                "    show_members_responses=True,",
                "    enable_agentic_context=True,",
                "    add_datetime_to_instructions=True,",
                "    success_criteria='The team has provided a complete and accurate response.',",
                ")",
                "",
            ]
        )

        return lines

    def generate_main_function(self) -> List[str]:
        """Generate main function and execution logic."""
        lines = ["def main() -> None:"]

        # Handle prompt file loading
        if self.config.has_prompt_file:
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

        # Determine execution target
        if self.config.team:
            target_var = self.config.team.variable_name
        elif self.config.agents:
            target_var = self.config.agents[0].variable_name
        else:
            target_var = None

        if target_var:
            if self.config.has_prompt_file:
                lines.extend(
                    [
                        "        if prompt_content:",
                        f"            {target_var}.print_response(",
                        "                prompt_content,",
                        "                stream=True,",
                        "                show_full_reasoning=True,",
                        "                stream_intermediate_steps=True,",
                        "            )",
                        "        else:",
                        f"            {target_var}.print_response(",
                        "                'Hello! How can I help you today?',",
                        "                stream=True,",
                        "                show_full_reasoning=True,",
                        "                stream_intermediate_steps=True,",
                        "            )",
                        "    else:",
                        f"        {target_var}.print_response(",
                        "            'Hello! How can I help you today?',",
                        "            stream=True,",
                        "            show_full_reasoning=True,",
                        "            stream_intermediate_steps=True,",
                        "        )",
                    ]
                )
            else:
                greeting = (
                    "'Hello! How can our team help you today?'"
                    if self.config.team
                    else "'Hello! How can I help you today?'"
                )
                lines.extend(
                    [
                        f"    {target_var}.print_response(",
                        f"        {greeting},",
                        "        stream=True,",
                        "        show_full_reasoning=True,",
                        "        stream_intermediate_steps=True,",
                        "    )",
                    ]
                )
        else:
            lines.append("    print('No agents defined')")

        return lines

    def generate_entry_point(self) -> List[str]:
        """Generate script entry point."""
        return [
            "",
            'if __name__ == "__main__":',
            "    main()",
        ]

    def generate_complete_code(self) -> str:
        """Generate the complete Agno Python code."""
        lines = []

        lines.extend(self.generate_imports())
        lines.extend(self.generate_agent_definitions())
        lines.extend(self.generate_team_definition())
        lines.extend(self.generate_main_function())
        lines.extend(self.generate_entry_point())

        return "\n".join(lines)

    def _generate_single_agent(self, agent: AgnoAgentConfig) -> List[str]:
        """Generate code for a single agent."""
        lines = [
            f"# Agent: {agent.name}",
            f"{agent.variable_name} = Agent(",
            f'    name="{agent.name}",',
            f'    instructions="""{agent.instruction}""",',
        ]

        # Add role if specified
        if agent.role:
            lines.append(f'    role="{agent.role}",')

        # Add model configuration
        if agent.model_config:
            model_code = self._generate_model_instantiation(agent.model_config)
            lines.append(f"    {model_code}")

        # Add tools
        if agent.tools:
            tools_list = [self._generate_tool_instantiation(tool) for tool in agent.tools]
            # Always add reasoning tools
            tools_list.append("ReasoningTools(add_instructions=True)")
            tools_str = ", ".join(tools_list)
            lines.append(f"    tools=[{tools_str}],")
        else:
            lines.append("    tools=[ReasoningTools(add_instructions=True)],")

        # Add history setting
        lines.append(f"    add_history_to_messages={str(agent.use_history)},")

        # Add human input if enabled
        if agent.human_input:
            lines.append("    human_input=True,")

        # Add enhanced properties
        for key, value in agent.enhanced_properties.items():
            if isinstance(value, str):
                lines.append(f'    {key}="{value}",')
            else:
                lines.append(f"    {key}={value},")

        # Add default enhanced properties
        lines.extend(
            [
                "    markdown=True,",
                "    add_datetime_to_instructions=True,",
                "    # Optional: Enable advanced features",
                "    # storage=SqliteStorage(table_name='agent_sessions', db_file='tmp/agent.db'),",
                "    # memory=Memory(model=Claude(id='claude-sonnet-4-20250514'), db=SqliteMemoryDb()),",
                "    # enable_agentic_memory=True,",
                ")",
            ]
        )

        return lines

    def _generate_model_instantiation(self, model_config: AgnoModelConfig) -> str:
        """Generate model instantiation code."""
        if model_config.model_type == "claude":
            return f'model=Claude(id="{model_config.model_id}"),'
        elif model_config.model_type == "openai":
            return (
                'model=OpenAILike(\n'
                f'        id="{model_config.model_id}",\n'
                f'        api_key=os.getenv("{model_config.api_key_env or "OPENAI_API_KEY"}"),\n'
                f'        base_url=os.getenv("{model_config.base_url_env or "OPENAI_BASE_URL"}"),\n'
                '    ),'
            )
        elif model_config.model_type == "custom":
            api_key_env = model_config.api_key_env or f"{model_config.provider.upper()}_API_KEY"
            base_url_env = model_config.base_url_env or f"{model_config.provider.upper()}_BASE_URL"
            return (
                'model=OpenAILike(\n'
                f'        id="{model_config.model_id}",\n'
                f'        api_key=os.getenv("{api_key_env}"),\n'
                f'        base_url=os.getenv("{base_url_env}"),\n'
                '    ),'
            )
        else:
            return f'model=OpenAILike(id="{model_config.model_id}"),'

    def _generate_tool_instantiation(self, tool_config: AgnoToolConfig) -> str:
        """Generate tool instantiation code."""
        if tool_config.params:
            params_str = ", ".join(f"{k}={v}" for k, v in tool_config.params.items())
            return f"{tool_config.tool_class}({params_str})"
        else:
            return f"{tool_config.tool_class}()"


class AgnoConfigBuilder:
    """Builder for creating AgnoFrameworkConfig from agentfile configuration."""

    def __init__(self):
        self.server_tool_mapping = {
            "web_search": AgnoToolConfig("DuckDuckGoTools", "from agno.tools.duckduckgo import DuckDuckGoTools"),
            "search": AgnoToolConfig("DuckDuckGoTools", "from agno.tools.duckduckgo import DuckDuckGoTools"),
            "browser": AgnoToolConfig("DuckDuckGoTools", "from agno.tools.duckduckgo import DuckDuckGoTools"),
            "finance": AgnoToolConfig(
                "YFinanceTools",
                "from agno.tools.yfinance import YFinanceTools",
                {"stock_price": True, "analyst_recommendations": True},
            ),
            "yfinance": AgnoToolConfig(
                "YFinanceTools",
                "from agno.tools.yfinance import YFinanceTools",
                {"stock_price": True, "analyst_recommendations": True},
            ),
            "stock": AgnoToolConfig(
                "YFinanceTools",
                "from agno.tools.yfinance import YFinanceTools",
                {"stock_price": True, "analyst_recommendations": True},
            ),
            "file": AgnoToolConfig("FileTools", "from agno.tools.file import FileTools"),
            "filesystem": AgnoToolConfig("FileTools", "from agno.tools.file import FileTools"),
            "shell": AgnoToolConfig("ShellTools", "from agno.tools.shell import ShellTools"),
            "terminal": AgnoToolConfig("ShellTools", "from agno.tools.shell import ShellTools"),
            "python": AgnoToolConfig("PythonTools", "from agno.tools.python import PythonTools"),
            "code": AgnoToolConfig("PythonTools", "from agno.tools.python import PythonTools"),
        }

    def build_model_config(self, model: str) -> AgnoModelConfig:
        """Build model configuration from model string."""
        if not model:
            return AgnoModelConfig("claude", "anthropic/claude-3-sonnet-20241022")

        model_lower = model.lower()

        if "anthropic" in model_lower or "claude" in model_lower:
            return AgnoModelConfig("claude", model)
        elif "openai" in model_lower or "gpt" in model_lower:
            return AgnoModelConfig("openai", model, api_key_env="OPENAI_API_KEY", base_url_env="OPENAI_BASE_URL")
        elif "/" in model:
            provider, model_name = model.split("/", 1)
            return AgnoModelConfig(
                "custom",
                model,
                provider=provider,
                api_key_env=f"{provider.upper()}_API_KEY",
                base_url_env=f"{provider.upper()}_BASE_URL",
            )
        else:
            return AgnoModelConfig("openai", model, api_key_env="OPENAI_API_KEY", base_url_env="OPENAI_BASE_URL")

    def build_tools_for_servers(self, servers: List[str]) -> List[AgnoToolConfig]:
        """Build tool configurations for given servers."""
        tools = []
        for server in servers:
            if server in self.server_tool_mapping:
                tools.append(self.server_tool_mapping[server])
        return tools

    def get_tool_imports(self, tools: List[AgnoToolConfig]) -> Set[str]:
        """Get import statements for tools."""
        return {tool.import_path for tool in tools}
