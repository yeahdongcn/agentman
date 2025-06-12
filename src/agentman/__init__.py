"""Agentman package for building MCP agents from Agentfiles."""

import sys

from agentman.cli import HelpException, init_cli, print_version
from agentman.common import perror

assert sys.version_info >= (3, 10), "Python 3.10 or greater is required."

__all__ = ["perror", "init_cli", "print_version", "HelpException"]
