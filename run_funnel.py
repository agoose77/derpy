from argparse import ArgumentParser

from funnel.grammar import f
from funnel.tokenizer import tokenize_file
from python import codegen
from derp import parse
from derp.ast import print_ast, cyclic_colour_formatter, NodeVisitor, highlight_node_formatter


class Block(NodeVisitor):

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

    tokens = list(tokenize_file(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))
    result = parse(f.file_input, tokens)

    if not result:
        print("Failed to parse!")

    else:
        module = result.pop()
        print(module)
        print_ast(module, format_func=cyclic_colour_formatter) #highlight_node_formatter(ast.alias, ast.green, ast.blue))

        Block().visit(module)
