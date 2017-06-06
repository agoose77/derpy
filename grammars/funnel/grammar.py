"""Generated grammar from funnel EBNF"""
from derp.grammar import Grammar
from derp.parsers import lit, star
from grammars.python.grammar import g

f = Grammar('Demo BNF')
f.file_input = +(f.type | lit('NEWLINE')) & lit('ENDMARKER')
f.type = lit('Type') & lit('ID') & lit(':') & f.suite
f.suite = lit('NEWLINE') & lit('INDENT') & star((f.body_stmt | lit('NEWLINE'))) & lit('DEDENT')
f.body_stmt = f.stmt | f.block
f.stmt = f.declaration_stmt
f.declaration_stmt = f.default_decl_stmt | f.required_decl_stmt
f.default_decl_stmt = (f.enum & ~(lit('=') & star(lit('LIT'))) | f.integer & ~(lit('=') & lit('NUMBER')) | f.string & ~(lit('=') & star(lit('LIT'))) | f.bool & ~(lit('=') & (lit('True') | lit('False'))) | f.other & ~(lit('=') & f.py_expr_stmt)) & lit('NEWLINE')

f.required_decl_stmt = lit('*') & (f.string | f.enum | f.integer | f.bool | f.other) & lit('NEWLINE')
f.enum = lit('Enum') & lit('ID') & lit('(') & lit('LIT') & star((lit(',') & lit('LIT'))) & lit(')')
f.integer = lit('Integer') & lit('ID')
f.string = lit('String') & lit('ID')
f.bool = lit('Bool') & lit('ID')
f.other = lit('ID') & lit('ID')
f.block = f.form_block | f.validate_block
f.form_block = lit('form') & lit(':') & f.block_suite
f.validate_block = lit('validate') & lit(':') & f.block_suite
def emit_suite(args):
    from grammars.python.codegen import to_source
    print(args)
    print(to_source(args[0]))

f.block_suite = f.py_suite >> emit_suite | f.if_stmt_inline
f.if_stmt_inline = lit('if') & f.py_test & lit(':') & f.py_simple_stmt
f.py_expr_stmt = g.expr_stmt
f.py_simple_stmt = g.simple_stmt
f.py_test = g.test
f.py_suite = g.suite
f.ensure_parsers_defined()

