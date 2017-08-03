from .token import Token

FLOAT_REGEX = r"((^[0-9])|(^[1-9][0-9]*))\.[0-9]+$"
INT_REGEX = r"^[1-9][0-9]*$"

from ast import literal_eval
from re import compile as re_compile, escape


class Tokenizer:
    NO_MATCH_NAME = "NO_MATCH"
    OP_CHARACTERS = "+/-*^%!~@.<>&|"
    PAREN_CHARACTERS = "()[]{}"

    keywords = frozenset()
    patterns = (
        ('NUMBER', r'\d+(\.\d*)?'),
        ('LIT', r"'([^']+)'"),
        ('ID', r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ('OP', r"|".join(escape(c) for c in OP_CHARACTERS)),
        ('PAREN', r"|".join(escape(c) for c in PAREN_CHARACTERS)),
        ('NEWLINE', r'\n'),
        ('FORMAT', r'[ \t]+'),
    )
    default_pattern = (NO_MATCH_NAME, r'.')

    def __init__(self):
        self.pattern = self.create_pattern()

    def create_pattern(self):
        patterns = self.patterns + (self.default_pattern,)
        full_match_string = "|".join(f'(?P<{n}>{m})' for n, m in patterns)
        return re_compile(full_match_string)

    def create_context(self, string):
        return {'line_number': 1, 'char_number': 0, 'string': string}

    def default_handler(self, match, value, context):
        return Token(match.lastgroup, value)

    def get_error_string(self, match, value, context):
        index = match.start() - context['char_number']
        lines = context['string'].splitlines()
        line = lines[context['line_number'] - 1]

        indicator_string = ''.join('^' if i == index else ' ' for i, _ in enumerate(line))
        return f"Unable to match character {value!r} on line {context['line_number']}\n{line}\n{indicator_string}"

    def tokenize_text(self, string):
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

    def tokenize_file(self, file_name):
        with open(file_name) as f:
            yield from self.tokenize_text(f.read())

    def handle_OP(self, match, value, context):
        return Token(value, value)

    handle_PAREN = handle_OP

    def handle_ID(self, match, value, context):
        if value in self.keywords:
            kind = value
        else:
            kind = "ID"

        return Token(kind, value)

    def handle_FORMAT(self, match, value, context):
        pass

    def handle_NEWLINE(self, match, value, context):
        context['char_number'] = match.end()
        context['line_number'] += 1

        return Token("NEWLINE", value)

    def handle_NUMBER(self, match, value, context):
        return Token("NUMBER", literal_eval(value))
