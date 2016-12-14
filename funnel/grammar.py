from python.grammar import g, Grammar
from . import ast
from derp import ter, one_plus
from derp.utilities import unpack_n


def emit_file_input(args):
    many_stmts, _ = args
    if many_stmts == '':
        many_stmts = ()

    return ast.Funnel(many_stmts)

def emit_type_def(args):
    _, name, _, body = unpack_n(args, 4)
    return ast.TypeDef(name, body)

def emit_nl_indented(args):
    _, _, list_of_stmts, _ = unpack_n(args, 4)
    stmts = []
    for n in list_of_stmts:
        if isinstance(n, ast.AST):
            stmts.append(n)
        else:
            stmts.extend(n)
    return tuple(stmts)

def emit_enum_body(args):
    first, remainder = args
    if remainder == '':
        return first,
    commas, lits = zip(*remainder)
    return (first,) + lits

def emit_enum_options(args):
    _, body, _ = unpack_n(args, 3)
    return body

def emit_opt_attr_def(args):
    _, typename, name, opt_options = unpack_n(args, 4)

    # If Enum
    if opt_options != '':
        if typename != "Enum":
            raise SyntaxError

        return ast.EnumAttrDef(typename, name, opt_options, None, True)

    return ast.AttrDef(typename, name, None, True)

def emit_default_attr_def(args):
    typename, name, opt_options, opt_assign = unpack_n(args, 4)

    if opt_assign != '':
        _, value = opt_assign
    else:
        value = None

    # If Enum
    if opt_options != '':
        if typename != "Enum":
            raise SyntaxError

        return ast.EnumAttrDef(typename, name, opt_options, value, False)

    return ast.AttrDef(typename, name, value, False)

def emit_simple_stmt(args):
    first_stmt, remainder, opt_colon, newline = unpack_n(args, 4)
    if remainder != '':
        all_stmts = (first_stmt,) + tuple(s for c, s in remainder)
    else:
        all_stmts = first_stmt

    return all_stmts

def emit_form(args):
    _, _, body = unpack_n(args, 3)
    return ast.FormDef(body)

def emit_validate(args):
    _, _, body = unpack_n(args, 3)
    return ast.ValidateDef(body)

f = Grammar('Funnel')

f.form = (ter('form') & ter(':') & g.suite) >> emit_form
f.validate = (ter('validate') & ter(':') & g.suite) >> emit_validate

f.type_def = (ter('Type') & ter('ID') & ter(':') & f.suite) >> emit_type_def
f.enum_body = (ter('LIT') & +(ter(',') & ter('LIT'))) >> emit_enum_body
f.enum_options = (ter("(") & ~f.enum_body & ter(")")) >> emit_enum_options

f.attribute_def = (ter('*') & ter('ID') & ter('ID') & ~f.enum_options) >> emit_opt_attr_def | \
                  (ter('ID') & ter('ID') & ~f.enum_options & ~(ter('=') & g.atom)) >> emit_default_attr_def

f.stmt = f.simple_stmt | f.compound_stmt
f.small_stmt = f.attribute_def
f.simple_stmt = (f.small_stmt & +(ter(';') & f.small_stmt) & ~ter(';') & ter('NEWLINE')) >> emit_simple_stmt
f.compound_stmt = f.validate | f.form

f.suite = f.simple_stmt | (ter('NEWLINE') & ter('INDENT') & one_plus(f.stmt) & ter('DEDENT')) >> emit_nl_indented
f.file_input = (+(ter('NEWLINE') | f.type_def) & ter('ENDMARKER')) >> emit_file_input

f.ensure_parsers_defined()
