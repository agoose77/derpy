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


class _OverwritableProperty:
    """Property whose fget can be ignored once assigned with a value"""

    def __init__(self, fget):
        self._instances = WeakKeyDictionary()
        self._fget = fget

    def __get__(self, instance, cls):
        try:
            return self._instances[instance]

        except KeyError:
            return self._fget.__get__(instance)()

    def __set__(self, instance, value):
        self._instances[instance] = value


def overwritable_property(fget):
    return _OverwritableProperty(fget)


inf = float("+inf")


def fix(bottom, n=inf, unwrap=lambda x: x):
    if not callable(bottom):
        bottom_value = bottom
        bottom = lambda *args: bottom_value

    def decorator(f):
        def f_fix(*args):
            me = (f_fix, args)

            if not fix.calling:
                value, fix.values[me] = None, bottom(*args)
                i = 0
                while i < n and value != fix.values[me]:
                    fix.calling.add(me)
                    value, fix.values[me] = fix.values[me], unwrap(f(*args))
                    fix.calling.clear()
                    i += 1

                return value

            else:
                if me in fix.calling:
                    return fix.values.get(me, bottom(*args))

                fix.calling.add(me)
                value = fix.values[me] = unwrap(f(*args))
                fix.calling.remove(me)

                return value
        return f_fix
    return decorator

fix.calling = set()
fix.values = {}