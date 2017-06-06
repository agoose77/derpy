import token
import tokenize
from io import StringIO
from keyword import iskeyword
from tokenize import generate_tokens

from derp.parsers import Token


FUNNEL_KEYWORDS = frozenset(['Type', 'Enum', 'form', 'validate'])

def is_keyword(word):
    if iskeyword(word):
        return True

    return word in FUNNEL_KEYWORDS


def tokenize_text(source):
    string_io = StringIO(source + "\n")
    return tokenize_readline(string_io.readline)


def tokenize_file(filename):
    with open(filename) as f:
        string_io = StringIO(f.read() + "\n")
    return tokenize_readline(string_io.readline)


def tokenize_readline(readline):
    for tok_info in generate_tokens(readline):

        if tok_info.type == token.NAME:
            value = tok_info.string
            if is_keyword(value):
                yield Token(value, value)

            else:
                yield Token('ID', tok_info.string)

        elif tok_info.type == token.STRING:
            yield Token('LIT', eval(tok_info.string))

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
            yield Token("##", '##')
            tokens = list(tokenize_text(tok_info.string[2:]))
            yield from iter(tokens[1:-2]) # String indent and dedent+EOF
            yield Token("NEWLINE", "NEWLINE")

        elif tok_info.type == tokenize.NL:
            continue

        else:
            yield Token(tok_info.string, tok_info.string)
