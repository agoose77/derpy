from argparse import ArgumentParser

from python.grammar import generate_parser_tokens, g
from python import ast
from python.codegen import to_source

from derp import parse


if __name__ == "__main__":
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('-filepath', default="sample.py")
    args = parser.parse_args()

    tokens = list(generate_parser_tokens(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))

    result = parse(g.file_input, tokens)

    if not result:
        print("Failed to parse!")

    else:
        module = result.pop()
        ast.print_ast(module, format_func=ast.cyclic_colour_formatter)#ast.highlight_node_formatter(ast.alias, ast.green, ast.blue))

        source = to_source(module)
        print("Source:\n", source)
