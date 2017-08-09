from unittest import TestCase, main

from derp import parse, Token
from grammars.python import p, PythonTokenizer, ast

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


tokenizer = PythonTokenizer()


class TestParsePython(TestCase):
    def test_tokens(self):
        tokens = tuple(tokenizer.tokenize_text(test_string))

        self.assertTupleEqual(tokens, expected_tokens)

    def test_parse_tree(self):
        tokens = tuple(tokenizer.tokenize_text(test_string))
        parse_trees = parse(p.file_input, tokens)

        self.assertEqual(len(parse_trees), 1)
        module = next(iter(parse_trees))

        self.assertEqual(module, expected_ast)


if __name__ == "__main__":
    main()
