
from collections import deque
import contextlib


def noop(*args, **kw): pass

def identity(arg): return arg

def plural_identity(*args): return args

def mean(nums):
    cnt = len(nums)
    if cnt == 0:
        return None
    return sum(nums) / float(cnt)

def median(nums):
    cnt = len(nums)
    if cnt == 0:
        return None
    nums = sorted(nums)
    med_idx = cnt // 2
    if cnt % 2 == 1:
        return nums[med_idx]
    else:
        return (nums[med_idx-1] + nums[med_idx]) / float(2)

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

def unique_ordered(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
