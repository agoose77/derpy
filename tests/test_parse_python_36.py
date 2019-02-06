import os
from unittest import TestCase, main

from derpy import parse, Token, ast as derpy_ast
from derpy.grammars.python36 import p, PythonTokenizer, ast

test_string = "x = x + 1"

expected_ast = ast.Module((ast.Assign((ast.Name("x"),), ast.BinOp(ast.Name("x"), ast.Add(), ast.Num(1))),))

expected_tokens = (
    Token("ID", "x"),
    Token("=", "="),
    Token("ID", "x"),
    Token("+", "+"),
    Token("NUMBER", "1"),
    Token("NEWLINE", "NEWLINE"),
    Token("ENDMARKER", "ENDMARKER"),
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

    def test_round_trip(self):
        tokens = tuple(tokenizer.tokenize_text(test_string))
        parse_trees = parse(p.file_input, tokens)

        self.assertEqual(len(parse_trees), 1)
        module = next(iter(parse_trees))

        with ast.patched_ast_module():
            import astor

            try:
                result = astor.to_source(module)
            except AttributeError:
                if derpy_ast.ENV_VAR_NO_SLOTS not in os.environ:
                    raise EnvironmentError(
                        f"Environment flag {derpy_ast.ENV_VAR_NO_SLOTS!r} must be defined to support "
                        "round-trip code generation."
                    )
                raise

            namespace = {"x": 0}

            exec(test_string, namespace)
            self.assertEqual(namespace["x"], 1)

            exec(result, namespace)
            self.assertEqual(namespace["x"], 2)


if __name__ == "__main__":
    main()
