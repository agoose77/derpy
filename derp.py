from collections import namedtuple
from contextlib import contextmanager
from itertools import product
from abc import ABC, abstractmethod
from functools import wraps

inf = float("+inf")


def memo(f):
    cache = {}

    @wraps(f)
    def f_memo(*args):
        try:
            return cache[args]

        except KeyError:
            result = cache[args] = f(*args)
            return result

    return f_memo


memo_property = lambda f: property(memo(f))


def recursive_repr(to_text):
    @wraps(to_text)
    def wrapper(self, seen):
        if self not in seen:
            seen.add(self)
            return to_text(self, seen)
        return "..."
    return wrapper


class Undefined:
    pass


def lazy(f, *args, **kwargs):
    value = Undefined

    class proxy:
        def __hash__(self):
            return id(self)

        def __eq__(self, other):
            return id(self) == id(other)

        def __getattr__(self, name):
            nonlocal value
            if value is Undefined:
                value = f(*args, **kwargs)

            return getattr(value, name)

    return proxy()


def fields(*fields):
    def decorator(cls):
        cls_dict = {}
        cls_dict['__slots__'] = tuple(fields)

        assert all(f.isidentifier() for f in fields)
        if fields:
            arg_string = ", ".join(fields)
            body_definitions = ["self.{0} = {0}".format(f) for f in fields]
            definition = "def __init__(self, {}):\n\t".format(arg_string) + "\n\t".join(body_definitions)
            exec(definition, cls_dict)

        cls_name = cls.__name__ + "_record"
        return type(cls_name, (cls,), cls_dict)

    return decorator


@fields('first', 'second')
class Token:
    pass


class Infix:

    _concat = None
    _alt = None
    _rep = None
    _optional = None
    _reduce = None

    def __and__(self, other):
        return self._concat(self, other)

    def __or__(self, other):
        return self._alt(self, other)

    def __pos__(self):
        return self._rep(self)

    def __invert__(self):
        return self._optional(self)

    def __rshift__(self, other):
        return self._reduce(self, other)


class BaseParser(Infix, ABC):

    def compact(self, seen):
        seen.add(self)
        return self

    @abstractmethod
    def derive(self, token):
        pass

    @abstractmethod
    def derive_null(self):
        pass

    @abstractmethod
    def to_text(self, seen):
        pass


class Delayable(BaseParser):

    _null_set = None

    @fields('parser', 'token')
    class Lazy(BaseParser):

        def compact(self, seen):
            return self.derivative.compact(seen)

        @memo_property
        def derivative(self):
            return self.parser._derive(self.token)

        def derive(self, token):
            return self.derivative.derive(token)

        def derive_null(self):
            return self.derivative.derive_null()

        @recursive_repr
        def to_text(self, seen):
            return "Lazy({}, {})".format(self.parser.to_text(seen), self.token)

    @abstractmethod
    def _derive(self, token):
        pass

    @abstractmethod
    def _derive_null(self):
        pass

    @memo
    def derive(self, token):
        return self.__class__.Lazy(self, token)

    @memo
    def derive_null(self):
        if self._null_set is not None:
            return self._null_set

        new_set = set()

        while True:
            self._null_set = new_set
            new_set = self._derive_null()

            if self._null_set == new_set:
                return self._null_set


# Alt-Concat-Rec
@fields('left', 'right')
class Alternate(Delayable):

    def __new__(cls, left, right):
        if left is empty:
            return right

        if right is empty:
            return left

        return super().__new__(cls)

    def compact(self, seen):
        if self not in seen:
            seen.add(self)

            self.left = self.left.compact(seen)
            self.right = self.right.compact(seen)

        if self.left is empty:
            return self.right

        elif self.right is empty:
            return self.left

        return self

    def _derive(self, token):
        return Alternate(self.left.derive(token), self.right.derive(token))

    def _derive_null(self):
        deriv_left = self.left.derive_null()
        deriv_right = self.right.derive_null()

        return deriv_left | deriv_right

    @recursive_repr
    def to_text(self, seen):
        return "({} | {})".format(self.left.to_text(seen), self.right.to_text(seen))


@fields('left', 'right')
class Concatenate(Delayable):

    def __new__(cls, left, right):
        if left is empty or right is empty:
            return empty

        return super().__new__(cls)

    def compact(self, seen):
        if self not in seen:
            seen.add(self)

            self.left = self.left.compact(seen)
            self.right = self.right.compact(seen)

        if self.left is empty or self.right is empty:
            return empty

        if isinstance(self.left, Epsilon) and self.left.size == 1:
            result = next(iter(self.left.derive_null()))

            def reduction(token):
                return result, token
            return Reduce(self.right, reduction)

        if isinstance(self.right, Epsilon) and self.right.size == 1:
            result = next(iter(self.right.derive_null()))

            def reduction(token):
                return token, result
            return Reduce(self.left, reduction)

        return self

    def _derive(self, token):
        return Alternate(Concatenate(self.left.derive(token), self.right),
                         Concatenate(Delta(self.left), self.right.derive(token)))

    def _derive_null(self):
        result = set()

        deriv_left = self.left.derive_null()
        deriv_right = self.right.derive_null()

        for a, b in product(deriv_left, deriv_right):
            result.add((a, b))

        return result

    @recursive_repr
    def to_text(self, seen):
        return "({} & {})".format(self.left.to_text(seen), self.right.to_text(seen))


@fields('parser')
class Delta(Infix):

    def compact(self, seen):
        return Epsilon(self.parser.derive_null())

    def derive(self, token):
        return empty

    def derive_null(self):
        return self.parser.derive_null()

    def to_text(self, seen):
        return "Delta()".format(self.parser)


@fields()
class _Empty(BaseParser):

    def derive(self, token):
        return empty

    def derive_null(self):
        return set()

    def to_text(self, seen):
        return "Empty()"
empty = _Empty()


@fields('_trees')
class Epsilon(BaseParser):

    @classmethod
    def from_value(cls, value):
        return cls({value})

    def __new__(cls, trees):
        if not isinstance(trees, set):
            raise ValueError(trees)

        if not trees:
            return empty

        return super().__new__(cls)

    @property
    def size(self):
        return len(self._trees)

    def derive(self, token):
        return empty

    def derive_null(self):
        return self._trees

    def to_text(self, seen):
        return "Eps({!r})".format(self._trees)
empty_string = Epsilon.from_value('')


class Recurrence(Delayable):
    parser = None

    def compact(self, seen):
        return self.parser.compact(seen)

    def _derive(self, token):
        return self.parser.derive(token)

    def _derive_null(self):
        return self.parser.derive_null()

    @recursive_repr
    def to_text(self, seen):
        return self.parser.to_text(seen)


@fields('parser', 'func')
class Reduce(Delayable):

    def compact(self, seen):
        if self not in seen:
            seen.add(self)
            self.parser = self.parser.compact(seen)

        if self.parser is empty:
            return empty

        elif isinstance(self.parser, self.__class__):
            sub_reduction = self.parser
            inner = sub_reduction.func
            outer = self.func

            def combination(token):
                return outer(inner(token))

            return self.__class__(sub_reduction.parser, combination)

        else:
            return self

    def _derive(self, token):
        return Reduce(self.parser.derive(token), self.func)

    def _derive_null(self):
        result = set()
        for obj in self.parser.derive_null():
            result.add(self.func(obj))
        return result

    @recursive_repr
    def to_text(self, seen):
        return "{} >> {}()".format(self.parser.to_text(seen), self.func.__name__)


@fields('string')
class Ter(BaseParser):

    def derive(self, token):
        return Epsilon.from_value(token.second) if token.first == self.string else empty

    def derive_null(self):
        return set()

    def to_text(self, seen):
        return "Ter({!r})".format(self.string)


def repeat(parser):
    r = Recurrence()
    r.parser = Alternate(empty_string, Concatenate(r, parser))
    return r


def optional(parser):
    return Alternate(empty_string, parser)


Infix._concat = Concatenate
Infix._alt = Alternate
Infix._rep = staticmethod(repeat)
Infix._reduce = Reduce
Infix._optional = staticmethod(optional)


def unpack_n(seq, n, first=True):
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


def flatten_first(packed):
    a, b = packed
    if not isinstance(a, tuple):
        yield a
    else:
        yield from flatten_first(a)
    yield b


def flatten_last(packed):
    if len(packed) == 1:
        yield packed[0]
        return
    a, b = packed
    yield a
    if not isinstance(b, tuple):
        yield b
    else:
        yield from flatten_last(b)


def ter(word):
    return Ter(word)


def parse(parser, tokens):
    for token in tokens:
        parser = compact(parser.derive(token))

    return parser.derive_null()


def compact(parser):
    return parser.compact(set())


def to_text(parser):
    return parser.to_text(set())


# examples
if __name__ == '__main__' and 1:
    # S = Recurrence()
    # a = empty_string | (S & ter('1'))
    # S.parser = a
    # a = +ter('1')
    #
    # print(parse(a, [Token(t, str(i)) for i, t in enumerate(['1', '1', '1'])]))
    print(to_text(ter(1) | ter(2) | ter(3)))