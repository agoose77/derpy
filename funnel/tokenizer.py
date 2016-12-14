from derp import Token
from python.tokenizer import tokenize_readline as py_tokenize_readline
from io import StringIO


def tokenize_text(source):
    string_io = StringIO(source + '\n')
    return tokenize_readline(string_io.readline)


def tokenize_file(filename):
    with open(filename) as f:
        string_io = StringIO(f.read() + '\n')
    return tokenize_readline(string_io.readline)


def tokenize_readline(readline):
    keywords = {'Type', 'form', 'validate'}
    for token in py_tokenize_readline(readline):
        if token.first == 'ID' and token.second in keywords:
            yield Token(token.second, token.second)
        else:
            yield token

