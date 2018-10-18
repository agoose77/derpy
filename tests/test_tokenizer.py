import unittest

from derpy import RegexTokenizer, Token

test_string = """
x = y + z
j = "bob"
"""

expected_tokens = (
    Token('NEWLINE', '\n'),
    Token('ID', 'x'),
    Token('=', '='),
    Token('ID', 'y'),
    Token('+', '+'),
    Token('ID', 'z'),
    Token('NEWLINE', '\n'),
    Token('ID', 'j'),
    Token('=', '='),
    Token('LIT', '"bob"'),
    Token('NEWLINE', '\n'),
    Token('ENDMARKER', 'ENDMARKER'),
)


class TestTokenizer(unittest.TestCase):
    def test_tokenizer(self):
        tokenizer = RegexTokenizer()
        tokens = tuple(tokenizer.tokenize_text(test_string))
        self.assertTupleEqual(tokens, expected_tokens)


if __name__ == "__main__":
    unittest.main()
