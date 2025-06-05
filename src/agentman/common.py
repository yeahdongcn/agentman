import sys


def perror(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
