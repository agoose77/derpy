from derpy.ast import AST

Grammar = AST.subclass("Grammar", "rules")
CompoundParser = AST.subclass("Compound", "left right")
ConcatParser = CompoundParser.subclass("ConcatParser")
AltParser = CompoundParser.subclass("AltParser")
Comment = AST.subclass("Comment", "string")
RuleReference = AST.subclass("RuleReference", "name")
LitParser = AST.subclass("LitParser", "lit")
RuleDefinition = AST.subclass("RuleDefinition", "name parser")

ChildParser = AST.subclass("ChildParser", "child")
OptParser = ChildParser.subclass("OptParser")
ManyParser = ChildParser.subclass("ManyParser")
OnePlusParser = ChildParser.subclass("OnePlusParser")
GroupParser = ChildParser.subclass("GroupParser")

ID = AST.subclass("ID", "name")
