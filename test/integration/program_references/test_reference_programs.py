"""
These are the integration tests for the reference programs in the `docs/refs/` directory.
This ensures the Blip code can be parsed, interpreted, and transpiled into all supported languages.
"""

import pytest
import json
import subprocess
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs


@pytest.fixture(scope="module", autouse=True, name="blip")
def blip_binary():
    subprocess.run(["./build.sh"], check=True)  # Build the blip CLI tool

    blip = "./build/bin/blip"
    result = subprocess.run([blip, "--help"], stdout=subprocess.DEVNULL)  # Check it built correctly
    if result.returncode != 0:
        raise RuntimeError("Failed to build blip executable")

    return blip


def test_hello_world_interpret(blip):
    result = subprocess.run([blip, "-"], input="ret 'Hello World'", text=True, check=True, capture_output=True)

    assert result.stdout == "['Hello World']\n"


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_parsing(blip, ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the Blip code parses into the correct BlipIR."""

    expected_blip_ir = ref.blip_ir

    result = subprocess.run([blip, "-", "--ir"], input=ref.blip_code, text=True, check=True, capture_output=True)
    actual_blip_ir = json.loads(result.stdout)

    assert actual_blip_ir == expected_blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_interpreting(blip, ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the BlipIR is interpreted correctly."""

    pytest.skip()


# @pytest.mark.parametrize("ref", get_reference_programs())
# def test_reference_program_transpile_python(blip, ref: ReferenceProgram):
#     """Given a `ReferenceProgram`, test that the BlipIR is transpiled into Python correctly."""

#     pytest.skip()


# @pytest.mark.parametrize("ref", get_reference_programs())
# def test_reference_program_transpile_cpp(blip, ref: ReferenceProgram):
#     """Given a `ReferenceProgram`, test that the BlipIR is transpiled into C++ correctly."""

#     pytest.skip()


# @pytest.mark.parametrize("ref", get_reference_programs())
# def test_reference_program_transpile_c(blip, ref: ReferenceProgram):
#     """Given a `ReferenceProgram`, test that the BlipIR is transpiled into C correctly."""

#     pytest.skip()
