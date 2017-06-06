from argparse import ArgumentParser
from pathlib import Path
from time import time

from derp.ast import write_ast
from derp.parsers import parse
from grammars.python.grammar import g
from grammars.python.tokenizer import tokenize_file


def main():
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('filepath', type=Path)
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))

    start_time = time()
    result = parse(g.file_input, tokens)
    finish_time = time()

    if not result:
        print("Failed to parse Python source")

    elif len(result) > 1:
        print("Ambiguous parse of Python source, mutliple parse trees")

    else:
        print("Parsed in {:.3f}s".format(finish_time - start_time))

        module = result.pop()
        output_filename = "{}.ast".format(args.filepath)

        with open(output_filename, 'w') as f:
            write_ast(module, f)


if __name__ == "__main__":
    main()
