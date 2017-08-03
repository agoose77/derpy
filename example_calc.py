from functools import partial

from derp.ast import AST
from derp.ast import NodeVisitor
from derp.grammar import Grammar
from derp.parsers import lit, parse, Token
from derp.utilities import unpack_n

Compound = AST.subclass("Compound", "left right")
Add = Compound.subclass("Add")
Sub = Compound.subclass("Sub")
Mul = Compound.subclass("Mul")
Div = Compound.subclass("Div")

FLOAT_REGEX = r"((^[0-9])|(^[1-9][0-9]*))\.[0-9]+$"
INT_REGEX = r"^[1-9][0-9]*$"


from ast import literal_eval
from re import compile as re_compile, escape


class Tokenizer:
    NO_MATCH_NAME = "NO_MATCH"
    OP_CHARACTERS = "+/-*^%!~@.<>&[]()"
    keywords = frozenset()
    patterns = [
        ('NUMBER', r'\d+(\.\d*)?'),
        ('LIT', r"'([^']+)"),
        ('ID', r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ('OP', r"|".join(escape(c) for c in OP_CHARACTERS)),
        ('NEWLINE', r'\n'),
        ('FORMAT',    r'[ \t]+'),
        (NO_MATCH_NAME, r'.')
    ]

    def __init__(self):
        full_match_string = "|".join(f'(?P<{n}>{m})' for n, m in self.patterns)
        self.pattern = re_compile(full_match_string)

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

    def handle_OP(self, match, value, context):
        return Token(value, value)

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


def emit_compound(f, args):
    l, _, r = unpack_n(args, 3)
    print("COMP",f(l,r))
    return f(l, r)


def emit_neg(args):
    return args[1]


def emit_paren(args):
    _, x, _ = unpack_n(args, 3)
    return x


g = Grammar("Calc")
g.sum = (g.product |
         (g.sum & lit('+') & g.product) >> partial(emit_compound, Add) |
         (g.sum & lit('-') & g.product) >> partial(emit_compound, Sub)
         )
g.product = (g.item |
             (g.product & lit('*') & g.item) >> partial(emit_compound, Mul) |
             (g.product & lit('/') & g.item) >> partial(emit_compound, Div)
             )
g.item = (lit('NUMBER') |
          (lit('-') & g.item) >> emit_neg |
          ((lit('(') & g.sum & lit(')')) >> emit_paren)
          )


import operator
class EvalVisitor(NodeVisitor):
    eval_table = {Sub: operator.sub,
                  Mul: operator.mul,
                  Div: operator.truediv,
                  Add: operator.add}

    def generic_visit(self, node, *args, **kwargs):
        node_type = type(node)
        try:
            op = self.eval_table[node_type]
        except KeyError:
            if not isinstance(node, AST):
                return node
            return super().generic_visit(node, *args, **kwargs)

        left = self.visit(node.left)
        right = self.visit(node.right)
        return op(left, right)


def eval_ast(ast):
    visitor = EvalVisitor()
    result = visitor.visit(ast)
    print(result)


if __name__ == "__main__":
    tokens = Tokenizer().tokenize_text(
        """99+1+2+3*4"""
    )

    from pprint import pprint
    tokens = list(tokens)
    pprint(tokens)

    ast = parse(g.sum, tokens).pop()

    eval_ast(ast)
