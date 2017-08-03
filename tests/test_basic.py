import unittest

from derp import lit, Token, rec, parse, rflatten


class TestBasic(unittest.TestCase):
    def test_basic(self):
        parser = rec()
        parser.parser = ~(parser & lit('1'))

        tokens = [Token('1', '1') for i in range(10)]
        result = parse(parser, tokens)

        self.assert_(result)
        tuple_ = result.pop()
        flattened = tuple(rflatten(tuple_))
        self.assertEqual(len(flattened), 10 + 1)


if __name__ == "__main__":
    unittest.main()
