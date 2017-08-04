import operator
from functools import partial

from derp import Grammar, lit, parse, unpack_n, Tokenizer
from derp.ast import AST, NodeVisitor

Compound = AST.subclass("Compound", "left right", module_name=__name__)
Add = Compound.subclass("Add")
Sub = Compound.subclass("Sub")
Mul = Compound.subclass("Mul")
Div = Compound.subclass("Div")


def emit_compound(f, args):
    l, _, r = unpack_n(args, 3)
    return f(l, r)


def emit_neg(args):
    return args[1]


def emit_paren(args):
    _, x, _ = unpack_n(args, 3)
    return x


def emit_eqn(args):
    return args[0]


g = Grammar("Calc")
g.sum = (g.product |
         (g.sum & lit('+') & g.product) >> partial(emit_compound, Add) |
         (g.sum & lit('-') & g.product) >> partial(emit_compound, Sub)
         )
g.product = (g.item |
             (g.product & lit('*') & g.item) >> partial(emit_compound, Mul) |
             (g.product & lit('/') & g.item) >> partial(emit_compound, Div)
             )
g.item = (lit('NUMBER') |
          (lit('-') & g.item) >> emit_neg |
          ((lit('(') & g.sum & lit(')')) >> emit_paren)
          )
g.equation = (g.sum & lit('ENDMARKER')) >> emit_eqn


class EvalVisitor(NodeVisitor):
    eval_table = {Sub: operator.sub,
                  Mul: operator.mul,
                  Div: operator.truediv,
                  Add: operator.add}

    def generic_visit(self, node, *args, **kwargs):
        node_type = type(node)

        if not issubclass(node_type, AST):
            return node

        try:
            op = self.eval_table[node_type]
        except KeyError:
            raise ValueError

        left = self.visit(node.left)
        right = self.visit(node.right)
        return op(left, right)


def eval_ast(ast):
    visitor = EvalVisitor()
    result = visitor.visit(ast)
    return result


if __name__ == "__main__":
    expr = "99+1+2+3*4"
    tokens = Tokenizer().tokenize_text(expr)

    from pprint import pprint

    tokens = list(tokens)
    pprint(tokens)

    ast = parse(g.equation, tokens).pop()
    result = eval_ast(ast)
    print(f"Result of {expr} is {result}")
