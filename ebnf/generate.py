from derp.ast import iter_child_nodes
from derp.grammar import Grammar
from derp.parsers import Reduce, lit, Alternate, Concatenate, star, plus, opt


class YieldingNodeVisitor:
    def generic_visit(self, node):
        for child in iter_child_nodes(node):
            yield from self.visit(child)

    def visit(self, node):
        visitor_name = "visit_{}".format(node.__class__.__name__)
        visitor = getattr(self, visitor_name, self.generic_visit)
        yield from visitor(node)


grammar_declaration = """
from derp.grammar import Grammar
from derp.parsers import lit, star

{name} = Grammar('test')
{rules}
{name}.ensure_parsers_defined()
"""


class ParserGenerator(YieldingNodeVisitor):
    def __init__(self, grammar_name):
        self.grammar = Grammar(grammar_name)
        self.grammar_name = "g"

    def emit_default(self, args):
        return args

    def visit_Grammar(self, node):
        defns = []
        for rule in node.rules:
            defn = next(self.visit(rule))
            defns.append(defn)
        rules = '\n'.join(defns)
        test = grammar_declaration.format(name=self.grammar_name, rules=rules)
        yield test

    def visit_ID(self, node):
        if node.name == "STRING":
            yield "lit('LIT')"
        elif node.name == "NAME":
            yield "lit('ID')"
        elif node.name in {"NEWLINE", "ENDMARKER", "INDENT", "DEDENT", "NUMBER"}:
            yield "lit({!r})".format(node.name)
        else:
            yield "{}.{}".format(self.grammar_name, node.name)

    def visit_OptParser(self, node):
        child_text = next(self.visit(node.child))
        yield "~({})".format(child_text)

    def visit_GroupParser(self, node):
        child_text = next(self.visit(node.child))
        yield "({})".format(child_text)

    def visit_RuleDefinition(self, node):
        parser = next(self.visit(node.parser))
        #print(parser, type(parser))
        #emit_name = "emit_{}".format(node.name)
        #parser = Reduce(parser, getattr(self, emit_name, self.emit_default))
        #setattr(self.grammar, node.name, parser)

        yield "g.{} = {}".format(node.name, parser)

    def visit_RuleReference(self, node):
        yield getattr(self.grammar, node.name)

    def visit_AltParser(self, node):
        left = next(self.visit(node.left))
        right = next(self.visit(node.right))
        yield "({} | {})".format(left, right)#Alternate(left, right)

    def visit_LitParser(self, node):
        yield "lit({!r})".format(node.lit)

    def visit_ConcatParser(self, node):
        left = next(self.visit(node.left))
        right = next(self.visit(node.right))
        yield "{} & {}".format(left, right)#Alternate(left, right)

    def visit_ManyParser(self, node):
        parser = next(self.visit(node.child))
        yield "+{}".format(parser)

    def visit_OnePlusParser(self, node):
        parser = next(self.visit(node.child))
        yield "star({})".format(parser)

    def visit_OptParser(self, node):
        parser = next(self.visit(node.child))
        yield "~{}".format(parser)
