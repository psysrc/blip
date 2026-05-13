"""
These are the unit tests for the reference programs in the `docs/refs/` directory.
This ensures the Blip code can be parsed and produces the correct outputs when interpreted.
"""

import pytest
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs
from bliplib.parser import Parser, ParserError
from bliplib.interpreter import Interpreter, InterpreterError


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_parsing(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the Blip code parses into the correct BlipIR."""

    parser = Parser()

    try:
        actual_blip_ir = parser.parse(ref.blip_code)
    except ParserError as err:
        pytest.fail(f"Program reference '{ref.name}': Parser error: {err}")

    assert actual_blip_ir == ref.blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_interpreting(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the BlipIR is interpreted correctly."""

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
