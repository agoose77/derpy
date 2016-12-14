from python.ast import AST

Funnel = AST.subclass("Funnel", "body")

Block = AST.subclass('Block')
TypeDef = Block.subclass("TypeDef", "name body")

AttrDef = Block.subclass("AttrDef", "type name default optional")
EnumAttrDef = AttrDef.subclass("EnumAttrDef", "options")

PythonBlock = Block.subclass('PythonBlock')
ValidateDef = PythonBlock.subclass('ValidateDef', 'body')
FormDef = PythonBlock.subclass('FormDef', 'body')
