from .fields import FieldMeta


class Token(metaclass=FieldMeta, fields="first second"):
    def __hash__(self):
        return hash((self.first, self.second))

    def __eq__(self, other):
        return type(other) is self.__class__ and other.first == self.first and other.second == self.second
