
from collections import deque
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

def exhaust(generator):
    deque(generator, maxlen=0)

def yield_loop(iterable):
    """Generator to unendingly yield items from a non-exhaustive iterable.

    Items are yielded from the iterable through a for-loop. Once all items
    have been yielded, the for-loop repeats to yield additional items.

    Args:
        iterable: An non-exhaustive iterable collection containing items
          to be retrieved.

    Yields:
        An item in the `iterable` collection.

    Examples:
        >>> item_gen = yield_loop([0, 1])
        >>> for i in range(5):
        >>>     print(next(item_gen))
        0
        1
        0
        1
        0
    """
    while True:
        for item in iterable:
            yield item
