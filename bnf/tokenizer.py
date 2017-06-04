from abc import ABC, abstractclassmethod, abstractmethod
from itertools import chain
from ast import literal_eval
from derp.parsers import Token


def get_root_tokenizers():
    return LitTokenizer, IDTokenizer, ParenTokenizer, ColonTokenizer, GreedyTokenizer, OnePlusTokenizer, AltTokenizer, \
           NewlineTokenizer, FormattingTokenizer, CommentTokenizer


def get_paren_tokenizers():
    return LitTokenizer, IDTokenizer, ParenTokenizer, ColonTokenizer, GreedyTokenizer, OnePlusTokenizer, AltTokenizer, \
           NewlineConsumerTokenizer, FormattingTokenizer, CommentTokenizer


class TokenizerIsClosed(Exception):
    """Raising this exception moves the handling of a token to the next tokenizer"""
    pass


class BaseTokenizer(ABC):

    @abstractclassmethod
    def should_enter(self, char):
        pass

    @abstractmethod
    def handle_char(self, char):
        pass

    def finish(self):
        self.handle_char = self._raise_closed

    def abort(self):
        self.finish()
        raise TokenizerIsClosed

    def _raise_closed(self, token):
        raise TokenizerIsClosed

    def get_tokens(self):
        return
        yield


class TextTokenizerMixin:

    def __init__(self):
        super().__init__()

        self._chars = []

    @property
    def string(self):
        return ''.join(self._chars)

    def handle_text_char(self, char):
        self._chars.append(char)


class LitTokenizer(TextTokenizerMixin, BaseTokenizer):
    sentinel_char = "'"

    @classmethod
    def should_enter(cls, char):
        return char == cls.sentinel_char

    def handle_char(self, char):
        self.handle_text_char(char)

        # First character is always the one that opens this tokenizer
        if char == self.sentinel_char and len(self._chars) > 1:
            self.finish()

    def get_tokens(self):
        yield Token('LIT', literal_eval(self.string))


class IDTokenizer(TextTokenizerMixin, BaseTokenizer):
    """Consumes Python identifiers"""

    @classmethod
    def should_enter(cls, char):
        return char.isalpha()

    def handle_char(self, char):
        is_valid = (self.string + char).isidentifier()
        if not is_valid:
            self.abort()

        self.handle_text_char(char)

    def get_tokens(self):
        yield Token('ID', self.string)


class ParenTokenizer(BaseTokenizer):
    entry_to_exit_parens = {'(': ')', '[': ']'}

    def __init__(self):
        super().__init__()

        self._entry_paren = None
        self._exit_paren = None
        self._token_iterables = []

        tokenizers = get_paren_tokenizers()
        self._token_generator = TokenGenerator(tokenizers)

    @classmethod
    def should_enter(cls, char):
        return char in cls.entry_to_exit_parens

    def handle_char(self, char):
        assert char in self.entry_to_exit_parens
        self._entry_paren = char
        self._exit_paren = self.entry_to_exit_parens[char]
        self.handle_char = self.handle_char_following_paren

    def handle_char_following_paren(self, char):
        try:
            self._token_iterables.append(self._token_generator.handle_char(char))
        except ValueError:
            assert char == self._exit_paren
            self.finish()

    def get_tokens(self):
        yield Token(self._entry_paren, self._entry_paren)
        yield from chain.from_iterable(self._token_iterables)
        yield from self._token_generator.flush_tokens()
        yield Token(self._exit_paren, self._exit_paren)


class SymbolTokenizerBase(BaseTokenizer):
    symbol = None

    def __init__(self):
        super().__init__()

        self._char = None

    @classmethod
    def should_enter(cls, char):
        return char == cls.symbol

    def handle_char(self, char):
        self._char = char
        self.finish()

    def get_tokens(self):
        yield Token(self.symbol, self.symbol)


class ColonTokenizer(SymbolTokenizerBase):
    symbol = ':'


class AltTokenizer(SymbolTokenizerBase):
    symbol = '|'


class OnePlusTokenizer(SymbolTokenizerBase):
    symbol = '+'


class GreedyTokenizer(SymbolTokenizerBase):
    symbol = '*'


class NewlineTokenizer(SymbolTokenizerBase):
    symbol = '\n'

    def get_tokens(self):
        yield Token('NEWLINE', '\n')


class NewlineConsumerTokenizer(NewlineTokenizer):
    def get_tokens(self):
        return
        yield


class FormattingTokenizer(BaseTokenizer):
    @classmethod
    def should_enter(cls, char):
        return char in {' ', '\t'}

    def handle_char(self, char):
        self.finish()


class CommentTokenizer(BaseTokenizer):

    @classmethod
    def should_enter(cls, char):
        return char == '#'

    def handle_char(self, char):
        if char == '\n':
            self.finish()


class TokenGenerator:
    """Generates Token instance from a list of valid tokenizers"""
    def __init__(self, tokenizers):
        self._tokenizers = tokenizers
        self._tokenizer = None
        self._token_iterables = []

    def handle_char(self, char):
        while True:
            if self._tokenizer is None:
                self._tokenizer = select_tokenizer_for(char, self._tokenizers)

            try:
                self._tokenizer.handle_char(char)
            except TokenizerIsClosed:
                tokens_iterable = self._tokenizer.get_tokens()
                self._token_iterables.append(tokens_iterable)
                self._tokenizer = None

            else:
                return self.flush_tokens()

    def flush_tokens(self):
        iterable = tuple(chain.from_iterable(self._token_iterables.copy()))
        self._token_iterables.clear()
        return iterable


def select_tokenizer_for(char, tokenizers):
    try:
        return next(p for p in tokenizers if p.should_enter(char))()
    except StopIteration:
        raise ValueError("Cannot handle char {!r}".format(char))


def tokenize_file(filename):
    with open(filename) as f:
        return tokenize_text(f.read())


def tokenize_text(source):
    tokenizers = get_root_tokenizers()
    token_generator = TokenGenerator(tokenizers)

    for char in (source + '\n'):
        yield from token_generator.handle_char(char)

    yield from token_generator.flush_tokens()

    yield Token('ENDMARKER', 'ENDMARKER')
