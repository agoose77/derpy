from argparse import ArgumentParser
from time import time

from derp.ast import write_ast
from derp.parsers import parse
from funnel.grammar import f
from funnel.tokenizer import tokenize_file

if __name__ == "__main__":
    parser = ArgumentParser(description='Funnel parser')
    parser.add_argument('--funnel_path', default="sample.funnel")
    args = parser.parse_args()

    tokens = list(tokenize_file(args.funnel_path))
    print("Parsing: {} with {} tokens".format(args.funnel_path, len(tokens)))

    start_time = time()
    result = parse(f.file_input, tokens)
    finish_time = time()

    if not result:
        print("Failed to parse Funnel source")

    elif len(result) > 1:
        print("Ambiguous parse of Funnel source, mutliple parse trees")

    else:
        print("Parsed in {:.3f}s".format(finish_time - start_time))

        module = result.pop()
        print(module)