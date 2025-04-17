import argparse
import json
from pathlib import Path
from blip.parser import Parser


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-f", "--file", required=True, help="The path to the file to parse")

    args = argument_parser.parse_args()
    file_path = Path(args.file)

    blip_code = file_path.read_text()

    parser = Parser(blip_code)
    blipir = parser.parse()

    print(json.dumps(blipir, indent=4))


if __name__ == "__main__":
    main()
