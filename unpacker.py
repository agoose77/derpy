def unpack(seq, first=True):
    while True:
        if not isinstance(seq, tuple):
            yield seq
            return

        if first:
            seq, x = seq
        else:
            x, seq = seq

            yield x


x = (1, (2, 3))
a, b, c = unpack(x, False)
print(a, b, c)
