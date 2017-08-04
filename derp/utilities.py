from collections import namedtuple
from functools import wraps, partial as _partial

TextContext = namedtuple("TextContext", "seen depth max_depth")


def limited_depth_text(func):
    """Prevent writing too much information to string than is legible"""

    @wraps(func)
    def wrapper(self, context):
        if context.depth == context.max_depth:
            return self.as_string

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
        return f"{self.as_string}(...)"

    return wrapper


def to_text_helper(func):
    """Combinatined recursion guard and depth limiter"""
    return recursion_guard_text(limited_depth_text(func))


def flatten(seq, first=True):
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


def unpack(seq, n, first=True):
    """Flatten N nested tuples into flat list

    (x, (y, z)) defines last ordering,
    ((x, y), z) defines first ordering.
    """
    if n < 1:
        raise ValueError(n)

    elif n > 1:
        if first:
            seq, x = seq
            yield from unpack(seq, n - 1, True)
            yield x

        else:
            x, seq = seq
            yield x
            yield from unpack(seq, n - 1, False)
    else:
        yield seq


def extracts(n, *indices, first=True):
    """Reduction to extract given args from parser"""
    def wrapper(args):
        all_args = tuple(unpack(args, n, first))
        return tuple(all_args[i] for i in indices)
    return wrapper


def extract(n, index, first=True):
    """Reduction to extract given arg from parser"""
    def wrapper(args):
        all_args = tuple(unpack(args, n, first))
        return all_args[index]
    return wrapper


def partial(f, n, *indices, first=True):
    extractor = extracts(n, *indices, first)
    def wrapper(args):
        return f(*extractor(args))
    return wrapper