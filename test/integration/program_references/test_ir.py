import json

import pytest

from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_compiling_reference_programs, get_failing_reference_programs
from test.integration.conftest import run_blip


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_reference_program_ir(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that `blip --ir` emits the correct annotated BlipIR."""

    expected_blip_ir = ref.blip_ir

    result = run_blip(["--ir"], ref.blip_code)

    if result.returncode == 0:
        actual_blip_ir = json.loads(result.stdout)

        assert actual_blip_ir == expected_blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"
    else:
        pytest.fail(f"Program reference '{ref.name}': Failed to parse (error code {result.returncode})\n{result.stderr}")


@pytest.mark.parametrize("ref", get_failing_reference_programs())
def test_reference_program_fails_to_compile(ref: ReferenceProgram):
    """A program with a `#### Compilation` section produces no BlipIR, so `--ir` must refuse it."""

    result = run_blip(["--ir"], ref.blip_code)

    assert result.returncode != 0, f"Program reference '{ref.name}': expected {ref.compile_error} but --ir succeeded"
