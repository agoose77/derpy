from python.ast import AST


TypeDef = AST.subclass("TypeDef", "name body")
Funnel = AST.subclass("Funnel", "body")
Block = AST.subclass('Block')

AttrDef = AST.subclass("AttrDef", "type name default optional")
EnumAttrDef = AttrDef.subclass("EnumAttrDef", "type name options default optional")

PythonBlock = Block.subclass('PythonBlock')
ValidateDef = PythonBlock.subclass('ValidateDef', 'body')
FormDef = PythonBlock.subclass('FormDef', 'body')
