import argparse
from pathlib import Path
from blip.tokenizer import Tokenizer


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-c", "--parse-code")

    args = argument_parser.parse_args()
    parse_code_path = Path(args.parse_code)

    parse_code = parse_code_path.read_text()

    tokenizer = Tokenizer(parse_code)

    while not tokenizer.end_of_stream():
        print(f"{tokenizer.next_token()}  ", end="")

    print()


if __name__ == "__main__":
    main()
