from derp.parsers import lit, Token, Recurrence, parse


if __name__ == "__main__":
    parser = Recurrence()
    parser.parser = ~(parser & lit('1'))

    tokens = [Token('1', '1') for i in range(1000)]
    import time
    start = time.time()
    result = parse(parser, tokens)
    print(time.time() - start)
