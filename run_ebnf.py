from argparse import ArgumentParser

from ebnf.generate import ParserGenerator
from ebnf.meta_grammar import b
from ebnf.tokenizer import tokenize_file
from derp.ast import to_string
from derp.parsers import parse

sample = """for"""


class CustomParserGenerator(ParserGenerator):
    def emit_my_rule(self, args):
        print("Emit My Rule!", args)
        return args


if __name__ == "__main__":
    parser = ArgumentParser(description='BNF parser generator')
    parser.add_argument('-filepath', default="sample.ebnf")
    parser.add_argument('-sample', default="sample.txt")
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing BNF grammar: {} with {} tokens".format(args.filepath, len(tokens)))
    tokens = list(tokens);print(tokens)
    # Print parse of BNF
    import time
    start = time.monotonic()

    result = parse(b.grammar, tokens)
    stop = time.monotonic()
    print(f"{stop-start}")
    from pprint import pprint
    pprint(result)

    print(f"{len(result)} results")

    root = result.pop()
    print(to_string(root))
    print("Built AST")
    #
    # Generate parsers from AST
    generator = CustomParserGenerator('Demo BNF')
    grammar = next(generator.visit(root))
    # grammar.ensure_parsers_defined()
    print(grammar)
    exec(grammar)

    # print("Built Grammar")
    # for name in dir(grammar):
    #     print(name, getattr(grammar, name))

    from python.tokenizer import tokenize_text
    from derp.parsers import lit
    # from python.grammar import g

    # Tokenize expression
    sample_tokens = tokenize_text("x = y")
    sample_tokens = list(sample_tokens)
    result = parse(g.file_input, sample_tokens)
    print(result)