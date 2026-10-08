import argparse
import json
import sys
from pathlib import Path

from bliplib.analysis import analyse
from bliplib.errors import InterpreterError, ParserError, SemanticError, TranspilerError
from bliplib.interpreter import Interpreter
from bliplib.ir import IRError, load
from bliplib.parser import Parser
from bliplib.transpiler import factory as transpiler_factory
from bliplib.transpiler.interface import Transpiler


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
    mode_args.add_argument("--ir", action="store_true", help="Output the program's Intermediate Representation (BlipIR)")
    mode_args.add_argument("--check", action="store_true", help="Check the program for errors and exit")

    argument_parser.add_argument("--prog", action="store_true", help="Create a full program when transpiling")
    argument_parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Dump unanalysed BlipIR with no type checking. Only valid with --ir. Mostly for debugging the analyser itself",
    )
    argument_parser.add_argument("input_strings", nargs="*", help="Input strings (only used in interpret mode)")

    args = argument_parser.parse_args()

    if args.file == "-":
        blip_code = sys.stdin.read()
    else:
        blip_code = Path(args.file).read_text()

    if not any([args.ir, args.transpile, args.interpret, args.check]):
        args.interpret = True

    if args.no_analysis and not args.ir:
        # Skipping analysis in a mode that consumes the result would run a program the analyser rejected
        print("Error: --no-analysis is only valid with --ir", file=sys.stderr)
        sys.exit(1)

    try:
        blip_ir = Parser().parse(blip_code)

    except ParserError as err:
        print(f"Parser error: {err}", file=sys.stderr)
        sys.exit(1)

    try:
        program = load(blip_ir)

    except IRError as err:
        print(f"IR error: {err}", file=sys.stderr)
        sys.exit(1)

    try:
        if not args.no_analysis:
            analyse(program)

    except SemanticError as err:
        print(f"Semantic error: {err}", file=sys.stderr)
        sys.exit(1)

    if args.ir:
        print(json.dumps(program.to_dict(), indent=4))
        sys.exit(0)

    if args.check:
        sys.exit(0)

    if args.interpret:
        try:
            interpreter = Interpreter(program.to_dict())
            input_strings: list[str] = args.input_strings
            output_strings: list[str] = interpreter.run(input_strings)
            print(json.dumps(output_strings))
            sys.exit(0)

        except InterpreterError as err:
            print(f"Interpreter error: {err}", file=sys.stderr)
            sys.exit(1)

    if args.transpile:
        try:
            transpiler: Transpiler = transpiler_factory.get_transpiler(args.transpile)

            if args.prog:
                target_code = transpiler.transpile_program(program.to_dict())
            else:
                target_code = transpiler.transpile_function(program.to_dict())

            print(target_code)
            sys.exit(0)

        except TranspilerError as err:
            print(f"Transpiler error: {err}", file=sys.stderr)
            sys.exit(1)

    print("Error: Program called with unexpected arguments.", file=sys.stderr)
    print(f"{args}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
