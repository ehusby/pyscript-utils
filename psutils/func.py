
import contextlib


def noop(*args, **kw): pass

def identity(arg): return arg

def plural_identity(*args): return args

def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)

def median(lst):
    n = len(lst)
    s = sorted(lst)
    return (sum(s[n//2-1:n//2+1])/2.0, s[n//2])[n % 2] if n else None

@contextlib.contextmanager
def with_noop():
    try:
        yield None
    finally:
        pass
