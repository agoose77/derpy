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
