"""Common utilities for Agentman."""

import sys


def perror(*args, **kwargs):
    """Print error message to stderr.

    Args:
        *args: Arguments to pass to print()
        **kwargs: Keyword arguments to pass to print()
    """
    print(*args, file=sys.stderr, **kwargs)
