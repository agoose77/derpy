from typing import Any, Callable, Iterable, Tuple


def extracts(n: int, *indices: Tuple[int, ...], first=True) -> Callable[[tuple], tuple]:
    """Build wrapper which returns selected arguments"""

    def wrapper(args):
        all_args = tuple(unpack(args, n, first))
        return tuple(all_args[i] for i in indices)

    return wrapper


def extract(n: int, index: int, first=True) -> Callable[[tuple], Any]:
    """Build wrapper which returns selected argument"""

    def wrapper(args):
        all_args = tuple(unpack(args, n, first))
        return all_args[index]

    return wrapper


def flatten(seq: Iterable, first=True) -> tuple:
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


def partial(f, n, *indices, first=True) -> Callable[[tuple], Any]:
    """Build wrapper which returns result of f(...) with selected arguments"""
    extractor = extracts(n, *indices, first)

    def wrapper(args):
        return f(*extractor(args))

    return wrapper


def unpack(seq: Iterable, n: int, first=True) -> tuple:
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
