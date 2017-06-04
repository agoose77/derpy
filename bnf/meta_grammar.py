from derp.grammar import Grammar
from derp.parsers import lit
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

b.parse_definition = (lit('ID') & lit(':') & b.suite) >> emit_definition
b.element = lit('LIT') >> emit_lit_parser | lit('ID') >> emit_grammar_parser

b.multiline_suite = ((b.all_elements | lit('NEWLINE')) & ~b.multiline_suite) >> emit_root

b.opt_elem = (lit('[') & b.multiline_suite & lit(']')) >> emit_opt_parser
b.group_elem = (lit('(') & b.multiline_suite & lit(')')) >> emit_group_parser

b.multiline_elements = b.opt_elem | b.group_elem

b.any_elem = (b.all_elements & lit('*')) >> emit_many_parser
b.one_plus_elem = (b.all_elements & lit('+')) >> emit_one_plus_parser
b.or_elem = (b.all_elements & lit('|') & b.all_elements) >> emit_alt_parser

b.all_elements = b.element | b.any_elem | b.multiline_elements | b.or_elem | b.one_plus_elem

b.file_input = (+(lit('NEWLINE') | b.parse_definition) & lit('ENDMARKER')) >> emit_file

b.ensure_parsers_defined()
