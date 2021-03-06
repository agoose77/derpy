import operator
from argparse import ArgumentParser
from ast import literal_eval

from typing import Union

from derpy import Grammar, lit, parse, RegexTokenizer, selects, select, context
from derpy.ast import AST, NodeVisitor, to_string, cyclic_colour_formatter

Compound = AST.subclass("Compound", "left right")
Add = Compound.subclass("Add")
Sub = Compound.subclass("Sub")
Mul = Compound.subclass("Mul")
Div = Compound.subclass("Div")
Unary = AST.subclass("Unary", "child")
Neg = Unary.subclass("Neg")
ID = Unary.subclass("ID")

g = Grammar("Calc")
g.sum = (
    g.product
    | (g.sum & lit("+") & g.product) >> selects(3, 0, 2) >> Add._make
    | (g.sum & lit("-") & g.product) >> selects(3, 0, 2) >> Sub._make
)
g.product = (
    g.item
    | (g.product & lit("*") & g.item) >> selects(3, 0, 2) >> Mul._make
    | (g.product & lit("/") & g.item) >> selects(3, 0, 2) >> Div._make
)
g.item = (
    lit("NUMBER")
    | lit("ID") >> ID
    | (lit("-") & g.item) >> select(2, 1) >> Neg((lit("(") & g.sum & lit(")")) >> selects(3, 1))
)
g.equation = (g.sum & lit("ENDMARKER")) >> select(2, 0)


class EvalVisitor(NodeVisitor):
    eval_table = {Sub: operator.sub, Mul: operator.mul, Div: operator.truediv, Add: operator.add}

    def __init__(self):
        self.symbol_table = {}

    def _visit_and_return(self, value):
        if isinstance(value, AST):
            return self.visit(value)
        return value

    def _visit_compound_op(self, node):
        node_type = type(node)

        try:
            op = self.eval_table[node_type]
        except KeyError:
            raise ValueError

        left = self._visit_and_return(node.left)
        right = self._visit_and_return(node.right)
        return op(left, right)

    visit_Add = _visit_compound_op
    visit_Sub = _visit_compound_op
    visit_Div = _visit_compound_op
    visit_Mul = _visit_compound_op

    def visit_Neg(self, node):
        return -self._visit_and_return(node.child)

    def visit_ID(self, node):
        try:
            return self.symbol_table[node.child]

        except KeyError:
            value_str = input(f"Enter value for {node.child}")
            value = literal_eval(value_str)
            assert isinstance(value, (int, float))
            self.symbol_table[node.child] = value
            return value


def eval_ast(ast: AST) -> Union[int, float]:
    visitor = EvalVisitor()
    result = visitor.visit(ast)
    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("expression", type=str)
    args = parser.parse_args()

    expr = args.expression
    tokens = RegexTokenizer().tokenize_text(expr)

    with context():
        ast = next(iter(parse(g.equation, tokens)))

    print(to_string(ast, formatter=cyclic_colour_formatter))
    result = eval_ast(ast)
    print(f"Result of {expr} is {result}")
