"""Generated grammar from funnel EBNF"""
from derp.grammar import Grammar
from derp.parsers import lit, star
from derp.utilities import unpack_n
from grammars.funnel import ast
from grammars.python import ast as py_ast
from grammars.python.grammar import p


def emit_module(args):
    type_defs, endmarker = args
    valid_stmts = tuple([type_def for type_def in type_defs if type_def != '\n'])
    return ast.FunnelModule(valid_stmts)


def emit_type(args):
    _, name, _, body = unpack_n(args, 4)
    return ast.FunnelType(name, body)


def emit_suite(args):
    _, _, stmts, _ = unpack_n(args, 4)
    valid_stmts = tuple([s for s in stmts if s != '\n'])
    return valid_stmts


def emit_enum(args):
    _, name, _, first_opt, option_pairs, _ = unpack_n(args, 6)
    _, options = zip(*option_pairs)
    all_options = (first_opt,) + options
    return ast.EnumType(name, all_options)


def emit_int(args):
    _, name = args
    return ast.IntegerType(name)


def emit_string(args):
    _, name = args
    return ast.IntegerType(name)


def emit_bool(args):
    _, name = args
    return ast.IntegerType(name)


def emit_other(args):
    type_name, name = args
    return ast.OtherType(name, type_name)


def emit_nullable(args):
    _, field, _ = unpack_n(args, 3)
    return ast.NullableField(field)


def emit_default_decl(args):
    field_type, assignment, _ = unpack_n(args, 3)
    if assignment == '':
        return field_type

    _, value = assignment
    return ast.DefaultField(field_type, value)


def emit_form_block(args):
    _, _, body = unpack_n(args, 3)
    return ast.FormBlock(body)


def emit_validate_block(args):
    _, _, body = unpack_n(args, 3)
    return ast.ValidateBlock(body)


def emit_if_stmt(args):
    _, test, _, body = unpack_n(args, 4)
    return py_ast.If(test, (body,), ()),


f = Grammar('Demo BNF')
f.file_input = (+(f.type | lit('NEWLINE')) & lit('ENDMARKER')) >> emit_module
f.type = (lit('Type') & lit('ID') & lit(':') & f.suite) >> emit_type
f.suite = (lit('NEWLINE') & lit('INDENT') & star((f.body_stmt | lit('NEWLINE'))) & lit('DEDENT')) >> emit_suite
f.body_stmt = f.stmt | f.block
f.stmt = f.declaration_stmt
f.declaration_stmt = f.default_decl_stmt | f.nullable_decl_stmt
f.default_decl_stmt = ((f.enum & ~(lit('=') & lit('LIT')) |
                        f.integer & ~(lit('=') & lit('NUMBER')) |
                        f.string & ~(lit('=') & lit('LIT')) |
                        f.bool & ~(lit('=') & (lit('True') | lit('False'))) |
                        f.other & ~(lit('=') & f.py_expr_stmt)) & lit('NEWLINE')) >> emit_default_decl

f.nullable_decl_stmt = (lit('*') & (f.string | f.enum | f.integer | f.bool | f.other) & lit('NEWLINE')) >> emit_nullable
f.enum = (lit('Enum') & lit('ID') & lit('(') & lit('LIT') & star((lit(',') & lit('LIT'))) & lit(')')) >> emit_enum
f.integer = (lit('Integer') & lit('ID')) >> emit_int
f.string = (lit('String') & lit('ID')) >> emit_string
f.bool = (lit('Bool') & lit('ID')) >> emit_bool
f.other = (lit('ID') & lit('ID')) >> emit_other
f.block = f.form_block | f.validate_block
f.form_block = (lit('form') & lit(':') & f.block_suite) >> emit_form_block
f.validate_block = (lit('validate') & lit(':') & f.block_suite) >> emit_validate_block

f.block_suite = f.py_suite | f.if_stmt_inline
f.if_stmt_inline = (lit('if') & f.py_test & lit(':') & f.py_simple_stmt) >> emit_if_stmt

f.py_expr_stmt = p.expr_stmt
f.py_simple_stmt = p.simple_stmt
f.py_test = p.test
f.py_suite = p.suite
f.ensure_parsers_defined()
