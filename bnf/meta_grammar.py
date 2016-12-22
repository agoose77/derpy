from derp.parsers import ter
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

b = Grammar('meta-BNF')
b.suite = (b.all_elements & ~b.suite) >> emit_root

b.parse_definition = (ter('ID') & ter(':') & b.suite) >> emit_definition
b.element = ter('LIT') >> emit_lit_parser | ter('ID') >> emit_grammar_parser

b.multiline_suite = ((b.all_elements | ter('NEWLINE')) & ~b.multiline_suite) >> emit_root

b.opt_elem = (ter('[') & b.multiline_suite & ter(']')) >> emit_opt_parser
b.group_elem = (ter('(') & b.multiline_suite & ter(')')) >> emit_group_parser

b.multiline_elements = b.opt_elem | b.group_elem

b.any_elem = (b.all_elements & ter('*')) >> emit_many_parser
b.one_plus_elem = (b.all_elements & ter('+')) >> emit_one_plus_parser
b.or_elem = (b.all_elements & ter('|') & b.all_elements) >> emit_alt_parser

b.all_elements = b.element | b.any_elem | b.multiline_elements | b.or_elem | b.one_plus_elem

b.file_input = (+(ter('NEWLINE') | b.parse_definition) & ter('ENDMARKER')) >> emit_file

b.ensure_parsers_defined()
