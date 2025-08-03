"""
This unit test runs through all of the example programs in the `docs/refs/` directory and tests them.
This involves taking the Blip code, parsing it, then interpreting it with all of the inputs and asserting the correct outputs.
"""

from typing import Optional
import pytest
import warnings
import os
from bliplib.parser import Parser, ParserError
from bliplib.interpreter import Interpreter, InterpreterError
from test.reference_parser import ReferenceParser
from test.reference_program import ReferenceProgram


__reference_programs: Optional[list[ReferenceProgram]] = None


def get_reference_programs() -> list[ReferenceProgram]:
    global __reference_programs
    if __reference_programs is None:
        ref_program_dir = "docs/refs"
        ref_program_files = [
            f"{ref_program_dir}/{f}" for f in os.listdir(ref_program_dir) if os.path.isfile(os.path.join(ref_program_dir, f))
        ]

        print(f"Found files: {ref_program_files}")

        __reference_programs = []

        for ref_prog_file in ref_program_files:
            if ref_prog_file == "docs/refs/README.md":
                continue

            with open(ref_prog_file) as file:
                markdown_text = file.read()

            found_programs = ReferenceParser(markdown_text).get_reference_programs()

            __reference_programs.extend(found_programs)

    return __reference_programs


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, perform all necessary testing."""

    parser = Parser(ref.blip_code)

    try:
        blip_ir = parser.parse()
    except ParserError as err:
        pytest.fail(f"Program reference '{ref.name}': Parser error: {err}")

    assert blip_ir == ref.blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"

    interpreter = Interpreter(blip_ir)

    for i, exec in enumerate(ref.executions):
        if exec.success:
            try:
                output = interpreter.run(exec.input_strings)
            except InterpreterError as err:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: {err}")
            else:
                assert output == exec.output_strings, f"Program reference '{ref.name}': Execution #{i + 1}: Incorrect program output"

        else:
            try:
                output = interpreter.run(exec.input_strings)
            except InterpreterError:
                pass
            else:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: Did not throw error, output was {output}")


def test_number_of_reference_programs():
    """
    Test that the correct number of reference programs were executed
    This is a belts-and-braces test to make sure the test suite is functioning correctly
    """

    expected_programs = 2

    actual_programs = len(get_reference_programs())

    if actual_programs != expected_programs:
        warnings.warn(
            f"Expected to run {expected_programs} reference program tests but actually ran {actual_programs}"
            "\nIf you've added/removed reference programs, you probably just need to update the number of expected programs."
            "\nHowever, if this warning is unexpected, you should check that the test suite is functioning correctly!"
        )
