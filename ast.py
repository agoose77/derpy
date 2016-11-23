from abc import ABC, abstractmethod
from collections import OrderedDict
from enum import Enum
from pprint import pprint, pformat


ArgUnpackTypes = Enum('ArgUnpackTypes', 'args kwargs none')
UnaryOpType = Enum('UnaryOp', 'UAdd Invert USub Not')
BoolOpType = Enum('BoolOp', 'And Or')
OperatorType = Enum('Operator', 'Add Div Sub Mod Pow Mult MatMult RShift LShift BitOr BitXOr BitAnd FloorDiv')
ComparisonOpType = Enum('ComparisonOp', 'Eq NotEq Lt LtE Gt GtE Is IsNot In NotIn')


class AstNode(ABC):

    @abstractmethod
    def _as_dict(self):
        pass

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return False

        try:
            return self._as_dict() == other._as_dict()

        except AttributeError:
            return False


def make_ast_node(name, field_str, parent=None):
    fields = [f.strip() for f in field_str.split(' ') if f.strip()]
    cls_dict = {}
    if parent is None:
        bases = AstNode,
    else:
        bases = parent, AstNode

    if fields:
        body = "\n    ".join("self.{0} = {0}".format(name) for name in fields)
        field_args = ", ".join(fields)
        declare_init = "def __init__(self, {field_args}):\n    {body}"\
            .format(field_args=field_args, body=body)
        exec(declare_init, cls_dict)

        dict_str = ", ".join("({0!r}, self.{0})".format(name) for name in fields)
        declare_as_dict = "def _as_dict(self):\n    return OrderedDict([{fields}])".format(fields=dict_str)
        exec(declare_as_dict, globals(), cls_dict)

        values_str = ", ".join("self.{0}".format(name) for name in fields)
        declare_hash ="def __hash__(self):\n    return hash(tuple(({values_str},)))".format(values_str=values_str)
        exec(declare_hash, cls_dict)

    else:
        def as_dict(self):
            return {}
        cls_dict['_as_dict'] = as_dict

        def __hash__(self):
            return hash(())
        cls_dict['__hash__'] = __hash__

    return type(name, bases, cls_dict)


Slice = make_ast_node('Subscript', 'first second third')

Bytes = make_ast_node('Bytes', 'value')
String = make_ast_node('String', 'value')
Num = make_ast_node('Num', 'value')
Dict = make_ast_node('Dict', 'keys values')
List = make_ast_node('List', 'values')
Set = make_ast_node('Set', 'elts')
Tuple = make_ast_node('Tuple', 'elts')
Assignment = make_ast_node('Assignment', 'targets value')
FunctionDef = make_ast_node('FunctionDef', 'name args body decorators returns')
Pass = make_ast_node('Pass', '')
Ellipsis_ = make_ast_node('Ellipsis_', '')
None_ = make_ast_node('None_', '')
Del = make_ast_node('Del', '')
Not = make_ast_node('Not', 'expression')
Continue = make_ast_node('Continue', '')
Assert = make_ast_node('Assert', 'test msg')

Import = make_ast_node('Import', 'names')
ImportFrom = make_ast_node('ImportFrom', 'module names level')
Yield = make_ast_node('Yield', 'expr')
YieldFrom = make_ast_node('YieldFrom', 'expr')

Break = make_ast_node('Break', '')
Return = make_ast_node('Return', 'value')
Nonlocal = make_ast_node('Nonlocal', 'names')
Global = make_ast_node('Global', 'names')
Raise = make_ast_node('Raise', 'exc cause')
LambdaDef = make_ast_node('LambdaDef', 'args body')
Compare = make_ast_node('Compare', 'left ops comparators')
If = make_ast_node('If', 'test body or_else')
IfExp = make_ast_node('IfExp', 'test body or_else')
While = make_ast_node('While', 'test body or_else')
For = make_ast_node('For', 'target iter body or_else')
ClassDef = make_ast_node('ClassDef', 'name bases keywords body decorators')
Attribute = make_ast_node('Attribute', 'value attr')
Subscript = make_ast_node('Subscript', 'value slice')
Call = make_ast_node('Call', 'func args keywords')
Arg = make_ast_node('Arg', 'arg annotation')
Arguments = make_ast_node('Arguments', 'args vararg kwonlyargs kw_defaults kwarg defaults')
BinOp = make_ast_node('BinOp', 'left op right')
UnaryOp = make_ast_node('UnaryOp', 'op operand')
BoolOp = make_ast_node('BoolOp', 'values')
With = make_ast_node('With', 'items body')
Expr = make_ast_node('Expr', 'exp')
AugAssign = make_ast_node('Augassign', 'target op value')

# arg=None for **kwargs
Keyword = make_ast_node('Keyword', 'arg value')
Starred = make_ast_node('Starred', 'value')
Name = make_ast_node('Name', 'id')

_CompFor = make_ast_node('CompFor', 'exprs or_test iterable')
_CompIf = make_ast_node('CompIf', 'cond opt')


def format_ast(node, indent='', field_indent='    '):
    fields = []
    children = []
    for name, value in node._as_dict().items():
        if isinstance(value, AstNode):
            children.append((name, value))
        else:
            fields.append((name, value))

    total_field_indent = indent + field_indent
    stmts = ["{name} = {value}".format(name=name, value=value) for name, value in fields]
    stmts.extend(["{name} = {value}"
              .format(name=name, value=format_ast(child, total_field_indent, field_indent)) for name, child in children])
    body = ("\n{indent}".format(indent=total_field_indent)).join(stmts)
    return "{indent}{name}:\n{field_indent}{body}".format(field_indent=field_indent, indent=total_field_indent, name=node.__class__.__name__, body=body)


def walk(node):
    yield node
    for name, child in node._as_dict():
        if isinstance(child, AstNode):
            yield from walk(child)


def print_ast(node):
    print(format_ast(node))
