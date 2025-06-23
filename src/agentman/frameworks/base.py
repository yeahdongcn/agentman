"""Base framework interface for AgentMan."""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from agentman.agentfile_parser import AgentfileConfig


class BaseFramework(ABC):
    """Base class for framework implementations."""

    def __init__(self, config: AgentfileConfig, output_dir: Path, source_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.source_dir = source_dir
        self.has_prompt_file = (source_dir / "prompt.txt").exists()

    @abstractmethod
    def build_agent_content(self) -> str:
        """Build the main agent file content."""
        pass

    @abstractmethod
    def get_requirements(self) -> List[str]:
        """Get framework-specific requirements."""
        pass

    @abstractmethod
    def generate_config_files(self) -> None:
        """Generate framework-specific configuration files."""
        pass

    @abstractmethod
    def get_dockerfile_config_lines(self) -> List[str]:
        """Get framework-specific Dockerfile configuration lines."""
        pass

    def get_custom_model_providers(self) -> set:
        """Extract custom model providers from all models used."""
        providers = set()

        # Check default model
        if self.config.default_model and "/" in self.config.default_model:
            provider = self.config.default_model.split("/")[0]
            # Skip official providers that don't need custom base URLs
            if provider.lower() not in ["openai", "anthropic"]:
                providers.add(provider)

        # Check agent models
        for agent in self.config.agents.values():
            if agent.model and "/" in agent.model:
                provider = agent.model.split("/")[0]
                # Skip official providers that don't need custom base URLs
                if provider.lower() not in ["openai", "anthropic"]:
                    providers.add(provider)

        return providers

    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
