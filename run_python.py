from argparse import ArgumentParser

from python.tokenizer import tokenize_file
from python.grammar import g
from python.codegen import to_source

from derp import parse
from derp.ast import write_ast


if __name__ == "__main__":
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('-filepath', default="sample.py")
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))

    result = parse(g.file_input, tokens)

    if not result:
        print("Failed to parse!")

    else:
        module = result.pop()

        output_filename = "{}.ast".format(args.filepath)
        with open(output_filename, 'w') as f:
            write_ast(module,f)
