__all__ = "ParserGenerator",

from derp.ast import NodeVisitor
from .ast import CompoundParser


class ParserGenerator(NodeVisitor):
    grammar_declaration = """
from derp import Grammar, lit

{variable} = Grammar({name!r})
{rules}
{variable}.ensure_parsers_defined()
"""

    def __init__(self, name, variable='g'):
        self.name = name
        self.variable = variable

    def visit_Grammar(self, node):
        statements = []

        for rule in node.rules:
            statement = self.visit(rule)
            statements.append(statement)

        rules = '\n'.join(statements)
        return self.grammar_declaration.format(name=self.name, variable=self.variable, rules=rules, self=self)

    def visit_Comment(self, node):
        return node.string

    def visit_ID(self, node):
        if node.name == "STRING":
            return "lit('LIT')"
        elif node.name == "NAME":
            return "lit('ID')"
        elif node.name in {"NEWLINE", "ENDMARKER", "INDENT", "DEDENT", "NUMBER"}:
            return "lit({!r})".format(node.name)
        else:
            return "{}.{}".format(self.variable, node.name)

    def visit_OptParser(self, node):
        child_text = self.visit(node.child)
        if isinstance(node.child, CompoundParser):
            return "~({})".format(child_text)
        return "~{}".format(child_text)

    def visit_GroupParser(self, node):
        child_text = self.visit(node.child)
        return "({})".format(child_text)

    def visit_RuleDefinition(self, node):
        parser = self.visit(node.parser)
        return "{}.{} = {}".format(self.variable, node.name, parser)

    def visit_RuleReference(self, node):
        return getattr(self.name, node.name)

    def visit_AltParser(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return "{} | {}".format(left, right)  # Alternate(left, right)

    def visit_LitParser(self, node):
        return "lit({})".format(node.lit)

    def visit_ConcatParser(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return "{} & {}".format(left, right)  # Alternate(left, right)

    def visit_ManyParser(self, node):
        parser = self.visit(node.child)
        if isinstance(node.child, CompoundParser):
            return "({})[...]".format(parser)
        return "{}[...]".format(parser)

    def visit_OnePlusParser(self, node):
        parser = self.visit(node.child)

        if isinstance(node.child, CompoundParser):
            return "({})[1:]".format(parser)
        return "{}[1:]".format(parser)
