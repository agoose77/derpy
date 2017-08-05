from unittest import TestCase, main

from derp import parse, Token
from grammars.ebnf import e, EBNFTokenizer, ast

test_string = """dog: (NAME 'barked')+ 'woof'*"""

expected_ast = ast.Grammar(
    rules=(
        ast.RuleDefinition(
            name='dog',
            parser=ast.ConcatParser(
                left=ast.OnePlusParser(
                    child=ast.GroupParser(
                        child=ast.ConcatParser(
                            left=ast.ID(
                                name='NAME'
                            ),
                            right=ast.LitParser(
                                lit="'barked'"
                            )
                        )
                    )
                ),
                right=ast.ManyParser(
                    child=ast.LitParser(
                        lit="'woof'"
                    )
                )
            )
        ),
    )
)

expected_tokens = (
    Token('ID', 'dog'),
    Token(':', ':'),
    Token('(', '('),
    Token('ID', 'NAME'),
    Token('LIT', "'barked'"),
    Token(')', ')'),
    Token('+', '+'),
    Token('LIT', "'woof'"),
    Token('*', '*'),
    Token('\n', '\n'),
    Token('ENDMARKER', 'ENDMARKER')
)


class TestParseEBNF(TestCase):
    def test_tokens(self):
        tokens = tuple(EBNFTokenizer().tokenize_text(test_string, force_trailing_newline=True))
        self.assertTupleEqual(tokens, expected_tokens)

    def test_parse_tree(self):
        tokens = tuple(EBNFTokenizer().tokenize_text(test_string, force_trailing_newline=True))
        parse_trees = parse(e.grammar, tokens)
        self.assertEqual(len(parse_trees), 1)
        module = next(iter(parse_trees))
        self.assertEqual(module, expected_ast)


if __name__ == "__main__":
    main()
