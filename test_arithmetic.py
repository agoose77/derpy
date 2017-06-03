from argparse import ArgumentParser
from derp.grammar import Grammar
from derp.parsers import Token, parse, lit, alt
from derp.utilities import unpack_n


def apply(op, seq):
    """Apply operator to sequence item pairs"""
    node, *remainder = list(seq)
    for next_node in remainder:
        node = op(node, next_node)
    return node


def emit_add_expr(args):
    l, _, r = unpack_n(args, 3)
    return ('add', l, r)


def emit_mult_expr(args):
    l, _, r = unpack_n(args, 3)
    return ('mult', l, r)


def emit_bracketed(args):
    l, body, r = unpack_n(args, 3)
    return body


def emit_expr(expr):
    return ('expr', expr)


g = Grammar('arith')
g.digit = apply(alt, [lit(str(i)) for i in range(10)])
g.number = g.digit >> int
g.add_op = lit('+') | lit('-')
g.add_expr = g.mult_expr | (g.mult_expr & g.add_op & g.mult_expr) >> emit_add_expr
g.mult_op = lit('*') | lit('/')
g.value = g.number | (lit('(') & g.add_expr & lit(')')) >> emit_bracketed
g.mult_expr = g.value | (g.value & g.mult_op & g.value) >> emit_mult_expr
g.expr = g.add_expr >> emit_expr


# Greedy
def make_tokens(string):
    return [Token(c, c) for c in string]


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-expr", type=str, default="(1*3)/4")
    args = parser.parse_args()

    tokens = make_tokens(args.expr)
    result = parse(g.expr, tokens)

    print(result)
