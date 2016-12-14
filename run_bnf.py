from argparse import ArgumentParser

from bnf.tokenizer import tokenize_file, tokenize_text
from bnf.generate import  ParserGenerator
from bnf.meta_grammar import b

from derp import parse, ter
from derp.ast import print_ast

from python.tokenizer import tokenize_file as py_tokenize_file


sample = """for"""


class CustomParserGenerator(ParserGenerator):

    def emit_my_rule(self, args):
        print("Emit My Rule!", args)
        return args


if __name__ == "__main__":
    parser = ArgumentParser(description='BNF parser generator')
    parser.add_argument('-filepath', default="sample.bnf")
    parser.add_argument('-sample', default="sample.txt")
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing BNF grammar: {} with {} tokens".format(args.filepath, len(tokens)))

    # Print parse of BNF
    result = parse(b.file_input, tokens)
    root = result.pop()
    print_ast(root)

    print("Built AST")
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
