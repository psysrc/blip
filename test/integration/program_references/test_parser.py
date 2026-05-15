import pytest
import json
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs
from test.integration.conftest import run_blip


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_parse(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the Blip code parses into the correct BlipIR."""

    expected_blip_ir = ref.blip_ir

    result = run_blip(["--ir"], ref.blip_code)

    if result.returncode == 0:
        actual_blip_ir = json.loads(result.stdout)

        assert actual_blip_ir == expected_blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"
    else:
        pytest.fail(f"Program reference '{ref.name}': Failed to parse (error code {result.returncode})\n{result.stderr}")
