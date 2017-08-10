from derp import Grammar, lit, unpack, selects, select
from grammars.ebnf import ast


def emit_grammar_parser(args):
    any_rules_or_nl, end_marker = args
    rules = tuple([r for r in any_rules_or_nl if r != '\n'])
    return ast.Grammar(rules)

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


e = Grammar('EBNF')

e.alt = (e.cat & (lit('|') & e.cat)[...]) >> emit_alt_parser
e.cat = (e.star & e.star[...]) >> emit_concat_parser
e.star = (e.plus & ~lit('*')) >> emit_star
e.plus = (e.element & ~lit('+')) >> emit_plus

e.optional = (lit('[') & e.alt & lit(']')) >> select(3, 1) >> ast.OptParser
e.grouped = (lit('(') & e.alt & lit(')')) >> select(3, 1) >> ast.GroupParser

e.element = (lit('ID') >> ast.ID |
             lit('LIT') >> ast.LitParser |
             e.grouped |
             e.optional)

e.rule = (lit('ID') & lit(':') & e.alt & lit('\n')) >> selects(4, 0, 2) >> ast.RuleDefinition._make
e.comment = (lit('COMMENT') & lit('\n')) >> select(2, 0) >> ast.Comment

e.stmt = e.rule | e.comment | lit('\n')

e.grammar = (e.stmt[...] & lit('ENDMARKER')) >> emit_grammar_parser

e.freeze()
