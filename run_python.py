from argparse import ArgumentParser

from python.tokenizer import tokenize_file
from python.grammar import g
from python.codegen import to_source

from derp.parsers import parse
from derp.ast import write_ast

from time import time
if __name__ == "__main__":
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('-filepath', default="sample.py")
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))
    s=time()
    result = parse(g.file_input, tokens)

    if not result:
        print("Failed to parse!")

    else:
        module = result.pop()
        print(time()-s)
        output_filename = "{}.ast".format(args.filepath)
        with open(output_filename, 'w') as f:
            write_ast(module,f)
