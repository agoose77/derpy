def fields(*fields):
    def decorator(cls=object):
        cls_dict = {'__slots__': tuple(fields)}
        cls_dict['_fields'] = fields

        assert all(f.isidentifier() for f in fields)
        if fields:
            arg_string = ", ".join(fields)
            body_definitions = ["self.{0} = {0}".format(f) for f in fields]
            definition = "def __init__(self, {}):\n\t".format(arg_string) + "\n\t".join(body_definitions)
            exec(definition, cls_dict)

        cls_name = cls.__name__
        return type(cls_name, (cls,), cls_dict)

    return decorator

from collections import namedtuple
from enum import Enum

ArgUnpackTypes = Enum('ArgUnpackTypes', 'args kwargs none')
SliceNode = namedtuple('Subscript', 'first second third')

DictNode = namedtuple('Dict', 'keys values')
ListNode = namedtuple('List', 'values')
SetNode = namedtuple('Set', 'elements')
TupleNode = namedtuple('Tuple', 'values')
StringNode = namedtuple('String', 'value')
AssignmentNode = namedtuple('Assignment', 'targets value')
FunctionDefNode = namedtuple('FunctionDef', 'name args body decorators')
PassNode = namedtuple('Pass', '')
EllipsisNode = namedtuple('Ellipsis', '')
NotNode = namedtuple('Not', 'expression')
ContinueNode = namedtuple('Continue', '')
BreakNode = namedtuple('BreakNode', '')
ReturnNode = namedtuple('Return', 'value')
NonlocalNode = namedtuple('Nonlocal', 'names')
GlobalNode = namedtuple('Global', 'names')
RaiseNode = namedtuple('Raise', 'exc cause')
LambdaDefNode = namedtuple('LambdaDef', 'args body')
ComparisonNode = namedtuple('Comparison', 'left op exprs')
IfExpNode = namedtuple('IfExp', 'test body or_else')
WhileNode = namedtuple('While', 'test body or_else')
ForNode = namedtuple('For', 'target iter body or_else')
ClassDefNode = namedtuple('ClassDef', 'name bases keywords body decorators')
AttributeNode = namedtuple('Attribute', 'value attr')
SubscriptNode = namedtuple('Subscript', 'value slice')
CallNode = namedtuple('Call', 'func args keywords')
ArgNode = namedtuple('Arg', 'name value unpack')
BinOpNode = namedtuple('BinOp', 'left op right')
UnaryOpNode = namedtuple('UnaryOp', 'op operand')

UnaryOp = Enum('UnaryOp', 'pos inv neg')
BinOp = Enum('BinOp', 'add div sub mod pow mult')
# Argument = namedtuple('Argument', 'name value')
