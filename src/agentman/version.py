"""Version information for Agentman."""


def version():
    """Return the current version of Agentman."""
    return "0.1.6"


def print_version(args):
    """Print the version information."""
    if args.quiet:
        print(version())
    else:
        print(f"agentman version {version()}")
