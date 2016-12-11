"""Parsing with derivatives, in Python"""

__all__ = ('Token', 'Alternate', 'Concatenate', 'empty_string', 'empty', 'Recurrence', 'Reduce', 'Ter', 'ter',
           'one_plus', 'greedy', 'optional', 'parse', 'compact', 'to_text')

from itertools import product
from abc import ABC, abstractmethod

from .utilities import to_text_helper, memoized_property, memoized, TextContext, overwritable_property, with_fields


@with_fields('first', 'second')
class Token:
    def __repr__(self):
        return "<Token: {} {}>".format(repr(self.first), repr(self.second))


class InfixMixin:
    """Provides infix notation support to parsers.

    As parsers may operate upon their own types, these methods are defined later.
    """

    _concat = None
    _alt = None
    _greedy = None
    _optional = None
    _reduce = None

    def __and__(self, other):
        return self._concat(self, other)

    def __or__(self, other):
        return self._alt(self, other)

    def __pos__(self):
        return self._greedy(self)

    def __invert__(self):
        return self._optional(self)

    def __rshift__(self, other):
        return self._reduce(self, other)


class BaseParser(InfixMixin, ABC):

    @overwritable_property
    def simple_name(self):
        return self.__class__.__name__

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
    def to_text(self, context):
        pass


class Delayable(BaseParser):
    """Delays derivative evaluation to avoid non-terminating recursion"""

    _null_set = None

    @with_fields('parser', 'token')
    class Lazy(BaseParser):

        def compact(self, seen):
            return self.derivative.compact(seen)

        @memoized_property
        def derivative(self):
            return self.parser._derive(self.token)

        def derive(self, token):
            return self.derivative.derive(token)

        def derive_null(self):
            return self.derivative.derive_null()

        @to_text_helper
        def to_text(self, seen):
            return "Lazy({}, {})".format(self.parser.to_text(seen), self.token)

    @abstractmethod
    def _derive(self, token):
        pass

    @abstractmethod
    def _derive_null(self):
        pass

    @memoized
    def derive(self, token):
        return self.__class__.Lazy(self, token)

    @memoized
    def derive_null(self):
        if self._null_set is not None:
            return self._null_set

        new_set = set()

        while True:
            self._null_set = new_set
            new_set = self._derive_null()

            if self._null_set == new_set:
                return self._null_set


@with_fields('left', 'right')
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

    @to_text_helper
    def to_text(self, seen):
        return "({} | {})".format(self.left.to_text(seen), self.right.to_text(seen))


@with_fields('left', 'right')
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
            result_set = set(self.left.derive_null())
            result = result_set.pop()
            assert not result_set

            def reduction(token):
                return result, token

            return Reduce(self.right, reduction)

        if isinstance(self.right, Epsilon) and self.right.size == 1:
            result_set = set(self.right.derive_null())
            result = result_set.pop()
            assert not result_set

            def reduction(token):
                return token, result

            return Reduce(self.left, reduction)

        return self

    def _derive(self, token):
        return Alternate(Concatenate(self.left.derive(token), self.right),
                         Concatenate(Delta(self.left), self.right.derive(token)))

    def _derive_null(self):
        deriv_left = self.left.derive_null()
        deriv_right = self.right.derive_null()

        return set(product(deriv_left, deriv_right))

    @to_text_helper
    def to_text(self, seen):
        return "({} & {})".format(self.left.to_text(seen), self.right.to_text(seen))


@with_fields('parser')
class Delta(InfixMixin):
    """Used to keep a record of skipped parse trees"""

    def compact(self, seen):
        return Epsilon(self.parser.derive_null())

    def derive(self, token):
        return empty

    def derive_null(self):
        return self.parser.derive_null()

    def to_text(self, seen):
        return "Delta()".format(self.parser)


@with_fields()
class _Empty(BaseParser):
    def derive(self, token):
        return empty

    def derive_null(self):
        return set()

    def to_text(self, seen):
        return "Empty()"


empty = _Empty()


@with_fields('_trees')
class Epsilon(BaseParser):
    @overwritable_property
    def simple_name(self):
        return "Epsilon({})".format(self._trees)

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

    @to_text_helper
    def to_text(self, seen):
        return self.parser.to_text(seen)


@with_fields('parser', 'func')
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

            combination.__name__ = "{}({})".format(outer.__name__, inner.__name__)

            return self.__class__(sub_reduction.parser, combination)

        else:
            return self

    def _derive(self, token):
        return Reduce(self.parser.derive(token), self.func)

    def _derive_null(self):
        return set(map(self.func, self.parser.derive_null()))

    @to_text_helper
    def to_text(self, seen):
        return "{} >> {}()".format(self.parser.to_text(seen), self.func.__name__)


@with_fields('string')
class Ter(BaseParser):
    @overwritable_property
    def simple_name(self):
        return "Ter({})".format(self.string)

    def derive(self, token):
        return Epsilon.from_value(token.second) if token.first == self.string else empty

    def derive_null(self):
        return set()

    def to_text(self, seen):
        return "Ter({!r})".format(self.string)


def one_plus(parser):
    def red_one_plus(args):
        first, remainder = args
        if remainder == '':
            return first,
        return (first,) + remainder

    return Reduce(Concatenate(parser, greedy(parser)), red_one_plus)


def greedy(parser):
    r = Recurrence()

    def red_repeat(args):
        first, remainder = args
        if remainder == '':
            return first,
        return (first,) + remainder

    r.parser = Alternate(empty_string, Reduce(Concatenate(parser, r), red_repeat))  # r = ~(parser & r)
    return r


def optional(parser):
    return Alternate(empty_string, parser)


def ter(word):
    return Ter(word)


# Define Infix operations
InfixMixin._concat = Concatenate
InfixMixin._alt = Alternate
InfixMixin._greedy = staticmethod(greedy)
InfixMixin._reduce = Reduce
InfixMixin._optional = staticmethod(optional)


def parse(parser, tokens):
    for token in tokens:
        parser = compact(parser.derive(token))
        if parser is empty:
            break
    return parser.derive_null()


def compact(parser):
    return parser.compact(set())


def to_text(parser, max_depth=None):
    context = TextContext(set(), 0, max_depth)
    return parser.to_text(context)