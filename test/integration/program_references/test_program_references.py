"""
These are the integration tests for the reference programs in the `docs/refs/` directory.
This ensures the Blip code can be parsed, interpreted, and transpiled into all supported languages.
"""

import pytest
import warnings
from bliplib.parser import Parser, ParserError
from bliplib.interpreter import Interpreter, InterpreterError
from test.common.classes import ReferenceProgram
from test.common.getter import get_reference_programs


def run_interpreter_test(ref: ReferenceProgram):
    interpreter = Interpreter(ref.blip_ir)

    for i, execution in enumerate(ref.executions):
        if execution.expect_success:
            try:
                output = interpreter.run(execution.input_strings)
            except InterpreterError as err:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: {err}")
            else:
                assert output == execution.output_strings, f"Program reference '{ref.name}': Execution #{i + 1}: Incorrect program output"

        else:
            try:
                output = interpreter.run(execution.input_strings)
            except InterpreterError:
                pass
            else:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: Did not throw error, output was {output}")


def run_parser_test(ref: ReferenceProgram):
    parser = Parser()

    try:
        actual_blip_ir = parser.parse(ref.blip_code)
    except ParserError as err:
        pytest.fail(f"Program reference '{ref.name}': Parser error: {err}")

    assert actual_blip_ir == ref.blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, perform all necessary testing."""

    run_parser_test(ref)
    run_interpreter_test(ref)


def test_number_of_reference_programs():
    """
    Check that the correct number of reference programs were tested.
    This is a belts-and-braces test to make sure the test suite is functioning correctly.
    """

    expected_programs = 14

    actual_programs = len(get_reference_programs())

    if actual_programs != expected_programs:
        warnings.warn(
            f"Expected to run {expected_programs} reference program tests but actually ran {actual_programs}"
            "\nIf you've added or removed reference programs, you probably just need to update the number of expected programs."
            "\nHowever, if this warning is unexpected, you should check that the test suite is functioning correctly!"
        )
