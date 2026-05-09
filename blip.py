import argparse
import json
from pathlib import Path
import sys
from bliplib.interpreter import Interpreter, InterpreterError
from bliplib.parser import Parser, ParserError


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("file", help="Path of the Blip file to use")

    mode_group = argument_parser.add_argument_group("Run Mode", "How Blip should handle the input file")
    mode_args = mode_group.add_mutually_exclusive_group()
    mode_args.add_argument(
        "-i",
        "--interpret",
        action="store_true",
        help="Execute the program using the Blip Interpreter (this is the default)",
    )
    mode_args.add_argument("-t", "--transpile", metavar="LANG", help="Transpile the program into another language")
    mode_args.add_argument("--ir", action="store_true", help="Output the program's Intermediate Representation")

    argument_parser.add_argument("input_strings", nargs="*", help="Input strings (only used in interpret mode)")

    args = argument_parser.parse_args()

    file_path = Path(args.file)

    if not any([args.ir, args.transpile, args.interpret]):
        args.interpret = True

    try:
        blip_ir = Parser(file_path.read_text()).parse()

    except ParserError as err:
        print(f"Parser error: {err}", file=sys.stderr)
        sys.exit(1)

    except Exception as err:
        print(f"Unknown error encountered while parsing program: {err}", file=sys.stderr)
        sys.exit(2)

    if args.interpret:
        try:
            interpreter = Interpreter(blip_ir)
            input_strings: list[str] = args.input_strings
            output_strings: list[str] = interpreter.run(input_strings)
            print(output_strings)
            sys.exit(0)

        except InterpreterError as err:
            print(f"Interpreter error: {err}", file=sys.stderr)
            sys.exit(1)

        except Exception as err:
            print(f"Unknown error encountered while interpreting program: {err}", file=sys.stderr)
            sys.exit(2)

    if args.transpile:
        raise NotImplementedError("Transpiling is not supported yet.")

    if args.ir:
        print(json.dumps(blip_ir, indent=4))
        sys.exit(0)

    print("Error: Program called with unexpected arguments.", file=sys.stderr)
    print(f"{args}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
