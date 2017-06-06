from grammars.ebnf.generate import ParserGenerator as _ParserGenerator


class ParserGenerator(_ParserGenerator):
    grammar_declaration = """
from derp.grammar import Grammar
from derp.parsers import lit, star
from python.grammar import g

{variable} = Grammar({name!r})
{rules}
{variable}.py_expr_stmt = g.expr_stmt
{variable}.py_simple_stmt = g.simple_stmt
{variable}.py_test = g.test
{variable}.py_suite = g.suite
{variable}.ensure_parsers_defined()
"""
