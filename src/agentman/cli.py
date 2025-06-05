import argparse
import sys

from agentman.common import perror


class HelpException(Exception):
    pass


class ArgumentParserWithDefaults(argparse.ArgumentParser):
    def add_argument(self, *args, help=None, default=None, completer=None, **kwargs):
        if help is not None:
            kwargs['help'] = help
        if default is not None and args[0] != '-h':
            kwargs['default'] = default
            if help is not None and help != "==SUPPRESS==":
                kwargs['help'] += f' (default: {default})'
        action = super().add_argument(*args, **kwargs)
        if completer is not None:
            action.completer = completer
        return action


def get_description():
    return """\
Manage agents
"""


def configure_arguments(parser):
    """Configure the command-line arguments for the parser."""
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--debug",
        action="store_true",
        help="display debug messages",
    )


def create_argument_parser(description):
    parser = ArgumentParserWithDefaults(
        prog="agentman",
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    configure_arguments(parser)
    return parser


def runtime_options(parser, command):
    pass


def build_cli(args):
    pass


def build_parser(subparsers):
    parser = subparsers.add_parser("build", help="Build an image from a Agentfile")
    runtime_options(parser, "build")
    parser.set_defaults(func=build_cli)


def run_cli(args):
    pass


def run_parser(subparsers):
    parser = subparsers.add_parser("run", help="Create and run a new container from an agent")
    runtime_options(parser, "run")
    parser.set_defaults(func=run_cli)


def configure_subcommands(parser):
    """Add subcommand parsers to the main argument parser."""
    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = False
    build_parser(subparsers)
    run_parser(subparsers)


def parse_arguments(parser):
    """Parse command line arguments."""
    return parser.parse_args()


def post_parse_setup(args):
    pass


def init_cli():
    description = get_description()
    parser = create_argument_parser(description)
    configure_subcommands(parser)
    args = parse_arguments(parser)
    post_parse_setup(args)
    return parser, args


def main():
    parser, args = init_cli()

    def eprint(e, exit_code):
        perror("Error: " + str(e).strip("'\""))
        sys.exit(exit_code)

    try:
        args.func(args)
    except HelpException:
        parser.print_help()
    except AttributeError as e:
        parser.print_usage()
        perror("agentman: requires a subcommand")
        if getattr(args, "debug", False):
            raise e
