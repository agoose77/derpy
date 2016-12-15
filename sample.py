from argparse import ArgumentParser

from python.tokenizer import tokenize_file
from python.grammar import g
from python.codegen import to_source

from derp import parse
from derp.ast import print_ast, cyclic_colour_formatter


if __name__ == "__main__":
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('-filepath', default="sample.py")
    args = parser.parse_args()

    tokens = list(tokenize_file(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))

    result = parse(g.file_input, tokens)

    if not result:
        print("Failed to parse!")

    else:
        module = result.pop()
        print_ast(module, format_func=cyclic_colour_formatter)#ast.highlight_node_formatter(ast.alias, ast.green, ast.blue))

        source = to_source(module)
        print("Source:")
        print(source)
        import random

        guesses_made = 0

        name = raw_input('Hello! What is your name?\n')

        number = random.randint(1, 20)
        print
        'Well, {0}, I am thinking of a number between 1 and 20.'.format(name)

        while guesses_made < 6:

            guess = int(raw_input('Take a guess: '))

            guesses_made += 1

            if guess < number:
                print
                'Your guess is too low.'

            if guess > number:
                print
                'Your guess is too high.'

            if guess == number:
                break

        if guess == number:
            print
            'Good job, {0}! You guessed my number in {1} guesses!'.format(name, guesses_made)
        else:
            print
            'Nope. The number I was thinking of was {0}'.format(number)