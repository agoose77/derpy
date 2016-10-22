def fields(*fields):
    def decorator(cls=object):
        cls_dict = {'__slots__': tuple(fields)}

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
record = namedtuple


DictNode = namedtuple('DictNode', 'keys values')