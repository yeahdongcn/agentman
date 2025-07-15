"""Framework support for AgentMan."""

from .agno import AgnoFramework
from .base import BaseFramework
from .fast_agent import FastAgentFramework

__all__ = ["BaseFramework", "AgnoFramework", "FastAgentFramework"]
