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
    print(f"{len(result)} results")
    from pprint import pprint
    pprint(result)

    # root = result.pop()
    # print(to_string(root))
    # print("Built AST")
    #
    # # Generate parsers from AST
    # generator = CustomParserGenerator('Demo BNF')
    # grammar = next(generator.visit(root))
    # grammar.ensure_parsers_defined()
    #
    # print("Built Grammar")
    #
    # # Tokenize expression
    # print("Parsing grammar sample: {} with {} tokens".format(args.filepath, len(tokens)))
    # sample_tokens = py_tokenize_file(args.sample)
    # result = parse(grammar.main & ter('NEWLINE') & ter('ENDMARKER'), sample_tokens)
    # print(result)
