
import contextlib

def noop(*args, **kw): pass

@contextlib.contextmanager
def with_noop(*args, **kw):
    try:
        yield None
    finally:
        pass
