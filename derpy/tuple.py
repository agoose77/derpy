from typing import Any, Callable, Iterable, Iterator


def selects(n: int, *indices: int, first: bool = True) -> Callable[[tuple], tuple]:
    """Build wrapper which selects arguments given by indices from parse tree.

    :param n: size of nested parse tree to unpack
    :param indices: indices of elements to extract
    :param first: ordering (see unpack docs)
    """

    def selects_(args: tuple) -> tuple:
        all_args = tuple(unpack(args, n, first))
        return tuple(all_args[i] for i in indices)

    selects_.__doc__ = f"Select arguments {indices!r} from parse tree.\n    :param args: parse tree\n"
    return selects_


def select(n: int, index: int, first: bool = True) -> Callable[[tuple], Any]:
    """Build wrapper which selects argument given by index from parse tree.

    :param n: size of nested parse tree to unpack
    :param index: indices of element to extract
    :param first: ordering (see unpack docs)
    """

    def select_(args: tuple) -> Any:
        all_args = tuple(unpack(args, n, first))
        return all_args[index]

    select_.__doc__ = f"Select argument {index!r} from parse tree.\n    :param args: parse tree\n"
    return select_


def flatten(n: int, first: bool = True) -> Callable[[tuple], tuple]:
    """Build wrapper which flattens given number of parse tree tuples into a 1d tuple.

    :param n: size of nested parse tree to unpack
    :param first: ordering (see unpack docs)
    """

    def flatten_(args: tuple) -> tuple:
        return tuple(unpack(args, n, first))

    flatten_.__doc__ = f"Flatten {n!r} parse tree tuples into a 1d tuple.\n    :param args: parse tree\n"
    return flatten_


def unpack(seq: Iterable, n: int, first: bool = True) -> Iterator[tuple]:
    """Flatten N nested tuples into flat sequence (iterator).

    (x, (y, z)) defines last ordering,
    ((x, y), z) defines first ordering.

    :param seq: nested tuple sequence
    :param n: number of nested tuples
    :param first: ordering (see above)
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
