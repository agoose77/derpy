from derp import parse, Token
from derp.ast import to_string, NodeTransformer
from grammars.python import p, tokenize_text, ast
from unittest import TestCase, main


tokens = tokenize_text("x = x + 1")
parse_trees = parse(p.file_input, tokens)
module = next(iter(parse_trees))

test_string = "x = x + 1"

expected_ast = ast.Module(
    (
        ast.Assign(
            (
                ast.Name('x'),
            ),
            ast.BinOp(
                ast.Name('x'),
                ast.Add(),
                ast.Num(1)
            )
        ),
    )
)

expected_tokens = (
    Token('ID', 'x'),
    Token('=', '='),
    Token('ID', 'x'),
    Token('+', '+'),
    Token('NUMBER', '1'),
    Token('NEWLINE', 'NEWLINE'),
    Token('ENDMARKER', 'ENDMARKER'),
)


class TestParsePython(TestCase):

    def test_tokens(self):
        tokens = tuple(tokenize_text(test_string))

        self.assertTupleEqual(tokens, expected_tokens)

    def test_parse_tree(self):
        tokens = tuple(tokenize_text(test_string))
        parse_trees = parse(p.file_input, tokens)

        self.assertEqual(len(parse_trees), 1)
        module = next(iter(parse_trees))

        self.assertEqual(module, expected_ast)


if __name__ == "__main__":
    main()