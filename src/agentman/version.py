def version():
    return "0.1.0"


def print_version(args):
    if args.quiet:
        print(version())
    else:
        print("agentman version %s" % version())
