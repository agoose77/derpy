import operator

from derp import Grammar, lit, parse, unpack, Tokenizer, extracts, extract
from derp.ast import AST, NodeVisitor

Compound = AST.subclass("Compound", "left right", module_name=__name__)
Add = Compound.subclass("Add")
Sub = Compound.subclass("Sub")
Mul = Compound.subclass("Mul")
Div = Compound.subclass("Div")
Unary = AST.subclass("Unary", "child")
Neg = Unary.subclass("Neg")


def emit_compound(f, args):
    l, _, r = unpack(args, 3)
    return f(l, r)


def emit_neg(args):
    return Neg(args[1])


def emit_paren(args):
    _, x, _ = unpack(args, 3)
    return x


def emit_eqn(args):
    return args[0]


g = Grammar("Calc")
g.sum = (g.product |
         (g.sum & lit('+') & g.product) >> extracts(3, 0, 2) >> Add.from_tuple |
         (g.sum & lit('-') & g.product) >> extracts(3, 0, 2) >> Sub.from_tuple
         )
g.product = (g.item |
             (g.product & lit('*') & g.item) >> extracts(3, 0, 2) >> Mul.from_tuple |
             (g.product & lit('/') & g.item) >> extracts(3, 0, 2) >> Add.from_tuple
             )
g.item = (lit('NUMBER') |
          (lit('-') & g.item) >> extract(2, 1) >> Neg
          ((lit('(') & g.sum & lit(')')) >> extracts(3, 1))
          )
g.equation = (g.sum & lit('ENDMARKER')) >> extract(2, 0)


class EvalVisitor(NodeVisitor):
    eval_table = {Sub: operator.sub,
                  Mul: operator.mul,
                  Div: operator.truediv,
                  Add: operator.add}

    def _visit_or_return(self, value):
        if isinstance(value, AST):
            return self.visit(value)
        return value

    def _visit_compound_op(self, node):
        node_type = type(node)

        try:
            op = self.eval_table[node_type]
        except KeyError:
            raise ValueError

        left = self._visit_or_return(node.left)
        right = self._visit_or_return(node.right)
        return op(left, right)

    def visit_Neg(self, node):
        return -self._visit_or_return(node.child)

    visit_Add = _visit_compound_op
    visit_Sub = _visit_compound_op
    visit_Div = _visit_compound_op
    visit_Mul = _visit_compound_op


def eval_ast(ast):
    visitor = EvalVisitor()
    result = visitor.visit(ast)
    return result


if __name__ == "__main__":
    expr = "99+1"
    tokens = Tokenizer().tokenize_text(expr)

    from pprint import pprint

    tokens = list(tokens)
    pprint(tokens)

    ast = parse(g.equation, tokens).pop()
    result = eval_ast(ast)
    print(f"Result of {expr} is {result}")
