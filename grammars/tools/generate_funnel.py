import time
from argparse import ArgumentParser
from pathlib import Path

from derp.ast import to_string
from derp.parsers import parse
from grammars.ebnf.meta_grammar import b
from grammars.ebnf.tokenizer import tokenize_file
from grammars.funnel.generate import ParserGenerator

from grammars import funnel

default_path = Path(funnel.__path__[0]) / "funnel.ebnf"


def main():
    parser = ArgumentParser(description='Funnel parser')
    parser.add_argument('--grammar_filepath', default=default_path, type=Path)
    args = parser.parse_args()

    tokens = list(tokenize_file(args.grammar_filepath))
    print("Parsing BNF grammar: {} with {} tokens".format(args.grammar_filepath, len(tokens)))

    # Parse funnel EBNF grammar
    start_time = time.monotonic()
    result = parse(b.grammar, tokens)
    finish_time = time.monotonic()

    if not result:
        print("Failed to parse BNF")

    elif len(result) > 1:
        print("Ambiguous parse of BNF, mutliple parse trees")

    else:
        print("Successfully parsed Funnel in {:.3f}s".format(finish_time - start_time))
        root = result.pop()
        print("==========Built AST============")
        print(to_string(root))
        #
        # Generate parsers from AST
        generator = ParserGenerator(name='Demo BNF', variable='f')
        grammar = generator.visit(root)

        print("==========Built Grammar============")
        print(grammar)


if __name__ == "__main__":
    main()
