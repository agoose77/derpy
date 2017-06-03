"""Parsing with derivatives, in Python"""
from abc import ABCMeta, abstractmethod
from itertools import product

from .fields import FieldMeta
from .utilities import memoized_property, weakly_memoized, weakly_memoized_n, memoized_compact, overwritable_property

__all__ = ('Alternate', 'Concatenate', 'Recurrence', 'Reduce', 'Literal', 'Token', 'empty_parser',
           'empty_string', 'plus', 'star', 'opt', 'parse', 'lit')


class Token(metaclass=FieldMeta, fields='first second'):

    def __hash__(self):
        return hash((self.first, self.second))

    def __eq__(self, other):
        return type(other) is Token and other.first == self.first and other.second == self.second

    def __repr__(self):
        return "Token({!r}, {!r})".format(self.first, self.second)


class InfixMixin:
    """Provides infix notation support to parsers.

    As parsers may operate upon their own types, these methods are defined later.
    """

    _concatenate = None
    _alternate = None
    _plus = None
    _optional = None
    _reduce = None

    def __and__(self, other):
        return self._concatenate(other)

    def __or__(self, other):
        return self._alternate(other)

    def __pos__(self):
        return self._plus()

    def __invert__(self):
        return self._optional()

    def __rshift__(self, other):
        return self._reduce(other)


class BaseParserMeta(FieldMeta, ABCMeta):
    pass


class BaseParser(InfixMixin, metaclass=BaseParserMeta):

    @overwritable_property
    def simple_name(self):
        return self.__class__.__name__

    @abstractmethod
    def derive(self, token):
        pass

    @abstractmethod
    def derive_null(self):
        pass

    @memoized_compact
    def compact(self):
        return self


class LazyDerivative(BaseParser, fields='parser token'):
    """Lazy derivative evaluation of derivative of a parser wrt a given token.
    Partially avoids non-terminating recursion.
    """

    @memoized_compact
    def compact(self):
        return self.derivative.compact()

    @memoized_property
    def derivative(self):
        return self.parser._derive(self.token)

    def derive(self, token):
        return self.derivative.derive(token)

    def derive_null(self):
        return self.derivative.derive_null()


class Delayable(BaseParser):
    """Delays derivative evaluation to avoid non-terminating recursion"""

    _null_set = None

    @abstractmethod
    def _derive(self, token):
        pass

    @abstractmethod
    def _derive_null(self):
        pass

    @weakly_memoized_n
    def derive(self, token):
        return LazyDerivative(self, token)

    @weakly_memoized
    def derive_null(self):
        if self._null_set is not None:
            return self._null_set

        new_set = set()

        while True:
            self._null_set = new_set
            new_set = self._derive_null()

            if self._null_set == new_set:
                return self._null_set

# TODO return new parsers rather than mutating?
class Alternate(Delayable, fields='left right'):
    @memoized_compact
    def compact(self):
        self.left = self.left.compact()
        self.right = self.right.compact()

        if self.left is empty_parser:
            return self.right

        elif self.right is empty_parser:
            return self.left

        return self

    def _derive(self, token):
        return self.__class__(self.left.derive(token), self.right.derive(token))

    def _derive_null(self):
        deriv_left = self.left.derive_null()
        deriv_right = self.right.derive_null()

        return deriv_left | deriv_right


class Concatenate(Delayable, fields='left right'):

    @memoized_compact
    def compact(self):
        self.left = self.left.compact()
        self.right = self.right.compact()

        if self.left is empty_parser or self.right is empty_parser:
            return empty_parser

        if type(self.left) is Epsilon and self.left.size == 1:
            result_set = set(self.left.derive_null())
            result = result_set.pop()
            assert not result_set

            def reduction(token):
                return result, token

            return Reduce(self.right, reduction)

        if type(self.right) is Epsilon and self.right.size == 1:
            result_set = set(self.right.derive_null())
            result = result_set.pop()
            assert not result_set

            def reduction(token):
                return token, result

            return Reduce(self.left, reduction)

        return self

    def _derive(self, token):
        cls = self.__class__
        return Alternate(cls(self.left.derive(token), self.right),
                         cls(Delta(self.left), self.right.derive(token)))

    def _derive_null(self):
        deriv_left = self.left.derive_null()
        deriv_right = self.right.derive_null()

        return set(product(deriv_left, deriv_right))


class Delta(BaseParser, fields='parser'):
    """Used to keep a record of skipped parse trees"""

    @memoized_compact
    def compact(self):
        return Epsilon(self.parser.derive_null())

    def derive(self, token):
        return empty_parser

    def derive_null(self):
        return self.parser.derive_null()


class Empty(BaseParser):
    _singleton = None

    def __new__(cls):
        if cls._singleton is not None:
            raise ValueError

        instance = super().__new__(cls)
        cls._singleton = instance
        return instance

    def derive(self, token):
        return empty_parser

    def derive_null(self):
        return set()


class Epsilon(BaseParser, fields='_trees'):

    def __new__(cls, trees):
        if not isinstance(trees, set):
            raise ValueError(trees)

        if not trees:
            return empty_parser

        return super().__new__(cls)

    @overwritable_property
    def simple_name(self):
        return "Epsilon({!r})".format(self._trees)

    @classmethod
    def from_value(cls, value):
        return cls({value})

    @property
    def size(self):
        return len(self._trees)

    def derive(self, token):
        return empty_parser

    def derive_null(self):
        return self._trees


class Recurrence(Delayable):
    parser = None

    @memoized_compact
    def compact(self):
        return self.parser.compact()

    def _derive(self, token):
        return self.parser.derive(token)  # .compact()

    def _derive_null(self):
        return self.parser.derive_null()


class Reduce(BaseParser, fields='parser func'):
    @memoized_compact
    def compact(self):
        self.parser = self.parser.compact()

        if self.parser is empty_parser:
            return empty_parser

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

    def derive(self, token):
        return self.__class__(self.parser.derive(token), self.func)

    def derive_null(self):
        return set(map(self.func, self.parser.derive_null()))


class Literal(BaseParser, fields='string'):

    @overwritable_property
    def simple_name(self):
        return "Ter({})".format(self.string)

    def derive(self, token):
        return Epsilon.from_value(token.second) if token.first == self.string else empty_parser

    def derive_null(self):
        return set()


# API #####################################################
def star(parser):
    def red_one_plus(args):
        first, remainder = args
        if remainder == '':
            return first,
        return (first,) + remainder

    return Reduce(Concatenate(parser, plus(parser)), red_one_plus)


def plus(parser):

    def red_repeat(args):
        first, remainder = args
        if remainder == '':
            return first,
        return (first,) + remainder

    recurrence = Recurrence()
    recurrence.parser = Alternate(empty_string, Reduce(Concatenate(parser, recurrence), red_repeat))  # recurrence = ~(parser & recurrence)
    return recurrence


def opt(parser):
    return Alternate(empty_string, parser)


def lit(word):
    """Create a Literal parser"""
    return Literal(word)


def cat(left, right):
    """Create a Concatenate parser"""
    return Concatenate(left, right)


def alt(left, right):
    """Create an Alternate parser"""
    return Alternate(left, right)


def red(parser, func):
    """Create a Reduction parser"""
    return Reduce(parser, func)


def parse(parser, tokens):
    for i, token in enumerate(tokens):
        parser = parser.derive(token)
        parser = parser.compact()

        if parser is empty_parser:
            break

    result = parser.derive_null()
    return result


empty_parser = Empty()
empty_string = Epsilon.from_value('')

# Define Infix operations
InfixMixin._concatenate = cat
InfixMixin._alternate = alt
InfixMixin._plus = plus
InfixMixin._reduce = red
InfixMixin._optional = opt
