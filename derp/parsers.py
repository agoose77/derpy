"""Parsing with derivatives, in Python.

This module defines the base parsing combinators used to perform parsing with derivatives.
Each parser derives from OperatorMixin, which provides the ability to use operators instead of explicit names to 
combine parsers & BaseParser, which implements the main parser API and introduces the BaseParserMeta metaclass, which  
reduces the boilerplate to define fields that can be defined by instantiation arguments. 

Though there are better guides to the function of parsing with derivative (see 
https://maniagnosis.crsr.net/2012/04/parsing-with-derivatives-introduction.html), the general principle is this:

The derivative of any parser with respect to a Token will produce a new parser which can parse future tokens, and 
captures the progress of the parsing process. In other words, taking the derivative returns a new parser whose ability
 to parse future Tokens depends upon the grammar in question - if the parser is given an unexpected Token, then its
 derivative is consequently the Null parser (failed to parse)
 
"""
from abc import ABCMeta, abstractmethod
from itertools import product

from .caching import cached_property, memoized_n
from .fields import FieldMeta

__all__ = ('Alternate', 'Concatenate', 'Recurrence', 'Reduce', 'Literal', 'Token', 'empty_parser',
           'empty_string', 'plus', 'star', 'opt', 'parse', 'lit')


class Token(metaclass=FieldMeta, fields='first second'):
    def __hash__(self):
        return hash((self.first, self.second))

    def __eq__(self, other):
        return type(other) is Token and other.first == self.first and other.second == self.second

    def __repr__(self):
        return "Token({!r}, {!r})".format(self.first, self.second)


class OperatorMixin:
    """Provides operator support to parsers.

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


class BaseParser(OperatorMixin, metaclass=BaseParserMeta):
    def as_string(self):
        return self.__class__.__name__

    @abstractmethod
    def derive(self, token):
        pass

    @abstractmethod
    def derive_null(self):
        pass

    def compact(self):
        return self._compact(set())

    def _compact(self, seen):
        seen.add(self)
        return self


class LazyDerivative(BaseParser, fields='parser token'):
    """Lazy derivative evaluation of derivative of a parser w.r.t a given token.
    Partially avoids non-terminating recursion.
    """

    def _compact(self, seen):
        return self.derivative._compact(seen)

    @cached_property
    def derivative(self):
        return self.parser._derive(self.token)

    def derive(self, token):
        return self.derivative.derive(token)

    def derive_null(self):
        return self.derivative.derive_null()


class FixedPoint(BaseParser):
    """Delays derivative evaluation to avoid non-terminating recursion"""

    _null_set = None

    @abstractmethod
    def _derive(self, token):
        pass

    @abstractmethod
    def _derive_null(self):
        pass

    @memoized_n
    def derive(self, token):
        return LazyDerivative(self, token)

    def derive_null(self):
        """A stupid way to calculate the fixed point of the function"""
        if self._null_set is not None:
            return self._null_set

        new_set = set()

        while True:
            self._null_set = new_set
            new_set = self._derive_null()

            if self._null_set == new_set:
                return self._null_set


class Alternate(FixedPoint, fields='left right'):
    def _compact(self, seen):
        if self not in seen:
            seen.add(self)
            self.left = self.left._compact(seen)
            self.right = self.right._compact(seen)

        if self.left is empty_parser:
            return self.right

        elif self.right is empty_parser:
            return self.left

        return self

    def _derive(self, token):
        return self.__class__(self.left.derive(token), self.right.derive(token))

    def _derive_null(self):
        left_branch = self.left.derive_null()
        right_branch = self.right.derive_null()

        return left_branch | right_branch


class Concatenate(FixedPoint, fields='left right'):
    def _compact(self, seen):
        if self not in seen:
            seen.add(self)
            self.left = self.left._compact(seen)
            self.right = self.right._compact(seen)

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
        left_branch = self.left.derive_null()
        right_branch = self.right.derive_null()

        return set(product(left_branch, right_branch))


class Delta(BaseParser, fields='parser'):
    """Used to keep a record of skipped parse trees"""

    def _compact(self, seen):
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
        if not type(trees) is set:
            raise ValueError(trees)

        if not trees:
            return empty_parser

        return super().__new__(cls)

    def as_string(self):
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


class Recurrence(FixedPoint):
    parser = None

    def _compact(self, seen):
        return self.parser._compact(seen)

    def _derive(self, token):
        return self.parser.derive(token)  # .compact()

    def _derive_null(self):
        return self.parser.derive_null()


class Reduce(FixedPoint, fields='parser func'):
    def _compact(self, seen):
        if self not in seen:
            seen.add(self)
            self.parser = self.parser._compact(seen)

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

    def _derive(self, token):
        return self.__class__(self.parser.derive(token), self.func)

    def _derive_null(self):
        return set(map(self.func, self.parser.derive_null()))


class Literal(BaseParser, fields='string'):
    def as_string(self):
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
    recurrence.parser = Alternate(empty_string, Reduce(Concatenate(parser, recurrence),
                                                       red_repeat))  # recurrence = ~(parser & recurrence)
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
    return result.copy()


empty_parser = Empty()
empty_string = Epsilon.from_value('')

# Define Infix operations
OperatorMixin._concatenate = cat
OperatorMixin._alternate = alt
OperatorMixin._plus = plus
OperatorMixin._reduce = red
OperatorMixin._optional = opt
