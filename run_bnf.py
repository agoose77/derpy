from argparse import ArgumentParser

from bnf.tokenizer import tokenize_file, tokenize_text
from bnf.generate import  ParserGenerator
from bnf.meta_grammar import b

from derp import parse, ter, to_text
from derp.ast import print_ast

from python.grammar import tokenize_text as py_tokenize_text


grammar = """my_rule: 'for' ['yield' ['s']]""" # Define 'for' because the Python tokenize will output a Token('for','for') rather than Token('ID', 'for') token
sample = """for"""


class CustomParserGenerator(ParserGenerator):

    def emit_my_rule(self, args):
        print("Emit My Rule!", args)
        return args


if __name__ == "__main__":
    # parser = ArgumentParser(description='BNF parser generator')
    # parser.add_argument('-filepath', default="python.bnf")
    # args = parser.parse_args()
    #
    # tokens = list(tokenize_file(args.filepath))
    # print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))
    tokens = list(tokenize_text(grammar))

    # Print parse of BNF
    result = parse(b.file_input, tokens)
    root = result.pop()
    print_ast(root)

    # Generate parsers from AST
    generator = CustomParserGenerator('My Language')
    grammar = next(generator.visit(root))
    grammar.ensure_parsers_defined()

    # Tokenize expression
    sample_tokens = py_tokenize_text(sample)
    result = parse(grammar.my_rule & ter('NEWLINE') & ter('ENDMARKER'), sample_tokens)
    print(result)
