from derp import Token

print(Token(1,2))

class X(metaclass=type(Token), fields="bill and ben"):
    pass

print(X())