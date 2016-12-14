from derp.ast import AST


Grammar = AST.subclass("Grammar", "rules")
ConcatParser = AST.subclass("ConcatParser", "left right")
AltParser = AST.subclass("AltParser", "left right")
RuleReference = AST.subclass("RuleReference", "name")
LitParser = AST.subclass("LitParser", "lit")
RuleDefinition = AST.subclass("RuleDefinition", "name parser")

ChildParser = AST.subclass("ChildParser", "child")
OptParser = ChildParser.subclass("OptParser", "child")
ManyParser = ChildParser.subclass("ManyParser", "child")
OnePlusParser = ChildParser.subclass("OnePlusParser", "child")
GroupParser = ChildParser.subclass("GroupParser", "child")
