"""
These are the interpreting unit tests for the reference programs in the `docs/refs/` directory.
This ensures the Blip code produces the correct outputs when interpreted.
"""

import pytest

from bliplib.interpreter import Interpreter, InterpreterError
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_compiling_reference_programs


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_reference_program_interpreting(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the BlipIR is interpreted correctly."""

    assert ref.blip_ir is not None
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
