from derp.parsers import lit, star
from derp.grammar import Grammar
from derp.utilities import unpack_n

from . import ast


def emit_grammar_parser(text):
    return ast.RuleReference(text)


def emit_lit_parser(text):
    return ast.LitParser(text)


def emit_opt_parser(args):
    _, child, _ = unpack_n(args, 3)
    return ast.OptParser(child)


def emit_one_plus_parser(args):
    elem, _ = args
    return ast.OnePlusParser(elem)


def emit_many_parser(args):
    elem, _ = args
    return ast.ManyParser(elem)


def emit_group_parser(args):
    _, child, _ = unpack_n(args, 3)
    return ast.GroupParser(child)


def emit_definition(args):
    name, _, child = unpack_n(args, 3)
    return ast.RuleDefinition(name, child)


def emit_multiline(args):
    parser, _ = args
    return parser,


def emit_root(args):
    elem, root = args
    if root == '':
        return elem
    if elem == '\n':
        return root
    return ast.ConcatParser(elem, root)


def emit_file(args):
    lines, _ = args
    return ast.Grammar(tuple(l for l in lines if not l == '\n'))


def emit_alt_parser(args):
    left, _, right = unpack_n(args, 3)
    return ast.AltParser(left, right)


b = Grammar('EBNF')
# b.suite = (b.group_elem & ~b.suite) >> emit_root
#
# b.parse_definition = (lit('ID') & lit(':') & b.suite) >> emit_definition
# b.element = lit('LIT') >> emit_lit_parser | lit('ID') >> emit_grammar_parser
#
# #b.multiline_suite = ((b.all_elements | lit('NEWLINE')) & ~b.multiline_suite) >> emit_root
#
# b.group_elem = (lit('(') & b.opt_elem & lit(')')) | b.opt_elem
# b.opt_elem = (lit('[') & b.or_expr & lit(']')) | b.or_expr
# b.or_expr = b.and_expr & +(lit('|') & b.and_expr)
# b.and_expr = b.one_plus & +b.one_plus
# b.one_plus = (b.any_n & lit('+'))# >> emit_one_plus_parser
# b.any_n  = (b.element & lit('*'))
#
#
# b.file_input = (+(lit('NEWLINE') | b.parse_definition) & lit('ENDMARKER')) >> emit_file

b.identifier = lit('ID')
b.lhs = b.identifier
b.rhs = b.identifier | lit('LIT') | b.optional | b.repeated | b.repeated | b.alternate
b.non_concatenating = star(b.rhs)
b.non_alternating = b.identifier | lit('LIT') | b.optional | b.repeated | b.repeated

b.optional = lit('[') & b.non_concatenating & lit(']')
b.repeated = lit('{') & b.non_concatenating & lit('}')
b.grouped = lit('(') & b.non_concatenating & lit(')')
b.alternate = b.non_alternating & star(lit('|') & b.non_alternating)

b.rule = b.lhs & lit(':') & b.non_concatenating & lit('\n')
b.grammar = +(b.rule | lit('\n')) & lit('ENDMARKER')

b.ensure_parsers_defined()
