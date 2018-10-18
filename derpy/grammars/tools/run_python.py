from argparse import ArgumentParser
from pathlib import Path
from time import time

from derpy.ast import write_ast
from derpy import parse
from derpy.grammars.python import p, tokenize_file


def main():
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('filepath', type=Path)
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))

    start_time = time()
    result = parse(p.file_input, tokens)
    finish_time = time()

    if not result:
        print("Failed to parse Python source")

    elif len(result) > 1:
        print("Ambiguous parse of Python source, mutliple parse trees")

    else:
        print("Parsed in {:.3f}s".format(finish_time - start_time))

        module = next(iter(result))
        output_filename = args.filepath.parent / "{}.ast".format(args.filepath.name)

        with open(output_filename, 'w') as f:
            write_ast(module, f)


if __name__ == "__main__":
    main()
