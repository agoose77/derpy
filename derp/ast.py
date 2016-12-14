from collections import deque, OrderedDict
from io import StringIO


class AST:
    """Base class for ast nodes"""

    _fields = ()

    def __hash__(self):
        return hash(())

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)

    def _to_dict(self):
        return OrderedDict()

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return False

        try:
            return self._to_dict() == other._to_dict()

        except AttributeError:
            return False

    @classmethod
    def subclass(cls, name, field_str=''):
        fields = tuple(f.strip() for f in field_str.split(' ') if f.strip())
        cls_dict = {'_fields': fields}

        # Populate init, hash and repr methods
        if fields:
            body = "\n    ".join("self.{0} = {0}".format(name) for name in fields)
            field_args = ", ".join(fields)
            declare_init = "def __init__(self, {field_args}):\n    {body}"\
                .format(field_args=field_args, body=body)
            exec(declare_init, cls_dict)

            values_str = ", ".join("self.{0}".format(name) for name in fields)
            declare_hash ="def __hash__(self):\n    return hash(tuple(({values_str},)))".format(values_str=values_str)
            exec(declare_hash, cls_dict)

            formatter_str = ", ".join("self.{}".format(name) for name in fields)
            dict_str = ", ".join("{}={{!r}}".format(name, getattr) for name in fields)
            declare_repr ="def __repr__(self):\n    return '{}({})'.format({})".format(name, dict_str, formatter_str)
            exec(declare_repr, cls_dict)

            # Optimised _to_dict method
            dict_str = ", ".join("({0!r}, self.{0})".format(name) for name in fields)
            declare_as_dict = "def _to_dict(self):\n    return OrderedDict([{fields}])".format(fields=dict_str)
            exec(declare_as_dict, globals(), cls_dict)

        return type(name, (cls,), cls_dict)


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

    as_dict = node._to_dict()

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
    yield from node._to_dict().items()


def iter_child_nodes(node):
    for key, value in node._to_dict().items():
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
