import argparse
import json
from pathlib import Path
from blip.parser import Parser


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-c", "--parse-code")

    args = argument_parser.parse_args()
    parse_code_path = Path(args.parse_code)

    parse_code = parse_code_path.read_text()

    parser = Parser(parse_code)
    ast = parser.parse()

    print(json.dumps(ast, indent=4))


if __name__ == "__main__":
    main()
