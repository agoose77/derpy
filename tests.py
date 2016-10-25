from derp import Token, parse, ter

# examples
if __name__ == '__main__' and 1:
    # Greedy
    tokens = [Token('var', i) for i in range(5)]
    parse_greedy_example = +ter('var')
    print(parse(parse_greedy_example, tokens))
