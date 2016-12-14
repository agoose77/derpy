from argparse import ArgumentParser

from python.grammar import tokenize_file, g
from python.codegen import to_source

from derp import parse
from derp.ast import print_ast, cyclic_colour_formatter


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
        print_ast(module, format_func=cyclic_colour_formatter)#ast.highlight_node_formatter(ast.alias, ast.green, ast.blue))

        source = to_source(module)
        print("Source:")
        print(source)
