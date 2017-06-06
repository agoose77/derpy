from derp.ast import NodeVisitor
from derp.grammar import Grammar

grammar_declaration = """
from derp.grammar import Grammar
from derp.parsers import lit, star

{variable} = Grammar({name!r})
{rules}
{variable}.ensure_parsers_defined()
"""


class ParserGenerator(NodeVisitor):
    def __init__(self, grammar_name, grammar_variable='g'):
        self.grammar_name = grammar_name
        self.grammar_variable = grammar_variable

    def visit_Grammar(self, node):
        statements = []

        for rule in node.rules:
            stmt = self.visit(rule)
            statements.append(stmt)

        rules = '\n'.join(statements)
        return grammar_declaration.format(name=self.grammar_name, variable=self.grammar_variable, rules=rules)

    def visit_ID(self, node):
        if node.name == "STRING":
            return "lit('LIT')"
        elif node.name == "NAME":
            return "lit('ID')"
        elif node.name in {"NEWLINE", "ENDMARKER", "INDENT", "DEDENT", "NUMBER"}:
            return "lit({!r})".format(node.name)
        else:
            return "{}.{}".format(self.grammar_variable, node.name)

    def visit_OptParser(self, node):
        child_text = self.visit(node.child)
        return "~({})".format(child_text)

    def visit_GroupParser(self, node):
        child_text = self.visit(node.child)
        return "({})".format(child_text)

    def visit_RuleDefinition(self, node):
        parser = self.visit(node.parser)
        return "g.{} = {}".format(node.name, parser)

    def visit_RuleReference(self, node):
        return getattr(self.grammar_name, node.name)

    def visit_AltParser(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return "{} | {}".format(left, right)  # Alternate(left, right)

    def visit_LitParser(self, node):
        return "lit({!r})".format(node.lit)

    def visit_ConcatParser(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return "{} & {}".format(left, right)  # Alternate(left, right)

    def visit_ManyParser(self, node):
        parser = self.visit(node.child)
        return "+{}".format(parser)

    def visit_OnePlusParser(self, node):
        parser = self.visit(node.child)
        return "star({})".format(parser)
