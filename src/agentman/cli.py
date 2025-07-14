"""Command-line interface for Agentman."""

import argparse
import errno
import subprocess
import sys
from pathlib import Path

from agentman.agent_builder import build_from_agentfile
from agentman.common import perror
from agentman.version import print_version


class HelpException(Exception):
    """Exception raised to trigger help display."""


class BuildArgs:
    """Arguments for the build command.

    This class serves as a placeholder for build-related arguments
    and may be expanded in the future to include argument validation
    and processing logic.
    """

    def __init__(self):
        """Initialize BuildArgs."""


def resolve_context_path(path):
    """Resolve and validate the build context path."""
    context_path = Path(path).resolve()
    if not context_path.exists():
        perror(f"Build context path not found: {context_path}")
        sys.exit(1)
    if context_path.is_file():
        context_path = context_path.parent
    return context_path


def safe_subprocess_run(cmd_args, check=True):
    """Safely run subprocess with validated arguments."""
    # Ensure all arguments are strings and properly escaped
    safe_args = []
    for arg in cmd_args:
        if not isinstance(arg, str):
            arg = str(arg)
        safe_args.append(arg)

    return subprocess.run(safe_args, check=check)


class ArgumentParserWithDefaults(argparse.ArgumentParser):
    """Argument parser with default value handling."""

    def add_argument(self, *args, help_text=None, default=None, completer=None, **kwargs):
        """Add an argument with help text and default value."""
        if help_text is not None:
            kwargs['help'] = help_text
        if default is not None and args[0] != '-h':
            kwargs['default'] = default
            if help_text is not None and help_text != "==SUPPRESS==":
                kwargs['help'] += f' (default: {default})'
        action = super().add_argument(*args, **kwargs)
        if completer is not None:
            action.completer = completer
        return action


def get_description():
    """Get the description for the CLI tool."""
    return """\
A tool for building and managing AI agents
"""


def configure_arguments(parser):
    """Configure the command-line arguments for the parser."""
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--debug",
        action="store_true",
        help="display debug messages",
    )
    verbosity_group.add_argument("--quiet", "-q", dest="quiet", action="store_true", help="reduce output.")


def create_argument_parser(description):
    """Create and configure the argument parser."""
    parser = ArgumentParserWithDefaults(
        prog="agentman",
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    configure_arguments(parser)
    return parser


def runtime_options(parser, command):
    """Configure runtime options for commands.

    Args:
        parser: The argument parser to add options to
        command: The command name (currently unused but reserved for future use)
    """
    # Runtime options are not yet implemented but reserved for future use
    # when we need command-specific runtime configurations


def post_parse_setup(args):
    """Perform post-parse setup operations.

    Args:
        args: Parsed command line arguments (currently unused but reserved)
    """
    # Post-parse setup is not yet implemented but reserved for future use
    # when we need to perform operations after argument parsing


def build_cli(args):
    """Build agent files from an Agentfile."""
    # Determine the build context path
    context_path = resolve_context_path(args.path)

    # Construct the Agentfile path relative to context
    agentfile_path = context_path / args.file

    if not agentfile_path.exists():
        perror(f"Agentfile not found: {agentfile_path}")
        sys.exit(1)

    # Determine output directory relative to context
    if args.output:
        output_dir = context_path / args.output
    else:
        output_dir = context_path / "agent"

    # Determine format hint
    format_hint = None
    if hasattr(args, 'from_yaml') and args.from_yaml:
        format_hint = "yaml"
    elif hasattr(args, 'format') and args.format:
        format_hint = args.format

    try:
        build_from_agentfile(str(agentfile_path), str(output_dir), format_hint)

        if args.build_docker:
            print("\n🐳 Building Docker image...")
            docker_cmd = ["docker", "build", "-t", args.tag, str(output_dir)]
            safe_subprocess_run(docker_cmd, check=True)
            print(f"✅ Docker image built: {args.tag}")

    except (subprocess.CalledProcessError, IOError, ValueError) as e:
        perror(f"Build failed: {e}")
        sys.exit(1)


def build_parser(subparsers):
    """Configure the build subcommand parser."""
    parser = subparsers.add_parser("build", help="Build an image from a Agentfile")
    parser.add_argument("-f", "--file", default="Agentfile", help="Name of the Agentfile")
    parser.add_argument("-o", "--output", help="Output directory for generated files (default: agent)")
    parser.add_argument("-t", "--tag", default="agent:latest", help="Name and optionally a tag for the Docker image")
    parser.add_argument(
        "--build-docker", action="store_true", help="Also build the Docker image after generating files"
    )
    parser.add_argument(
        "--format",
        choices=["dockerfile", "yaml"],
        help="Explicitly specify the Agentfile format (auto-detected by default)"
    )
    parser.add_argument(
        "--from-yaml",
        action="store_true",
        help="Build from YAML Agentfile format (same as --format yaml)"
    )
    parser.add_argument("path", nargs="?", default=".", help="Build context (directory or URL)")
    parser.usage = "agentman build [OPTIONS] PATH | URL | -"
    runtime_options(parser, "build")
    parser.set_defaults(func=build_cli)


def run_cli(args):
    """Run an agent from an Agentfile or existing image."""
    if args.from_agentfile:
        # Build first, then run
        # Determine the build context path
        context_path = resolve_context_path(args.path)

        # Construct the Agentfile path relative to context
        agentfile_path = context_path / args.file

        if not agentfile_path.exists():
            perror(f"Agentfile not found: {agentfile_path}")
            sys.exit(1)

        # Determine output directory relative to context
        if args.output:
            output_dir = context_path / args.output
        else:
            output_dir = context_path / "agent"

        # Determine format hint
        format_hint = None
        if hasattr(args, 'from_yaml') and args.from_yaml:
            format_hint = "yaml"
        elif hasattr(args, 'format') and args.format:
            format_hint = args.format

        try:
            print("🔨 Building agent files...")
            build_from_agentfile(str(agentfile_path), str(output_dir), format_hint)

            print("\n🐳 Building Docker image...")
            docker_cmd = ["docker", "build", "-t", args.tag, str(output_dir)]
            safe_subprocess_run(docker_cmd, check=True)

            print("\n🚀 Running agent container...")
            run_cmd = ["docker", "run"]

            # Add host.docker.internal mapping by default for localhost access
            run_cmd.extend(["--add-host", "host.docker.internal:host-gateway"])

            if args.interactive:
                run_cmd.extend(["-it"])

            if args.remove:
                run_cmd.append("--rm")

            if args.port:
                for port in args.port:
                    run_cmd.extend(["-p", port])

            if args.env:
                for env in args.env:
                    run_cmd.extend(["-e", env])

            if args.volume:
                for vol in args.volume:
                    run_cmd.extend(["-v", vol])

            run_cmd.append(args.tag)

            if args.command:
                run_cmd.extend(args.command)

            safe_subprocess_run(run_cmd, check=True)

        except (subprocess.CalledProcessError, IOError, ValueError) as e:
            perror(f"Run failed: {e}")
            sys.exit(1)
    else:
        # Run existing image
        print(f"🚀 Running agent container from image: {args.tag}")
        run_cmd = ["docker", "run"]

        # Add host.docker.internal mapping by default for localhost access
        run_cmd.extend(["--add-host", "host.docker.internal:host-gateway"])

        if args.interactive:
            run_cmd.extend(["-it"])

        if args.remove:
            run_cmd.append("--rm")

        if args.port:
            for port in args.port:
                run_cmd.extend(["-p", port])

        if args.env:
            for env in args.env:
                run_cmd.extend(["-e", env])

        if args.volume:
            for vol in args.volume:
                run_cmd.extend(["-v", vol])

        run_cmd.append(args.tag)

        if args.command:
            run_cmd.extend(args.command)

        try:
            safe_subprocess_run(run_cmd, check=True)
        except (subprocess.CalledProcessError, IOError, ValueError) as e:
            perror(f"Run failed: {e}")
            sys.exit(1)


def run_parser(subparsers):
    """Configure the run subcommand parser."""
    parser = subparsers.add_parser("run", help="Create and run a new container from an agent")
    parser.add_argument("-f", "--file", default="Agentfile", help="Name of the Agentfile (when building from source)")
    parser.add_argument(
        "-o", "--output", help="Output directory for generated files " "(default: agent, when building from source)"
    )
    parser.add_argument("-t", "--tag", default="agent:latest", help="Name and optionally a tag for the Docker image")
    parser.add_argument(
        "--from-agentfile",
        action="store_true",
        help="Build from Agentfile and then run " "(default is to run existing image)",
    )
    parser.add_argument(
        "--format",
        choices=["dockerfile", "yaml"],
        help="Explicitly specify the Agentfile format (auto-detected by default)"
    )
    parser.add_argument(
        "--from-yaml",
        action="store_true",
        help="Build from YAML Agentfile format (same as --format yaml)"
    )
    parser.add_argument("--path", default=".", help="Build context (directory or URL) " "when building from Agentfile")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run container interactively")
    parser.add_argument(
        "--rm", dest="remove", action="store_true", help="Automatically remove the container when it exits"
    )
    parser.add_argument(
        "-p", "--port", action="append", help="Publish container port(s) to the host " "(can be used multiple times)"
    )
    parser.add_argument(
        "-e", "--env", action="append", help="Set environment variables " "(can be used multiple times)"
    )
    parser.add_argument("-v", "--volume", action="append", help="Bind mount volumes (can be used multiple times)")
    parser.add_argument("command", nargs="*", help="Command to run in the container (overrides default)")
    runtime_options(parser, "run")
    parser.set_defaults(func=run_cli)


def version_parser(subparsers):
    """Configure the version subcommand parser."""
    parser = subparsers.add_parser("version", help="Show the Agentman version information")
    parser.set_defaults(func=print_version)


def convert_cli(args):
    """Convert between Agentfile formats."""
    from agentman.converter import convert_agentfile
    
    try:
        target_format = args.format if args.format else "auto"
        convert_agentfile(args.input, args.output, target_format)
    except (FileNotFoundError, ValueError) as e:
        perror(f"Conversion failed: {e}")
        sys.exit(1)


def convert_parser(subparsers):
    """Configure the convert subcommand parser."""
    parser = subparsers.add_parser("convert", help="Convert between Agentfile formats")
    parser.add_argument("input", help="Input Agentfile path")
    parser.add_argument("output", help="Output Agentfile path")
    parser.add_argument(
        "--format",
        choices=["yaml", "dockerfile"],
        help="Target format (auto-detected by default based on output extension)"
    )
    parser.set_defaults(func=convert_cli)


def validate_cli(args):
    """Validate an Agentfile."""
    from agentman.converter import validate_agentfile
    
    if not validate_agentfile(args.file):
        sys.exit(1)


def validate_parser(subparsers):
    """Configure the validate subcommand parser."""
    parser = subparsers.add_parser("validate", help="Validate an Agentfile")
    parser.add_argument("file", help="Agentfile path to validate")
    parser.set_defaults(func=validate_cli)


def help_cli(args):
    """Handle the help command by raising HelpException."""
    raise HelpException()


def help_parser(subparsers):
    """Configure the help subcommand parser."""
    parser = subparsers.add_parser("help")
    # Do not run in a container
    parser.set_defaults(func=help_cli)


def configure_subcommands(parser):
    """Add subcommand parsers to the main argument parser."""
    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = False
    build_parser(subparsers)
    run_parser(subparsers)
    convert_parser(subparsers)
    validate_parser(subparsers)
    help_parser(subparsers)
    version_parser(subparsers)


def parse_arguments(parser):
    """Parse command line arguments."""
    return parser.parse_args()


def init_cli():
    """Initialize the CLI by setting up argument parser and parsing arguments."""
    description = get_description()
    parser = create_argument_parser(description)
    configure_subcommands(parser)
    args = parse_arguments(parser)
    post_parse_setup(args)
    return parser, args


def main():
    """Main entry point for the CLI application."""
    parser, args = init_cli()

    def eprint(e, exit_code):
        perror("Error: " + str(e).strip("'\""))
        sys.exit(exit_code)

    try:
        args.func(args)
    except HelpException:
        parser.print_help()
        sys.exit(0)
    except AttributeError as e:
        parser.print_usage()
        perror("agentman: requires a subcommand")
        if getattr(args, "debug", False):
            raise e
    except KeyError as e:
        eprint(e, 1)
    except NotImplementedError as e:
        eprint(e, errno.ENOTSUP)
    except subprocess.CalledProcessError as e:
        eprint(e, e.returncode)
    except KeyboardInterrupt:
        sys.exit(0)
    except (ConnectionError, IndexError, ValueError) as e:
        eprint(e, errno.EINVAL)
    except IOError as e:
        eprint(e, errno.EIO)
