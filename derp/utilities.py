from collections import namedtuple
from functools import wraps
from weakref import WeakKeyDictionary

TextContext = namedtuple("TextContext", "seen depth max_depth")


def limited_depth_text(func):
    """Prevent writing too much information to string than is legible"""

    @wraps(func)
    def wrapper(self, context):
        if context.depth == context.max_depth:
            return self.simple_name

        new_context = TextContext(context.seen, context.depth + 1, context.max_depth)
        return func(self, new_context)

    return wrapper


def recursion_guard_text(func):
    """Prevent recursive calls through to_text traversal"""

    @wraps(func)
    def wrapper(self, context):
        if self not in context.seen:
            context.seen.add(self)

            return func(self, context)
        return "{}(...)".format(self.simple_name)

    return wrapper


def to_text_helper(func):
    """Combinatined recursion guard and depth limiter"""
    return recursion_guard_text(limited_depth_text(func))


def weakly_memoized(f):
    memo = WeakKeyDictionary()

    def wrapper(self, memo=memo):
        try:
            return memo[self]

        except KeyError:
            result = memo[self] = f.__get__(self)()
            return result

    return wrapper


def weakly_memoized_n(f):
    memo = WeakKeyDictionary()

    def wrapper(self, *args, memo=memo):
        try:
            self_memo = memo[self]
        except KeyError:
            self_memo = memo[self] = {}

        try:
            result = self_memo[args]
        except KeyError:
            result = self_memo[args] = f.__get__(self)(*args)
        return result

    return wrapper


def memoized_property(f):
    return property(weakly_memoized(f))


def memoized_compact(f):
    memo = WeakKeyDictionary()

    def wrapper(self, memo=memo):
        try:
            return memo[self]
        except KeyError:
            memo[self] = self
            result = memo[self] = f.__get__(self)()
            return result

    return wrapper


def rflatten(seq, first=True):
    """Recursively flatten nested tuples into flat list

    (x, (y, z)) defines last ordering,
    ((x, y), z) defines first ordering.
    """
    while True:
        if not isinstance(seq, tuple):
            yield seq
            return

        if first:
            seq, x = seq
        else:
            x, seq = seq

            yield x


def unpack_n(seq, n, first=True):
    """Flatten N nested tuples into flat list

    (x, (y, z)) defines last ordering,
    ((x, y), z) defines first ordering.
    """
    if n < 1:
        raise ValueError(n)

    elif n > 1:
        if first:
            seq, x = seq
            yield from unpack_n(seq, n-1, True)
            yield x

        else:
            x, seq = seq
            yield x
            yield from unpack_n(seq, n-1, False)
    else:
        yield seq
