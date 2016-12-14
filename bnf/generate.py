from derp import Reduce, ter, Alternate, Concatenate, one_plus, greedy, optional
from derp.ast import iter_child_nodes
from derp.grammar import Grammar


class YieldingNodeVisitor:

    def generic_visit(self, node):
        for child in iter_child_nodes(node):
            yield from self.visit(child)

    def visit(self, node):
        visitor_name = "visit_{}".format(node.__class__.__name__)
        visitor = getattr(self, visitor_name, self.generic_visit)
        yield from visitor(node)


class ParserGenerator(YieldingNodeVisitor):

    def __init__(self, grammar_name):
        self.grammar = Grammar(grammar_name)

    def emit_default(self, args):
        return args

    def visit_Grammar(self, node):
        for rule in node.rules:
            next(self.visit(rule))
        yield self.grammar

    def visit_RuleDefinition(self, node):
        parser = next(self.visit(node.parser))
        emit_name = "emit_{}".format(node.name)
        parser = Reduce(parser, getattr(self, emit_name, self.emit_default))
        setattr(self.grammar, node.name, parser)
        yield parser

    def visit_RuleReference(self, node):
        yield getattr(self.grammar, node.name)

    def visit_AltParser(self, node):
        return Alternate(node.left, node.right)

    def visit_LitParser(self, node):
        yield ter(node.lit)

    def visit_ConcatParser(self, node):
        left = next(self.visit(node.left))
        right = next(self.visit(node.right))
        yield Concatenate(left, right)

    def visit_ManyParser(self, node):
        parser = next(self.visit(node.child))
        yield greedy(parser)

    def visit_OnePlusParser(self, node):
        parser = next(self.visit(node.child))
        yield one_plus(parser)

    def visit_OptParser(self, node):
        parser = next(self.visit(node.child))
        yield optional(parser)
