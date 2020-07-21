
import contextlib


def noop(*args, **kw): pass

def identity(arg): return arg

def plural_identity(*args): return args


@contextlib.contextmanager
def with_noop():
    try:
        yield None
    finally:
        pass
