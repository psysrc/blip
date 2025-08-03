import pytest
import warnings
from bliplib.parser import Parser
from bliplib.interpreter import Interpreter, InterpreterError
from test.reference_parser import ReferenceParser
from test.reference_program import ReferenceProgram


def __test_reference_program(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, perform all necessary testing."""

    parser = Parser(ref.blip_code)
    blip_ir = parser.parse()

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


def test_references():
    with open("test/reference.md") as file:
        markdown_text = file.read()

    reference_programs = ReferenceParser(markdown_text).get_reference_programs()

    # Test all of the reference programs
    for prog in reference_programs:
        __test_reference_program(prog)

    # Test that the correct number of reference programs were executed
    # This is belts-and-braces to make sure the test suite is functioning correctly
    expected_programs = 2
    actual_programs = len(reference_programs)
    if actual_programs != expected_programs:
        warnings.warn(
            f"Expected to run {expected_programs} reference program tests but actually ran {actual_programs}"
            "\nIf you've added/removed reference programs, you probably just need to update the number of expected programs."
            "\nHowever, if this warning is unexpected, you should check that the test suite is functioning correctly!"
        )
