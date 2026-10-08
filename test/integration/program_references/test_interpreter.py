import json

import pytest

from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_compiling_reference_programs, get_failing_reference_programs
from test.integration.conftest import run_blip


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_reference_program_interpret(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the BlipIR is interpreted correctly."""

    for i, execution in enumerate(ref.executions):
        blip_args = ["--interpret"] + execution.input_strings
        result = run_blip(blip_args, ref.blip_code)

        if execution.expect_success:
            if result.returncode == 0:
                actual_output = json.loads(result.stdout)
                expected_output = execution.output_strings
                assert actual_output == expected_output, f"Program reference '{ref.name}': Execution #{i + 1}: Incorrect program output"

            else:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: Error code {result.returncode}\n{result.stderr}")

        else:
            if result.returncode == 0:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: Did not throw error, output was {result.stdout}")


@pytest.mark.parametrize("ref", get_failing_reference_programs())
def test_reference_program_that_fails_to_compile_is_not_interpreted(ref: ReferenceProgram):
    """A program rejected by the front end never runs, so there are no executions to check."""

    result = run_blip(["--interpret"], ref.blip_code)

    assert result.returncode != 0, f"Program reference '{ref.name}': expected {ref.compile_error} but it was interpreted"
    assert ref.executions == [], f"Program reference '{ref.name}': a program that cannot compile records no executions"
