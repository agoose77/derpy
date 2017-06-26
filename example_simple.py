from derp.parsers import Token

print(Token(1,2))

class X(metaclass=type(Token), fields=None):
    pass

print(X())