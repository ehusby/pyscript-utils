
from __future__ import print_function
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


debug = print
info = print
warning = eprint
error = eprint
critical = eprint
