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


def memoized(f):
    cache = {}

    @wraps(f)
    def f_memo(*args):
        try:
            return cache[args]

        except KeyError:
            result = cache[args] = f(*args)
            return result

    return f_memo


memoized_property = lambda f: property(memoized(f))


def unpack_n(seq, n, first=True):
    """Perform n-depth tuple pair unpacking:

    Transforms ((x, y), z) into x, y, z with n=3.
    """
    terms = []

    for i in range(n - 1):
        if first:
            seq, a = seq

        else:
            a, seq = seq

        terms.append(a)
    terms.append(seq)

    if first:
        terms.reverse()

    return terms


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


def with_fields(*fields):
    def decorator(cls):
        cls_dict = {}
        cls_dict['__slots__'] = tuple(fields)

        assert all(f.isidentifier() for f in fields)
        if fields:
            arg_string = ", ".join(fields)
            body_definitions = ["self.{0} = {0}".format(f) for f in fields]
            definition = "def __init__(self, {}):\n\t".format(arg_string) + "\n\t".join(body_definitions)
            exec(definition, cls_dict)

        cls_name = cls.__name__
        return type(cls_name, (cls,), cls_dict)

    return decorator
