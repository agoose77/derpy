from derp import Token, parse, ter, one_plus

# examples
if __name__ == '__main__' and 1:
    # Greedy
    tokens = [Token('var', i) for i in range(5)]

    parse_greedy_example = +ter('var')
    print(parse(parse_greedy_example, tokens))

    parse_one_plus_example = one_plus(ter('var'))
    print(parse(parse_one_plus_example, tokens))

    assert parse(parse_greedy_example, []) == {''}
    assert parse(parse_one_plus_example, []) == set()
