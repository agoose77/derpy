from derp.ast import AST


FunnelModule = AST.subclass("FunnelModule", "types")
FunnelType = AST.subclass("FunnelType", "name body")
FieldType = AST.subclass("FieldType", "name")
EnumType = FieldType.subclass("EnumType", "options")
IntegerType = FieldType.subclass("IntegerType")
BoolType = FieldType.subclass("BoolType")
StringType = FieldType.subclass("StringType")
OtherType = FieldType.subclass("OtherType", "type")
NullableField = AST.subclass("NullableField", "field")
DefaultField = AST.subclass("DefaultField", "field value")
Block = AST.subclass("Block", "body")
FormBlock = Block.subclass("FormBlock")
ValidateBlock = Block.subclass("ValidateBlock")