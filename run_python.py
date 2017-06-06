from argparse import ArgumentParser
from time import time

from derp.ast import write_ast
from derp.parsers import parse
from python.grammar import g
from python.tokenizer import tokenize_file

if __name__ == "__main__":
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('-filepath', default="sample.py")
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))

    start_time = time()
    result = parse(g.file_input, tokens)
    finish_time = time()

    if not result:
        print("Failed to parse!")

    else:
        print("Parsed in {:.3f}s".format(finish_time - start_time))

        module = result.pop()
        output_filename = "{}.ast".format(args.filepath)

        with open(output_filename, 'w') as f:
            write_ast(module, f)
