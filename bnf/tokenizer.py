from abc import ABC, abstractclassmethod
from derp import Token
from itertools import chain


def get_root_tokenizers():
    return LitTokenizer, IDTokenizer, ParenTokenizer, ColonTokenizer, GreedyTokenizer, OnePlusTokenizer, AltTokenizer,\
           NewlineTokenizer, FormattingTokenizer, CommentTokenizer


def get_paren_tokenizers():
    return LitTokenizer, IDTokenizer, ParenTokenizer, ColonTokenizer, GreedyTokenizer, OnePlusTokenizer, AltTokenizer,\
           NewlineConsumerTokenizer, FormattingTokenizer, CommentTokenizer


class BaseTokenizer(ABC):

    @abstractclassmethod
    def should_enter(self, char):
        pass

    def handle_char(self, char):
        pass

    def get_tokens(self):
        return
        yield


class SentinelTokenizer(BaseTokenizer):
    """A tokenizer which is able to determine that it is terminated from a sentinel value.
    The sentinel must therefore be consumed by this tokenizer"""

    def __init__(self):
        super().__init__()

        self._is_terminated = False

    def handle_terminating_char(self, char):
        pass

    def handle_char(self, char):
        if self._is_terminated:
            return True

        self._is_terminated = self.handle_terminating_char(char)
        return False


class TextTokenizerMixin:

    def __init__(self):
        super().__init__()

        self._chars = []

    @property
    def string(self):
        return ''.join(self._chars)

    def handle_text_char(self, char):
        self._chars.append(char)


class LitTokenizer(SentinelTokenizer, TextTokenizerMixin):
    sentinel_char = "'"

    @classmethod
    def should_enter(cls, char):
        return char == cls.sentinel_char

    def handle_terminating_char(self, char):
        self.handle_text_char(char)
        if len(self._chars) > 1 and char == self.sentinel_char:
            return True

        return False

    def get_tokens(self):
        yield Token("LIT", eval(self.string))


class IDTokenizer(TextTokenizerMixin, BaseTokenizer):
    """Consumes Python identifiers"""

    @classmethod
    def should_enter(cls, char):
        return char.isalpha()

    def handle_char(self, char):
        is_valid = (self.string + char).isidentifier()
        if not is_valid:
            return True

        self.handle_text_char(char)
        return False

    def get_tokens(self):
        yield Token("ID", self.string)


class TokenGenerator:

    def __init__(self, tokenizers):
        self._tokenizers = tokenizers
        self._tokenizer = None
        self._token_iterables = []

    def handle_char(self, char):
        while True:
            if self._tokenizer is None:
                self._tokenizer = select_tokenizer_for(char, self._tokenizers)

            # Couldn't handle this token, so True -> return please! TODO invert this
            if self._tokenizer.handle_char(char):
                self._token_iterables.append(self._tokenizer.get_tokens())
                self._tokenizer = None

            else:
                return self.flush_tokens()

    def flush_tokens(self):
        iterable = tuple(chain.from_iterable(self._token_iterables.copy()))
        self._token_iterables.clear()
        return iterable


class ParenTokenizer(SentinelTokenizer):
    entry_to_exit_parens = {'(': ')', '[':']'}

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

    def handle_terminating_char(self, char):
        # Consume first paren, and determine exit paren
        if self._exit_paren is None:
            assert char in self.entry_to_exit_parens
            self._entry_paren = char
            self._exit_paren = self.entry_to_exit_parens[char]

        # Delegate to child by default, unless it can't be handled
        else:
            try:
                self._token_iterables.append(self._token_generator.handle_char(char))
            except ValueError:
                assert char == self._exit_paren
                return True

        return False

    def get_tokens(self):
        yield Token(self._entry_paren, self._entry_paren)
        yield from chain.from_iterable(self._token_iterables)
        yield from self._token_generator.flush_tokens()
        yield Token(self._exit_paren, self._exit_paren)


class SymbolTokenizerBase(SentinelTokenizer):
    symbol = None

    def __init__(self):
        super().__init__()

        self._char = None

    @classmethod
    def should_enter(cls, char):
        return char == cls.symbol

    def handle_terminating_char(self, char):
        self._char = char
        return True

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


class FormattingTokenizer(SentinelTokenizer):

    @classmethod
    def should_enter(cls, char):
        return char in {' ', '\t'}

    def handle_terminating_char(self, char):
        return True


class CommentTokenizer(SentinelTokenizer):

    @classmethod
    def should_enter(cls, char):
        return char == '#'

    def handle_terminating_char(self, char):
        return char == '\n'


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

