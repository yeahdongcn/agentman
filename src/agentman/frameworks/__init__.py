"""Framework support for AgentMan."""

from .base import BaseFramework
from .agno import AgnoFramework
from .fast_agent import FastAgentFramework

__all__ = ["BaseFramework", "AgnoFramework", "FastAgentFramework"]
