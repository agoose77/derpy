"""AST module for ASTs independent of Python AST"""
from collections import deque
from inspect import currentframe, getmodule
from io import StringIO, TextIOBase
from typing import Any, Generator

from .formatting import cyclic_colour_formatter, Colours, highlight_node_formatter, no_op_formatter

_TUPLE_HASH = hash(())

_ast_declaration = """
class {name}(parent):

    _fields = ({fields})
    __slots__ = '_hash', {slots}

    def __init__(self{init_args}):
        self._hash = hash({hash})
        {init_body}
        
    def __hash__(self):
        return self._hash

    def __repr__(self):
        return {repr}

    def __eq__(self, other):
        return {eq}
    
    @classmethod
    def _make(cls, iterable):
        return cls(*iterable) 

    @classmethod
    def subclass(cls, name, field_str='', module_name=None):
        if module_name is None:
            module_name = _get_caller_caller_module_name()
        return _make_ast_node(name, field_str, cls, module_name)
{property_body}

"""

_ast_property_stmt = """
    @property
    def {name}(self):
        return self._{name}
"""

_field_getter_stmt = "{obj}._{name}"
_field_repr_stmt = "{name}={{!r}}"
_field_init_stmt = "self._{name} = {name}"


def _get_caller_caller_module_name():
    """Return name of module which calls the function from which this function is invoked"""
    frame = currentframe().f_back.f_back
    return getmodule(frame).__name__


def _make_ast_node(name, field_str="", parent_cls=None, module_name=__name__):
    """AST constructor

    :param name: name of AST class
    :param parent_cls: parent AST class
    :param module_name: module name to which class belongs
    """
    if field_str:
        field_names = tuple(field_str.split(' '))
    else:
        field_names = ()

    if parent_cls is None:
        parent_cls = object

    else:
        field_names = parent_cls._fields + field_names

    # Validation
    assert len(set(field_names)) == len(field_names), "Duplicate field name given. Check parent class {}" \
        .format(parent_cls)
    assert all(f.isidentifier() for f in field_names), "Non identifier field name given: {}".format(field_names)

    underscore_field_names_string = ", ".join((repr("_" + f) for f in field_names))
    field_names_string = ", ".join((repr(f) for f in field_names))
    field_names_string_trailer = (field_names_string + ",") if field_names else ""

    field_variables_string = ", ".join(field_names)
    field_variables_trailer = (", ".join(field_names) + ("," if len(field_names) == 1 else ""))

    init_args = (", " + field_variables_string) if field_names else ""
    init_body = ("\n        ".join(_field_init_stmt.format(name=f) for f in field_names) + "\n") if field_names else ""
    hash_string = "({})".format(field_variables_trailer)

    repr_elements = (_field_repr_stmt.format(name=f) for f in field_names)
    repr_values = [_field_getter_stmt.format(obj='self', name=f) for f in field_names]
    repr_string = "'{name}({elements})'.format({values})" \
        .format(name=name, elements=', '.join(repr_elements), values=', '.join(repr_values)) if field_names else \
        "'{}()'".format(name)

    property_body = "\n".join(_ast_property_stmt.format(name=n) for n in field_names)

    if field_names:
        other_repr_values = (_field_getter_stmt.format(obj='other', name=f) for f in field_names)
        eq_string = "self.__class__ is other.__class__ and ({}) == ({})".format(", ".join(repr_values),
                                                                                ", ".join(other_repr_values))

    else:
        eq_string = "self.__class__ == other.__class__"

    class_body = _ast_declaration.format(name=name, base=parent_cls, fields=field_names_string_trailer,
                                         slots=underscore_field_names_string, init_args=init_args, init_body=init_body,
                                         hash=hash_string, repr=repr_string, property_body=property_body, eq=eq_string)

    local_dict = {'parent': parent_cls}

    global_dict = globals().copy()
    global_dict['__name__'] = module_name

    exec(class_body, global_dict, local_dict)
    return local_dict[name]


AST = _make_ast_node("AST", field_str="")


def to_string(node: AST, formatter=None) -> str:
    io = StringIO()
    write_ast(node, io, format_func=formatter)
    return io.getvalue()


def write_ast(node: AST, io: TextIOBase, level=0, indent='  ', format_func=None):
    """Write AST node to writable IO object"""
    if format_func:
        def write(text):
            io.write(format_func(node, level, text))
    else:
        write = io.write

    as_dict = dict(iter_fields(node))

    root_margin = indent * level
    level += 1
    field_margin = indent * level

    # if not as_dict:
    write(f"{node.__class__.__name__}(")

    if as_dict:
        write("\n")
        for i, (name, value) in enumerate(as_dict.items()):
            # Between items separate with comma and newline
            if i != 0:
                write(",\n")

            # Write AstNode
            if isinstance(value, AST):
                write(f"{field_margin}{name} = ")
                write_ast(value, io, level, indent, format_func)

            # Write tuple field
            elif isinstance(value, tuple) and value:
                write(f"{field_margin}{name} = (\n")

                elem_margin = indent * (level + 1)

                write_trailing_comma = True
                for j, elem in enumerate(value):
                    if j != 0:
                        write(",\n")
                        write_trailing_comma = False

                    if isinstance(elem, AST):
                        write(elem_margin)
                        write_ast(elem, io, level + 1, indent, format_func)

                    else:
                        write(f"{elem_margin}{elem!r}")

                if write_trailing_comma:
                    write(",")
                write(f"\n{field_margin})")

            # Write with generic repr
            else:
                write(f"{field_margin}{name} = {value!r}")

        write("\n" + root_margin)
    write(")")


def iter_fields(node: AST):
    """Return iterator over fields of AST node"""
    return ((f, getattr(node, f)) for f in node._fields)


def iter_child_nodes(node: AST) -> Generator[Any, None, None]:
    """Return iterator over AST-derived fields of AST node"""
    for key, value in iter_fields(node):
        if isinstance(value, AST):
            yield value

        elif isinstance(value, tuple):
            yield from (i for i in value if isinstance(i, AST))


def walk(node: AST) -> Generator[AST, None, None]:
    """Walk all nodes in AST

    :param node: root node
    """
    if not isinstance(node, AST):
        raise TypeError(f"Expected AST node, received {type(node).__name__}")

    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(iter_child_nodes(node))
        yield node


class NodeVisitor:
    """Visit all nodes in AST and call corresponding visitor function"""

    def generic_visit(self, node):
        for child in iter_child_nodes(node):
            self.visit(child)
        return node

    def visit(self, node):
        visitor_name = "visit_{}".format(node.__class__.__name__)
        visitor = getattr(self, visitor_name, self.generic_visit)
        return visitor(node)


class NodeTransformer(NodeVisitor):
    """Visit all nodes in AST and return new AST if modified"""

    def _generic_visit_tuple(self, value):
        new_value = []

        for item in value:
            assert isinstance(item, AST)
            item = self.visit(item)

            if item is None:
                continue

            assert isinstance(item, AST)
            new_value.append(item)
        return tuple(new_value)

    def generic_visit(self, node):
        has_changed = False
        new_values = []

        for field, value in iter_fields(node):
            new_value = value

            if isinstance(value, tuple):
                new_value = self._generic_visit_tuple(value)

            elif isinstance(value, AST):
                new_value = self.visit(value)
                assert isinstance(new_value, AST) or new_value is None

            if new_value != value:
                has_changed = True

            new_values.append(new_value)

        if has_changed:
            return node.__class__(*new_values)

        return node
