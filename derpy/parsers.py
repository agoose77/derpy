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

from typing import Iterable, Callable

from .caching import cached_property, memoized_n
from .fields import FieldMeta
from .token import Token
from .tuple import unpack

__all__ = (
    "Alternate",
    "Concatenate",
    "Recurrence",
    "Reduce",
    "Literal",
    "Token",
    "empty_parser",
    "empty_string",
    "plus",
    "star",
    "opt",
    "parse",
    "lit",
)


class OperatorMixin:
    """Provides operator support to parsers.

    As parsers may operate upon their own types, these methods are defined later.
    """

    def __and__(self, other) -> "Concatenate":
        return cat(self, other)

    def __or__(self, other) -> "Alternate":
        return alt(self, other)

    def __getitem__(self, item) -> "BaseParser":
        if item is Ellipsis:
            return star(self)

        elif isinstance(item, slice):
            # TODO if we want to support "between", write new macro
            assert item.stop is None, "Cannot bound slice"
            return least(self, item.start)

        else:
            assert isinstance(item, int)
            return arr(self, item)

    def __invert__(self) -> "Alternate":
        return opt(self)

    def __rshift__(self, other) -> "Reduce":
        return red(self, other)


class BaseParserMeta(FieldMeta, ABCMeta):
    pass


class BaseParser(OperatorMixin, metaclass=BaseParserMeta):
    @abstractmethod
    def derive(self, token: Token) -> "BaseParser":
        pass

    @abstractmethod
    def derive_null(self) -> frozenset:
        pass

    def compact(self) -> "BaseParser":
        return self._compact(set())

    def _compact(self, seen: set) -> "BaseParser":
        seen.add(self)
        return self


class LazyDerivative(BaseParser, fields="parser token"):
    """Lazy derivative evaluation of derivative of a parser w.r.t a given token.
    Partially avoids non-terminating recursion.
    """

    def _compact(self, seen: set) -> BaseParser:
        return self.derivative._compact(seen)

    @cached_property
    def derivative(self) -> BaseParser:
        return self.parser._derive(self.token)

    def derive(self, token: Token) -> BaseParser:
        return self.derivative.derive(token)

    def derive_null(self) -> BaseParser:
        return self.derivative.derive_null()


class FixedPoint(BaseParser):
    """Delays derivative evaluation to avoid non-terminating recursion"""

    _null_set = None

    @abstractmethod
    def _derive(self, token: Token) -> BaseParser:
        pass

    @abstractmethod
    def _derive_null(self) -> BaseParser:
        pass

    @memoized_n
    def derive(self, token: Token) -> LazyDerivative:
        return LazyDerivative(self, token)

    def derive_null(self) -> frozenset:
        """A stupid way to calculate the fixed point of the function"""
        if self._null_set is not None:
            return self._null_set

        new_set = frozenset()

        while True:
            self._null_set = new_set
            new_set = self._derive_null()

            if self._null_set == new_set:
                return self._null_set


class Alternate(FixedPoint, fields="left right"):
    def _compact(self, seen: set) -> BaseParser:
        if self not in seen:
            seen.add(self)
            self.left = self.left._compact(seen)
            self.right = self.right._compact(seen)

        if self.left is empty_parser:
            return self.right

        elif self.right is empty_parser:
            return self.left

        return self

    def _derive(self, token: Token) -> "Alternate":
        return self.__class__(self.left.derive(token), self.right.derive(token))

    def _derive_null(self) -> frozenset:
        left_branch = self.left.derive_null()
        right_branch = self.right.derive_null()

        return left_branch | right_branch


class Concatenate(FixedPoint, fields="left right"):
    def _compact(self, seen: set) -> BaseParser:
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

            def reduction(token: Token):
                return result, token

            return Reduce(self.right, reduction)

        if type(self.right) is Epsilon and self.right.size == 1:
            result_set = set(self.right.derive_null())
            result = result_set.pop()
            assert not result_set

            def reduction(token: Token):
                return token, result

            return Reduce(self.left, reduction)

        return self

    def _derive(self, token: Token) -> Alternate:
        cls = self.__class__
        return Alternate(cls(self.left.derive(token), self.right), cls(Delta(self.left), self.right.derive(token)))

    def _derive_null(self) -> frozenset:
        left_branch = self.left.derive_null()
        right_branch = self.right.derive_null()

        return frozenset(product(left_branch, right_branch))


class Empty(BaseParser):
    _singleton = None

    def __new__(cls):
        if cls._singleton is not None:
            raise ValueError

        instance = super().__new__(cls)
        cls._singleton = instance
        return instance

    def derive(self, token: Token) -> "Empty":
        return empty_parser

    def derive_null(self) -> frozenset:
        return frozenset()


class Epsilon(BaseParser, fields="_trees"):
    def __new__(cls, trees: frozenset):
        if not type(trees) is frozenset:
            raise ValueError(trees)

        if not trees:
            return empty_parser

        return super().__new__(cls)

    @classmethod
    def from_value(cls, value) -> "Epsilon":
        as_set = frozenset((value,))
        return cls(as_set)

    @property
    def size(self) -> int:
        return len(self._trees)

    def derive(self, token: Token) -> Empty:
        return empty_parser

    def derive_null(self) -> frozenset:
        return self._trees


class Delta(BaseParser, fields="parser"):
    """Used to keep a record of skipped parse trees"""

    def _compact(self, seen: set) -> Epsilon:
        return Epsilon(self.parser.derive_null())

    def derive(self, token: Token) -> Empty:
        return empty_parser

    def derive_null(self) -> BaseParser:
        return self.parser.derive_null()


class Recurrence(FixedPoint):
    parser = None

    def _compact(self, seen) -> BaseParser:
        return self.parser._compact(seen)

    def _derive(self, token: Token) -> BaseParser:
        return self.parser.derive(token)  # .compact()

    def _derive_null(self) -> frozenset:
        return self.parser.derive_null()


class Reduce(FixedPoint, fields="parser func"):
    def _compact(self, seen: set) -> BaseParser:
        if self not in seen:
            seen.add(self)
            self.parser = self.parser._compact(seen)

        if self.parser is empty_parser:
            return empty_parser

        elif isinstance(self.parser, self.__class__):
            sub_reduction = self.parser
            inner = sub_reduction.func
            outer = self.func

            def combination(token: Token):
                return outer(inner(token))

            combination.__qualname__ = f"{inner} >> {outer})"
            return self.__class__(sub_reduction.parser, combination)

        else:
            return self

    def _derive(self, token: Token) -> "Reduce":
        return self.__class__(self.parser.derive(token), self.func)

    def _derive_null(self) -> frozenset:
        return frozenset(map(self.func, self.parser.derive_null()))


class Literal(BaseParser, fields="string"):
    def derive(self, token: Token) -> BaseParser:
        return Epsilon.from_value(token.second) if token.first == self.string else empty_parser

    def derive_null(self) -> frozenset:
        return frozenset()


# Macro API #####################################################
def plus(parser: BaseParser) -> Reduce:
    """Kleene plus (1+) parser"""

    def red_one_plus(args):
        first, remainder = args
        if remainder == "":
            return (first,)
        return (first,) + remainder

    return Reduce(Concatenate(parser, star(parser)), red_one_plus)


def arr(parser: BaseParser, n: int):
    assert n > 0

    def red_array(args):
        return tuple(unpack(args, n))

    p = parser
    for i in range(n - 1):
        p = Concatenate(p, parser)

    return Reduce(p, red_array)


def star(parser: BaseParser) -> Recurrence:
    """Kleene star (0+) parser"""

    def red_repeat(args):
        first, remainder = args
        if remainder == "":
            return (first,)
        return (first,) + remainder

    recurrence = Recurrence()
    recurrence.parser = Alternate(
        empty_string, Reduce(Concatenate(parser, recurrence), red_repeat)
    )  # recurrence = ~(parser & recurrence)
    return recurrence


def least(parser: BaseParser, n: int):
    assert n >= 0
    if n > 0:

        def reduce_slice(args):
            array, remainder = args
            if remainder == "":
                return array
            return array + remainder

        p = cat(arr(parser, n), star(parser))
        return Reduce(p, reduce_slice)

    return star(parser)


def opt(parser: BaseParser) -> Alternate:
    return Alternate(empty_string, parser)


def lit(word: str) -> Literal:
    """Create a Literal parser"""
    return Literal(word)


def cat(left: BaseParser, right: BaseParser) -> Concatenate:
    """Create a Concatenate parser"""
    return Concatenate(left, right)


def alt(left: BaseParser, right: BaseParser) -> Alternate:
    """Create an Alternate parser"""
    return Alternate(left, right)


def red(parser: BaseParser, func: Callable) -> Reduce:
    """Create a Reduction parser"""
    return Reduce(parser, func)


def rec() -> Recurrence:
    """Create a Recurrence parser"""
    return Recurrence()


def parse(parser: BaseParser, tokens: Iterable[Token]) -> frozenset:
    for i, token in enumerate(tokens):
        parser = parser.derive(token)
        parser = parser.compact()

        if parser is empty_parser:
            break

    return parser.derive_null()


empty_parser = Empty()
empty_string = Epsilon.from_value("")
