# from derp.parsers import Recurrence, Token, ter
#
#
# s = Recurrence()
# s.parser = ~(s & ter('a'))
# N = 1000
# tokens = [Token('a', 'a') for i in range(N)]
#
#
# times = []
#
# from time import monotonic
# for i in range(10):
#
#     s = Recurrence()
#     s.parser = ~(s & ter('a'))
#
#     started = monotonic()
#
#     parser = s
#     for token in tokens:
#         parser = parser.derive(token).compact()
#
#     result = parser.derive_null()
#     end = monotonic()
#     dt = end - started
#
#     times.append(dt)
#
#
# print(times)


_field_init_body = \
"""
def __init__(self, {arg_list}):
    {assignment_body}
"""

_field_assignment_stmt = "self.{0} = {0}"


class BaseParserMeta(type):
    def __new__(metacls, name, bases, cls_dict, fields=None):
        if fields is not None:
            field_names = tuple(fields.split())
            assert all(f.isidentifier() for f in field_names), "invalid field names given {}".format(fields)

            arg_list = ", ".join(field_names)
            assignment_body = "\n    ".join([_field_assignment_stmt.format(f) for f in field_names])
            init_body = _field_init_body.format(arg_list=arg_list, assignment_body=assignment_body)

            exec(init_body, cls_dict)

            cls_dict['__slots__'] = field_names
            cls_dict['_fields'] = field_names

        return super().__new__(metacls, name, bases, cls_dict)


class BaseParser(metaclass=BaseParserMeta):
    pass


class Parser(BaseParser, fields="x y"):
    pass