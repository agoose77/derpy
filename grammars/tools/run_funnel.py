from argparse import ArgumentParser
from pathlib import Path
from time import time

from derp.parsers import parse
from grammars.funnel.grammar import f
from grammars.funnel.tokenizer import tokenize_file

sample_path = Path(__file__).parent / "sample.funnel"


def main():
    parser = ArgumentParser(description='Funnel parser')
    parser.add_argument('--funnel_path', default=sample_path, type=Path)
    args = parser.parse_args()

    tokens = list(tokenize_file(args.funnel_path))
    print("Parsing: {} with {} tokens".format(args.funnel_path, len(tokens)))

    start_time = time()
    result = parse(f.file_input, tokens)
    finish_time = time()

    if not result:
        print("Failed to parse Funnel source")

    elif len(result) > 1:
        print("Ambiguous parse of Funnel source, mutliple parse trees")

    else:
        print("Parsed in {:.3f}s".format(finish_time - start_time))

        module = result.pop()
        print(module)


if __name__ == "__main__":
    main()
