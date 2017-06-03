"""AST module for ASTs independent of Python AST"""
from collections import deque
from io import StringIO


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
    def subclass(cls, name, field_str='', module_name=__name__):
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


def _make_ast_node(name, field_str="", parent_cls=None, module_name=__name__):
    if field_str:
        field_names = tuple(field_str.split(' '))
    else:
        field_names = ()

    if parent_cls is None:
        parent_cls = object

    else:
        field_names = parent_cls._fields + field_names

    # Validation
    assert len(set(field_names)) == len(field_names), "Duplicate field name given. Check parent class {}"\
        .format(parent_cls)
    assert all(f.isidentifier() for f in field_names), "Non identifier field name given: {}".format(field_names)

    underscore_field_names_string = ", ".join((repr("_"+f) for f in field_names))
    field_names_string = ", ".join((repr(f) for f in field_names))
    field_names_string_trailer = (field_names_string + ",") if field_names else ""

    field_variables_string = ", ".join(field_names)
    field_variables_trailer = (", ".join(field_names) + ("," if len(field_names) == 1 else ""))

    init_args = (", " + field_variables_string) if field_names else ""
    init_body = ("\n        ".join(_field_init_stmt.format(name=f) for f in field_names) + "\n") if field_names else ""
    hash_string = "({})".format(field_variables_trailer)

    repr_elements = (_field_repr_stmt.format(name=f) for f in field_names)
    repr_values = [_field_getter_stmt.format(obj='self', name=f) for f in field_names]
    repr_string = "'{name}({elements})'.format({values})"\
        .format(name=name, elements=', '.join(repr_elements), values=', '.join(repr_values)) if field_names else \
        "'{}()'".format(name)

    property_body = "\n".join(_ast_property_stmt.format(name=n) for n in field_names)

    if field_names:
        other_repr_values = (_field_getter_stmt.format(obj='other', name=f) for f in field_names)
        eq_string  = "self.__class__ is other.__class__ and ({}) == ({})".format(", ".join(repr_values), ", ".join(other_repr_values))

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


class Colours:

    @staticmethod
    def red(text):
        return '\x1b[0;31;m' + text

    @staticmethod
    def blue(text):
        return '\x1b[0;34;m' + text

    @staticmethod
    def green(text):
        return '\x1b[0;32;m' + text

    @staticmethod
    def white(text):
        return '\33[0;37;m' + text


def cyclic_colour_formatter(node, level, text):
    all_colours = Colours.red, Colours.green, Colours.blue, Colours.white
    colour_f = all_colours[level % len(all_colours)]
    return colour_f(text)


def highlight_node_formatter(node_cls, match_format, other_format):
    def wrapper(node, level, text):
        if isinstance(node, node_cls):
            return match_format(text)
        return other_format(text)
    return wrapper


def write_ast(node, writer, level=0, indent='  ', format_func=None):
    if format_func:
        def write(text):
            writer.write(format_func(node, level, text))

    else:
        write = writer.write

    root_margin = indent * level

    as_dict = dict(iter_fields(node))

    field_margin = (level + 1) * indent

    if not as_dict:
        write("{}()".format(node.__class__.__name__))

    else:
        write("{}(\n".format(node.__class__.__name__))

        for i, (name, value) in enumerate(as_dict.items()):
            # Between items separate with comma and newline
            if i != 0:
                write(",\n")

            # Write AstNode
            if isinstance(value, AST):
                field_text_left = field_margin + "{} = ".format(name)
                write(field_text_left)
                write_ast(value, writer, level + 1, indent, format_func)

            # Write tuple field
            elif type(value) is tuple:
                field_text_left = field_margin + "{} = (\n".format(name)
                write(field_text_left)

                j = -1
                elem_margin = (level + 2) * indent
                for j, elem in enumerate(value):
                    if j != 0:
                        write(",\n")

                    if isinstance(elem, AST):
                        write(elem_margin)
                        write_ast(elem, writer, level + 2, indent, format_func)

                    else:
                        write(elem_margin + repr(elem))

                if j > -1:
                    write(",\n")
                    write(field_margin + ")")

                else:
                    write(field_margin+")")

            # Write repr
            else:
                write(field_margin + "{} = {!r}".format(name, value))

        write("\n"+root_margin+")")


def iter_fields(node):
    return ((f, getattr(node, f)) for f in node._fields)


def iter_child_nodes(node):
    for key, value in iter_fields(node):

        if isinstance(value, AST):
            yield value

        elif isinstance(value, tuple):
            for item in value:
                if isinstance(item, AST):
                    yield item


def walk(node):
    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(iter_child_nodes(node))
        yield node


class NodeVisitor:

    def generic_visit(self, node):
        for child in iter_child_nodes(node):
            self.visit(child)

    def visit(self, node):
        visitor_name = "visit_{}".format(node.__class__.__name__)
        visitor = getattr(self, visitor_name, self.generic_visit)
        visitor(node)


class NodeTransformer(NodeVisitor):

    def generic_visit(self, node):
        for field, old_value in iter_fields(node):
            if isinstance(old_value, tuple):
                new_values = []

                for value in old_value:
                    if isinstance(value, AST):
                        value = self.visit(value)
                        if value is None:
                            continue

                        elif not isinstance(value, AST):
                            new_values.extend(value)
                            continue

                    new_values.append(value)
                old_value[:] = new_values

            elif isinstance(old_value, AST):
                new_node = self.visit(old_value)

                if new_node is None:
                    delattr(node, field)

                else:
                    setattr(node, field, new_node)

        return node


def print_ast(node, format_func=None):
    io = StringIO()
    write_ast(node, io, format_func=format_func)
    print(io.getvalue())
