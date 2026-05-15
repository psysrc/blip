"""
These are the integration tests for the reference programs in the `docs/refs/` directory.
This ensures the Blip code can be parsed, interpreted, and transpiled into all supported languages.
"""

import pytest
import json
import subprocess
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs


__blip_binary = "./build/bin/blip"


def __run_blip(blip_args: list[str], stdin: str) -> subprocess.CompletedProcess:
    prog_args = [__blip_binary, "-"] + blip_args
    return subprocess.run(prog_args, input=stdin, text=True, capture_output=True)


@pytest.fixture(scope="module", autouse=True)
def blip_binary():
    subprocess.run(["./build.sh"], check=True)  # Build the blip CLI tool

    result = subprocess.run([__blip_binary, "--help"], stdout=subprocess.DEVNULL)  # Check it built correctly
    if result.returncode != 0:
        raise RuntimeError(f"Failed to build blip executable: {result.stderr}")


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_parse(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the Blip code parses into the correct BlipIR."""

    expected_blip_ir = ref.blip_ir

    result = __run_blip(["--ir"], ref.blip_code)

    if result.returncode == 0:
        actual_blip_ir = json.loads(result.stdout)

        assert actual_blip_ir == expected_blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"
    else:
        pytest.fail(f"Program reference '{ref.name}': Failed to parse (error code {result.returncode})\n{result.stderr}")


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_interpret(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the BlipIR is interpreted correctly."""

    for i, execution in enumerate(ref.executions):
        blip_args = ["--interpret"] + execution.input_strings
        result = __run_blip(blip_args, ref.blip_code)

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


@pytest.mark.xfail(reason="Python transpiling is still under development")
@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_transpile_python(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the BlipIR is transpiled into Python and the Python code behaves correctly."""

    blip_args = ["--transpile", "python", "--prog"]
    blip_result = __run_blip(blip_args, ref.blip_code)

    if blip_result.returncode != 0:
        pytest.fail(f"Program reference '{ref.name}': Failed to transpile to Python\n{blip_result.stderr}")

    python_code = blip_result.stdout

    for i, execution in enumerate(ref.executions):
        python_args = ["python3", "-"] + execution.input_strings
        python_result = subprocess.run(python_args, input=python_code, text=True, capture_output=True)

        if execution.expect_success:
            if python_result.returncode == 0:
                actual_output = json.loads(python_result.stdout)
                expected_output = execution.output_strings
                assert actual_output == expected_output, f"Program reference '{ref.name}': Execution #{i + 1}: Incorrect program output"

            else:
                pytest.fail(
                    f"Program reference '{ref.name}': Execution #{i + 1}: Error code ({blip_result.returncode})\n{python_result.stderr}"
                )

        else:
            if python_result.returncode == 0:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: Did not throw error, output was {python_result.stdout}")


# @pytest.mark.parametrize("ref", get_reference_programs())
# def test_reference_program_transpile_cpp(ref: ReferenceProgram):
#     """Given a `ReferenceProgram`, test that the BlipIR is transpiled into C++ and the C++ code behaves correctly."""

#     pytest.skip()


# @pytest.mark.parametrize("ref", get_reference_programs())
# def test_reference_program_transpile_c(ref: ReferenceProgram):
#     """Given a `ReferenceProgram`, test that the BlipIR is transpiled into C and the C code behaves correctly."""

#     pytest.skip()
