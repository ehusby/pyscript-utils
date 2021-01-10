
from __future__ import print_function
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


trace = print
debug = print
info = print
verbose1 = print
verbose2 = print
verbose3 = print
warning = eprint
error = eprint
critical = eprint
