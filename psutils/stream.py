
import contextlib
import sys
import traceback
import warnings

import psutils.globals as psu_globals

if psu_globals.PYTHON_VERSION_LT_3:
    from StringIO import StringIO
else:
    from io import StringIO


@contextlib.contextmanager
def capture_stdout_stderr():
    oldout, olderr = sys.stdout, sys.stderr
    out = [StringIO(), StringIO()]
    try:
        sys.stdout, sys.stderr = out
        yield out
    finally:
        sys.stdout, sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()


def capture_error_trace():
    with capture_stdout_stderr() as out:
        traceback.print_exc()
    caught_out, caught_err = out
    return caught_err


showwarning_stderr = warnings.showwarning
def showwarning_stdout(message, category, filename, lineno, file=None, line=None):
    sys.stdout.write(warnings.formatwarning(message, category, filename, lineno))
