import unittest

from derp import lit, Token, rec, parse, unpack


class TestBasic(unittest.TestCase):
    def test_basic(self):
        parser = rec()
        parser.parser = ~(parser & lit('1'))

        tokens = [Token('1', '1') for i in range(10)]
        parse_trees = parse(parser, tokens)
        self.assertTrue(parse_trees)

        tuple_ = next(iter(parse_trees))
        # When unpacking, account for trailing '' from the optional parser
        flattened = tuple(unpack(tuple_, 10 + 1))
        self.assertEqual(len(flattened), 10 + 1)


if __name__ == "__main__":
    unittest.main()
