import time
from argparse import ArgumentParser
from pathlib import Path

from derp.ast import to_string
from derp.parsers import parse
from ebnf.generate import ParserGenerator
from ebnf.meta_grammar import b
from ebnf.tokenizer import tokenize_file

if __name__ == "__main__":
    parser = ArgumentParser(description='BNF parser generator')
    parser.add_argument('--filepath', default="sample.ebnf")
    parser.add_argument('--sample', default="sample.txt", type=Path)
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing BNF grammar: {} with {} tokens".format(args.filepath, len(tokens)))

    start_time = time.monotonic()
    result = parse(b.grammar, tokens)
    finish_time = time.monotonic()

    if not result:
        print("Failed to parse BNF")

    elif len(result) > 1:
        print("Ambiguous parse of BNF, mutliple parse trees")

    else:
        root = result.pop()
        print("==========Built AST============")
        print(to_string(root))
        #
        # Generate parsers from AST
        generator = ParserGenerator('Demo BNF')
        grammar = generator.visit(root)

        print("==========Built Grammar============")
        print(grammar)
        exec(grammar)

        print()
        from python.tokenizer import tokenize_file as pytokenize_file

        # Tokenize expression
        print("==========Test Grammar============")
        sample_tokens = pytokenize_file(args.sample)
        result = parse(g.file_input, sample_tokens)
        print(result)
