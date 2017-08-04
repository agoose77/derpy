from .token import Token

FLOAT_REGEX = r"((^[0-9])|(^[1-9][0-9]*))\.[0-9]+$"
INT_REGEX = r"^[1-9][0-9]*$"

from ast import literal_eval
from re import compile as re_compile, escape
from typing import Generator, Dict, Any, Tuple

PatternType = type(re_compile('.'))
MatchType = type(re_compile('.').match(' '))


class Tokenizer:
    """Basic REGEX matching tokenizer / lexer. Similar API to AST NodeVisitor, define/overload handle_XXX methods 
    corresponding to pattern names in the patterns table.
    
    Patterns priority ordered highest to lowest.
    """
    NO_MATCH_NAME: str = "NO_MATCH"
    OP_CHARACTERS: str = "+/-*^%!~@.<>&|"
    PAREN_CHARACTERS: str = "()[]{}"

    keywords: frozenset = frozenset()
    patterns: Tuple[Tuple[str, str], ...] = (
        ('NUMBER', r'\d+(\.\d*)?'),
        ('LIT', r"'([^']+)'"),
        ('ID', r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ('OP', r"|".join(escape(c) for c in OP_CHARACTERS)),
        ('PAREN', r"|".join(escape(c) for c in PAREN_CHARACTERS)),
        ('NEWLINE', r'\n'),
        ('FORMAT', r'[ \t]+'),
    )
    default_pattern: Tuple[str, str] = (NO_MATCH_NAME, r'.')

    def __init__(self):
        self.pattern: PatternType = self.create_pattern()

    def create_pattern(self) -> PatternType:
        patterns = self.patterns + (self.default_pattern,)
        full_match_string = "|".join(f'(?P<{n}>{m})' for n, m in patterns)
        return re_compile(full_match_string)

    def create_context(self, string: str) -> Dict[str, Any]:
        return {'line_number': 1, 'char_number': 0, 'string': string}

    def default_handler(self, match: MatchType, value, context: dict) -> Token:
        return Token(match.lastgroup, value)

    def get_error_string(self, match: MatchType, value, context: dict) -> str:
        index = match.start() - context['char_number']
        lines = context['string'].splitlines()
        line = lines[context['line_number'] - 1]

        indicator_string = ''.join('^' if i == index else ' ' for i, _ in enumerate(line))
        return f"Unable to match character {value!r} on line {context['line_number']}\n{line}\n{indicator_string}"

    def tokenize_text(self, string: str, force_trailing_newline: bool = False) -> Generator[Token, None, None]:
        if force_trailing_newline:
            string += "\n"

        context = self.create_context(string)

        for match in self.pattern.finditer(string):
            kind = match.lastgroup
            value = match.group(kind)

            if kind == self.NO_MATCH_NAME:
                raise ValueError(self.get_error_string(match, value, context))

            handler = getattr(self, f"handle_{kind}", self.default_handler)
            result = handler(match, value, context)
            if result is not None:
                yield result

        yield Token("ENDMARKER", "ENDMARKER")

    def tokenize_file(self, file_name: str, force_trailing_newline: bool = False) -> Generator[Token, None, None]:
        with open(file_name) as f:
            yield from self.tokenize_text(f.read(), force_trailing_newline)

    def handle_OP(self, match: MatchType, value, context: dict) -> Token:
        return Token(value, value)

    handle_PAREN = handle_OP

    def handle_ID(self, match: MatchType, value, context: dict) -> Token:
        if value in self.keywords:
            kind = value
        else:
            kind = "ID"

        return Token(kind, value)

    def handle_FORMAT(self, match: MatchType, value, context: dict) -> None:
        pass

    def handle_NEWLINE(self, match: MatchType, value, context: dict) -> Token:
        context['char_number'] = match.end()
        context['line_number'] += 1

        return Token("NEWLINE", value)

    def handle_NUMBER(self, match: MatchType, value, context: dict) -> Token:
        return Token("NUMBER", literal_eval(value))
