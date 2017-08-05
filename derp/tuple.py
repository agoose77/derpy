from typing import Any, Callable, Iterable


def selects(n: int, *indices: int, first=True) -> Callable[[tuple], tuple]:
    """Build wrapper which selects particular arguments from parse tree"""

    def wrapper(args: tuple) -> tuple:
        all_args = tuple(unpack(args, n, first))
        return tuple(all_args[i] for i in indices)

    return wrapper


def select(n: int, index: int, first=True) -> Callable[[tuple], Any]:
    """Build wrapper which returns particular arguments from parse tree"""

    def wrapper(args: tuple) -> Any:
        all_args = tuple(unpack(args, n, first))
        return all_args[index]

    return wrapper


def flattens(seq: Iterable, n: int, first=True) -> Callable[[tuple], tuple]:
    """Build wrapper which flattens from parse tree tuples into 1d tuple"""

    def wrapper(args: tuple) -> tuple:
        all_args = tuple(unpack(args, n, first))
        return all_args

    return wrapper


def unpack(seq: Iterable, n: int, first=True) -> tuple:
    """Flatten N nested tuples into flat list

    (x, (y, z)) defines last ordering,
    ((x, y), z) defines first ordering.
    """
    if n < 1:
        raise ValueError("Cannot unpack sequence of length 0")

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
