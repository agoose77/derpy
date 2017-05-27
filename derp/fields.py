_field_init_body = \
"""
def __init__(self, {arg_list}):
    {assignment_body}
"""

_field_assignment_stmt = "self.{0} = {0}"


class FieldMeta(type):
    """Metaclass which provides machinery to set named fields on class instance during initialisation.
    
    Use of this decorator automatically invokes the __slots__ mechanism
    """

    def __new__(metacls, name, bases, cls_dict, fields=None):
        if fields is not None:
            field_names = tuple(fields.split())

            assert all(f.isidentifier() for f in field_names), "invalid field names given {}".format(fields)

            arg_list = ", ".join(field_names)
            assignment_body = "\n    ".join([_field_assignment_stmt.format(f) for f in field_names])
            init_body = _field_init_body.format(arg_list=arg_list, assignment_body=assignment_body)

            exec(init_body, cls_dict)

        else:
            field_names = ()

        cls_dict['__slots__'] = field_names
        cls_dict['_fields'] = field_names

        return super().__new__(metacls, name, bases, cls_dict)
