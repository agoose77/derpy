_field_init_body = \
"""
def __init__(self, {arg_list}):
    {assignment_body}
"""

_field_assignment_stmt = "self.{0} = {0}"
_repr_getter_stmt = "self.{0}"

_field_repr_body = \
"""
def __repr__(self):
    return f"{cls_name}({repr_str})"
"""


class FieldMeta(type):
    """Metaclass which provides machinery to set named fields on class instance during initialisation.
    
    Use of this decorator automatically invokes the __slots__ mechanism
    """

    def __new__(metacls, name, bases, cls_dict, fields=None):
        if fields:
            field_names = tuple(fields.split())
            assert all(n.isidentifier() for n in field_names), f"invalid field names given {fields}"

            arg_list = ", ".join(field_names)
            assignment_body = "\n    ".join((_field_assignment_stmt.format(n) for n in field_names))
            init_body = _field_init_body.format(arg_list=arg_list, assignment_body=assignment_body)
            exec(init_body, cls_dict)

        else:
            field_names = ()

        # Repr definition
        repr_str = ', '.join(f"{n}={{{_repr_getter_stmt.format(n)}!r}}" for n in field_names)
        repr_body = _field_repr_body.format(cls_name=name, repr_str=repr_str)
        exec(repr_body, cls_dict)

        cls_dict['__slots__'] = field_names
        cls_dict['_fields'] = field_names

        return super().__new__(metacls, name, bases, cls_dict)
