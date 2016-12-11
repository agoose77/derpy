from argparse import ArgumentParser

from funnel.grammar import f, generate_parser_tokens
from python import ast as py_ast, codegen
from derp import parse


class Block(py_ast.NodeVisitor):

    def visit_ValidateDef(self, node):
        print("Validate")
        print(codegen.to_source(node))

    def visit_FormDef(self, node):
        print("Form")
        print(codegen.to_source(node))


if __name__ == "__main__":
    parser = ArgumentParser(description='Funnel parser')
    parser.add_argument('-filepath', default="sample.funnel")
    args = parser.parse_args()

    tokens = list(generate_parser_tokens(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))
    result = parse(f.file_input, tokens)

    if not result:
        print("Failed to parse!")

    else:
        module = result.pop()
        print(module)
        py_ast.print_ast(module, format_func=py_ast.cyclic_colour_formatter)#ast.highlight_node_formatter(ast.alias, ast.green, ast.blue))

        Block().visit(module)