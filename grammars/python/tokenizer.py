import token
import tokenize
from io import StringIO
from keyword import iskeyword
from tokenize import generate_tokens

from ast import literal_eval
from derp import Token, BaseTokenizer

from typing import Iterable, Callable
from os import PathLike


class PythonTokenizer(BaseTokenizer):


    def tokenize_text(self, source: str) -> Iterable[Token]:
        string_io = StringIO(source + '\n')
        return self.tokenize_readline(string_io.readline)


    def tokenize_file(self, filename: PathLike) -> Iterable[Token]:
        with open(filename) as f:
            string_io = StringIO(f.read() + '\n')
        return self.tokenize_readline(string_io.readline)

    def tokenize_readline(self, readline: Callable[[]]) -> Iterable[Token]:
        for tok_info in generate_tokens(readline):
            if tok_info.type == token.NAME:
                value = tok_info.string
                if iskeyword(value):
                    yield Token(value, value)

                else:
                    yield Token('ID', tok_info.string)

            elif tok_info.type == token.STRING:
                yield Token('LIT', literal_eval(tok_info.string))

            elif tok_info.type == token.NUMBER:
                yield Token('NUMBER', tok_info.string)

            elif tok_info.type in {token.NEWLINE}:
                yield Token("NEWLINE", "NEWLINE")

            elif tok_info.type == token.INDENT:
                yield Token("INDENT", "INDENT")

            elif tok_info.type == token.DEDENT:
                yield Token("DEDENT", "DEDENT")

            elif tok_info.type == token.ERRORTOKEN:
                yield Token("ERROR", tok_info.string)

            elif tok_info.type == token.ENDMARKER:
                yield Token("ENDMARKER", "ENDMARKER")

            elif tok_info.type == tokenize.COMMENT:
                continue

            elif tok_info.type == tokenize.NL:
                continue

            else:
                yield Token(tok_info.string, tok_info.string)
