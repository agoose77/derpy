from derp.grammar import Grammar
from derp.parsers import lit
from derp.utilities import unpack_n
from grammars.ebnf import ast


def emit_grammar_parser(args):
    any_rules_or_nl, end_marker = args
    rules = tuple([r for r in any_rules_or_nl if r != '\n'])
    return ast.Grammar(rules)


def emit_lit_parser(text):
    return ast.LitParser(text)


def emit_opt_parser(args):
    _, child, _ = unpack_n(args, 3)
    return ast.OptParser(child)


def emit_star(args):
    elem, plus = args
    if plus:
        return ast.ManyParser(elem)
    return elem


def emit_plus(args):
    elem, plus = args
    if plus:
        return ast.OnePlusParser(elem)
    return elem


def emit_group_parser(args):
    _, child, _ = unpack_n(args, 3)
    return ast.GroupParser(child)


def emit_definition(args):
    name, _, child, _ = unpack_n(args, 4)
    return ast.RuleDefinition(name, child)


def emit_file(args):
    lines, _ = args
    return ast.Grammar(tuple(l for l in lines if not l == '\n'))


def emit_alt_parser(args):
    node, expr_tuple = unpack_n(args, 2)
    if expr_tuple:
        _, exprs = zip(*expr_tuple)
        for expr in exprs:
            node = ast.AltParser(node, expr)
    return node


def emit_concat_parser(args):
    node, exprs = args
    if exprs:
        for expr in exprs:
            node = ast.ConcatParser(node, expr)
    return node


def emit_id(id_):
    return ast.ID(id_)


def emit_lit(lit):
    return ast.LitParser(lit)


b = Grammar('EBNF')

b.alt = (b.cat & +(lit('|') & b.cat)) >> emit_alt_parser
b.cat = (b.star & +b.star) >> emit_concat_parser
b.star = (b.plus & ~lit('*')) >> emit_star
b.plus = (b.element & ~lit('+')) >> emit_plus

b.optional = (lit('[') & b.alt & lit(']')) >> emit_opt_parser
b.grouped = (lit('(') & b.alt & lit(')')) >> emit_group_parser

b.element = lit('ID') >> emit_id | b.grouped | b.optional | lit('LIT') >> emit_lit

b.rule = (lit('ID') & lit(':') & b.alt & lit('\n')) >> emit_definition
b.grammar = (+(b.rule | lit('\n')) & lit('ENDMARKER')) >> emit_grammar_parser

b.ensure_parsers_defined()
