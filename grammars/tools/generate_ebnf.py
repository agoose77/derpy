"""Generator routine for a grammar written in EBNF"""
import time
from argparse import ArgumentParser
from pathlib import Path

from derp.ast import to_string
from derp import parse
from grammars.ebnf import ParserGenerator, e, EBNFTokenizer

default_path = Path(__file__).parent / "sample.ebnf"


def main():
    parser = ArgumentParser(description='EBNF parser generator')
    parser.add_argument('--grammar_filepath', default=default_path, type=Path)
    args = parser.parse_args()

    tokens = list(EBNFTokenizer().tokenize_file(args.grammar_filepath))
    print("Parsing EBNF grammar: {} with {} tokens".format(args.grammar_filepath, len(tokens)))

    start_time = time.monotonic()
    result = parse(e.grammar, tokens)
    finish_time = time.monotonic()

    if not result:
        print("Failed to parse EBNF")

    elif len(result) > 1:
        print("Ambiguous parse of EBNF, mutliple parse trees")

    else:
        print("Successfully parsed EBNF in {:.3f}s".format(finish_time-start_time))
        root = next(iter(result))
        print("==========Built AST============")
        print(to_string(root))
        #
        # Generate parsers from AST
        generator = ParserGenerator(name='EBNF', variable='e')
        grammar = generator.visit(root)

        print("==========Built Grammar============")
        print(grammar)


if __name__ == "__main__":
    main()
