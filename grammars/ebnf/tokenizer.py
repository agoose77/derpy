"""Primitive example of a tokenizer for a BNF grammar.

Implemented using state machine "tokenizers". Given that there are few cases where the tokenizer is context dependent,
such cases are implemented with nested tokenizers, and thereafter each tokenizer is tested whether it can handle a 
character until one is found
"""
from abc import ABC, abstractclassmethod, abstractmethod
from ast import literal_eval
from enum import Enum
from itertools import chain

from derp.parsers import Token


class TokenizerState(Enum):
    running = object()
    handled = object()
    unhandled = object()


def get_root_tokenizers():
    return LitTokenizer, IDTokenizer, ParenTokenizer, SymbolTokenizer, NewlineTokenizer, FormattingTokenizer, CommentTokenizer


def get_paren_tokenizers():
    return LitTokenizer, IDTokenizer, ParenTokenizer, SymbolTokenizer, NewlineConsumerTokenizer, FormattingTokenizer, CommentTokenizer


class TokenizerClosed(Exception):
    pass


class BaseTokenizer(ABC):
    @abstractmethod
    def feed_character(self, char):
        pass

    def close(self):
        """Finish such that next time tokenizer asked to handle character, it will raise TokenizerIsClosed"""
        self.handle_char = self._raise_closed
        self.should_enter = self._raise_closed

    def _raise_closed(self, token):
        raise TokenizerClosed

    def get_tokens(self):
        return
        yield


class SelectableTokenizer(BaseTokenizer):
    @abstractclassmethod
    def should_enter(self, char):
        pass


class TextTokenizer(SelectableTokenizer):
    def __init__(self):
        super().__init__()

        self._chars = []

    @property
    def string(self):
        return ''.join(self._chars)

    def handle_text_char(self, char):
        self._chars.append(char)


class LitTokenizer(TextTokenizer):
    sentinel_char = "'"

    @classmethod
    def should_enter(cls, char):
        return char == cls.sentinel_char

    def feed_character(self, char):
        self.handle_text_char(char)

        # First character is always the one that opens this tokenizer
        if char == self.sentinel_char and len(self._chars) > 1:
            return TokenizerState.handled
        return TokenizerState.running

    def get_tokens(self):
        yield Token('LIT', literal_eval(self.string))


class IDTokenizer(TextTokenizer):
    """Consumes Python identifiers"""

    @classmethod
    def should_enter(cls, char):
        return char.isalpha()

    def feed_character(self, char):
        is_valid = (self.string + char).isidentifier()
        if not is_valid:
            return TokenizerState.unhandled

        self.handle_text_char(char)
        return TokenizerState.running

    def get_tokens(self):
        yield Token('ID', self.string)


class ParenTokenizer(SelectableTokenizer):
    entry_to_exit_parens = {'(': ')', '[': ']', '{': '}'}

    def __init__(self):
        super().__init__()

        self._entry_paren = None
        self._exit_paren = None

        tokenizers = get_paren_tokenizers()
        self._token_generator = TokenGenerator(tokenizers)

    @classmethod
    def should_enter(cls, char):
        return char in cls.entry_to_exit_parens

    def feed_character(self, char):
        assert char in self.entry_to_exit_parens
        self._entry_paren = char
        self._exit_paren = self.entry_to_exit_parens[char]
        self.feed_character = self.handle_char_following_paren
        return TokenizerState.running

    def handle_char_following_paren(self, char):
        try:
            self._token_generator.feed_character(char)

        except ValueError:
            if char == self._exit_paren:
                return TokenizerState.handled
            raise

        return TokenizerState.running

    def get_tokens(self):
        yield Token(self._entry_paren, self._entry_paren)
        yield from self._token_generator.get_tokens()
        yield Token(self._exit_paren, self._exit_paren)


class SymbolTokenizer(SelectableTokenizer):
    symbols = frozenset(r'!"$%&\'*+,-./:;<=>?@^_`|~')

    def __init__(self):
        super().__init__()

        self._char = None

    @classmethod
    def should_enter(cls, char):
        return char in cls.symbols

    def feed_character(self, char):
        self._char = char
        return TokenizerState.handled

    def get_tokens(self):
        yield Token(self._char, self._char)


class NewlineConsumerTokenizer(SelectableTokenizer):
    """Consume newlines and don't generate Tokens for them. Only valid inside parentheses"""

    @classmethod
    def should_enter(cls, char):
        return char == '\n'

    def feed_character(self, char):
        return TokenizerState.handled


class NewlineTokenizer(NewlineConsumerTokenizer):
    def get_tokens(self):
        yield Token('\n', '\n')


class FormattingTokenizer(SelectableTokenizer):
    @classmethod
    def should_enter(cls, char):
        return char in {' ', '\t'}

    def feed_character(self, char):
        return TokenizerState.handled


class CommentTokenizer(SelectableTokenizer):
    @classmethod
    def should_enter(cls, char):
        return char == '#'

    def feed_character(self, char):
        if char == '\n':
            return TokenizerState.unhandled
        return TokenizerState.running


class TokenGenerator(BaseTokenizer):
    """Generates Token instance from a list of valid tokenizers"""

    def __init__(self, tokenizers):
        self._tokenizers = tokenizers
        self._current_tokenizer = None
        self._token_iterables = []

    def feed_character(self, char):
        while True:
            if self._current_tokenizer is None:
                self._current_tokenizer = select_tokenizer_for(char, self._tokenizers)

            state = self._current_tokenizer.feed_character(char)

            if state != TokenizerState.running:
                tokens_iterable = self._current_tokenizer.get_tokens()
                self._token_iterables.append(tokens_iterable)
                self._current_tokenizer.close()
                self._current_tokenizer = None

            if state != TokenizerState.unhandled:
                break

    def get_tokens(self):
        iterable = chain.from_iterable(self._token_iterables.copy())
        self._token_iterables.clear()
        yield from iterable


def select_tokenizer_for(char, tokenizers):
    """Return instance of first parser that can handle given character"""
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
        token_generator.feed_character(char)
        yield from token_generator.get_tokens()

    yield Token('ENDMARKER', 'ENDMARKER')
