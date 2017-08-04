from derp.grammar import Grammar
from derp.parsers import lit
from derp.utilities import unpack
from grammars.ebnf import ast


def emit_grammar_parser(args):
    any_rules_or_nl, end_marker = args
    rules = tuple([r for r in any_rules_or_nl if r != '\n'])
    return ast.Grammar(rules)


def emit_lit_parser(text):
    return ast.LitParser(text)


def emit_opt_parser(args):
    _, child, _ = unpack(args, 3)
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
    _, child, _ = unpack(args, 3)
    return ast.GroupParser(child)


def emit_definition(args):
    name, _, child, _ = unpack(args, 4)
    return ast.RuleDefinition(name, child)


def emit_file(args):
    lines, _ = args
    return ast.Grammar(tuple(l for l in lines if not l == '\n'))


def emit_alt_parser(args):
    node, expr_tuple = unpack(args, 2)
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


def emit_comment(comment):
    return ast.Comment(comment)


e = Grammar('EBNF')

e.alt = (e.cat & +(lit('|') & e.cat)) >> emit_alt_parser
e.cat = (e.star & +e.star) >> emit_concat_parser
e.star = (e.plus & ~lit('*')) >> emit_star
e.plus = (e.element & ~lit('+')) >> emit_plus

e.optional = (lit('[') & e.alt & lit(']')) >> emit_opt_parser
e.grouped = (lit('(') & e.alt & lit(')')) >> emit_group_parser

e.element = lit('ID') >> emit_id | e.grouped | e.optional | lit('LIT') >> emit_lit

e.rule = (lit('ID') & lit(':') & e.alt & lit('\n')) >> emit_definition
e.comment = lit('COMMENT') >> emit_comment
e.grammar = (+(e.rule | lit('\n') | e.comment) & lit('ENDMARKER')) >> emit_grammar_parser

e.ensure_parsers_defined()
