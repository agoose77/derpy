import unittest

from derp.ast.ast import AST, NodeTransformer, NodeVisitor

Module = AST.subclass("Module", "body")
While = AST.subclass("While", "condition body")
Expr = AST.subclass("Expr", "value")
Name = Expr.subclass("Name")
Print = Expr.subclass("Print")
Call = Expr.subclass("Call")


class RemoveCall(NodeTransformer):
    def visit_Call(self, node):
        return None


class NameCounter(NodeVisitor):
    count = 0

    def visit_Name(self, node):
        self.count += 1


class TestAST(unittest.TestCase):
    def _create_ast(self):
        body = While(Name("True"), (Print(Name("x")),
                                    Call(Name("foo")))
                     ),
        return Module(body)

    def test_transformer(self):
        mod = self._create_ast()
        mod_new = RemoveCall().visit(mod)

        self.assertIsNot(mod, mod_new)
        while_ = mod_new.body[0]
        self.assertEqual(len(while_.body), 1)

    def test_visitor(self):
        mod = self._create_ast()
        name_counter = NameCounter()
        name_counter.visit(mod)
        self.assertEqual(name_counter.count, 3)


if __name__ == '__main__':
    unittest.main()
