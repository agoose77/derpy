from enum import Enum
from derp.ast import AST

# Modules ##################################################
mod = AST.subclass('mod')
Module = mod.subclass('Module', 'body')
Interactive = mod.subclass('Interactive', 'body')
Expression = mod.subclass('Expression', 'body')

### Statements ##############################################
stmt = AST.subclass('stmt')
ClassDef = stmt.subclass('ClassDef', 'name bases keywords body decorator_list')
FunctionDef = stmt.subclass('FunctionDef', 'name args body decorator_list returns')
Return = stmt.subclass('Return', 'value')

Delete = stmt.subclass('Delete', 'targets')
Assign = stmt.subclass('Assign', 'targets value')
AugAssign = stmt.subclass('AugAssign', 'target op value')

For = stmt.subclass('For', 'target iter body orelse')
While = stmt.subclass('While', 'test body orelse')
If = stmt.subclass('If', 'test body orelse')
With = stmt.subclass('With', 'items body')

Raise = stmt.subclass('Raise', 'exc cause')
Try = stmt.subclass('Try', 'body handlers orelse finalbody')
Assert = stmt.subclass('Assert', 'test msg')

Import = stmt.subclass('Import', 'names')
ImportFrom = stmt.subclass('ImportFrom', 'module names level')

Global = stmt.subclass('Global', 'names')
Nonlocal = stmt.subclass('Nonlocal', 'names')
Expr = stmt.subclass('Expr', 'value')
Pass = stmt.subclass('Pass', '')
Break = stmt.subclass('Break', '')
Continue = stmt.subclass('Continue', '')
#############################################################

### Expressions #############################################
expr = AST.subclass('expr')
BoolOp = expr.subclass('BoolOp', 'op values')
BinOp = expr.subclass('BinOp', 'left op right')
UnaryOp = expr.subclass('UnaryOp', 'op operand')
LambdaDef = expr.subclass('LambdaDef', 'args body')
IfExp = expr.subclass('IfExp', 'test body or_else')
Dict = expr.subclass('Dict', 'keys values')
Set = expr.subclass('Set', 'elts')
ListComp = expr.subclass('ListComp', 'elt generators')
SetComp = expr.subclass('SetComp', 'elt generators')
DictComp = expr.subclass('DictComp', 'key value generators')
GeneratorExp = expr.subclass('GeneratorExp', 'elt generators')
# the grammar constrains where yield expressions can occur
Yield = expr.subclass('Yield', 'value')
YieldFrom = expr.subclass('YieldFrom', 'value')
# need sequences for compare to distinguish between
# x < 4 < 3 and (x < 4) < 3
Compare = expr.subclass('Compare', 'left ops comparators')
Call = expr.subclass('Call', 'func args keywords')
Num = expr.subclass('Num', 'n')
Str = expr.subclass('Str', 's')
Bytes = expr.subclass('Bytes', 's')
NameConstant = expr.subclass('NameConstant', 'value')
Ellipsis_ = expr.subclass('Ellipsis_', '')

# the following expression can appear in assignment context
Attribute = expr.subclass('Attribute', 'value attr')
Subscript = expr.subclass('Subscript', 'value slice')
Starred = expr.subclass('Starred', 'value')
Name = expr.subclass('Name', 'id')
List = expr.subclass('List', 'elts')
Tuple = expr.subclass('Tuple', 'elts')
#############################################################

### Slices ##################################################
slice = AST.subclass('slice')
Slice = slice.subclass('Slice', 'lower upper step')
ExtSlice = slice.subclass('ExitSubscript', 'dims')
Index = slice.subclass('Index', 'value')
#############################################################

boolop = AST.subclass('boolop')
And = boolop.subclass('And')
Or = boolop.subclass('Or')

operator = AST.subclass('operator')
Add = operator.subclass('Add')
Div = operator.subclass('Div')
Sub = operator.subclass('Sub')
Mod = operator.subclass('Mod')
Pow = operator.subclass('Pow')
Mult = operator.subclass('Mult')
MatMult = operator.subclass('MatMult')
RShift = operator.subclass('RShift')
LShift = operator.subclass('LShift')
BitOr = operator.subclass('BitOr')
BitXor = operator.subclass('BitXOr')
BitAnd = operator.subclass('BitAnd')
FloorDiv = operator.subclass('FloorDiv')

unaryop = AST.subclass('unaryop')
UAdd = unaryop.subclass('UAdd')
Invert = unaryop.subclass('Invert')
Not = unaryop.subclass('Not')
USub = unaryop.subclass('USub')

comparison = AST.subclass('comparison')
Eq = comparison.subclass('Eq')
NotEq = comparison.subclass('NotEq')
Lt = comparison.subclass('Lt')
LtE = comparison.subclass('LtE')
Gt = comparison.subclass('Gt')
GtE = comparison.subclass('GtE')
Is = comparison.subclass('Is')
IsNot = comparison.subclass('IsNot')
In = comparison.subclass('In')
NotIn = comparison.subclass('NotIn')

comprehension = AST.subclass('comprehension', 'target iter ifs')
excepthandler = AST.subclass('excepthandler', 'type name body')

arguments = AST.subclass('arguments', 'args vararg kwonlyargs kw_defaults kwarg defaults')
arg = AST.subclass('arg', 'arg annotation')

ArgUnpackTypes = Enum('ArgUnpackTypes', 'args kwargs none')

keyword = AST.subclass('keyword', 'arg value')# arg=None for **kwargs
alias = AST.subclass('alias', 'name asname')
withitem = AST.subclass('withitem', 'context_expr optional_vars')

# Helper nodes to clarify optional branches
compfor = AST.subclass('compfor', 'exprs iterable for_or_if')
compif = AST.subclass('compif', 'cond for_or_if')
importfrommodule = AST.subclass('importfrommodule', 'level module')
importfromsubmodules = AST.subclass('importfromsubmodules', 'aliases')
tryexceptelsefinally = AST.subclass('tryexceptelsefinally', 'handlers orelse finalbody')
tryfinally = AST.subclass('tryfinally', 'finalbody')
