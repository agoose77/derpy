from argparse import ArgumentParser
from pathlib import Path
from time import time

from derpy.ast import to_string
from derpy import parse
from derpy.grammars.python import p, PythonTokenizer


def main():
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('filepath', type=Path)
    parser.add_argument('-w', '--write-file', action='store_true')
    args = parser.parse_args()

    tokeniser = PythonTokenizer()
    tokens = list(tokeniser.tokenize_file(args.filepath))
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
        ast_string = to_string(module)

        output_path = args.filepath.parent / "{}.ast".format(args.filepath.name)

        if args.write_file:
            output_path.write_text(ast_string)
        else:
            print(ast_string)


if __name__ == "__main__":
    main()
