import pytest
import json
import subprocess
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs
from test.integration.conftest import run_blip


def __get_progs():
    xfail_progs = [
        "Identity Program",
        "Variable Assignment",
        "Concatenation",
        "Decomposition",
        "Indexing into Lists",
        "Fixed Input Directive",
        "Fixed Output Directive (Error case)",
        "Named Input Directive",
        "Range Input Directive",
        "Range Output Directive (Error case)",
    ]

    # See https://docs.pytest.org/en/latest/how-to/skipping.html#skip-xfail-with-parametrize
    return [pytest.param(p, marks=pytest.mark.xfail(strict=True)) if p.name in xfail_progs else p for p in get_reference_programs()]


@pytest.mark.parametrize("ref", __get_progs())
def test_reference_program_transpile_python(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the BlipIR is transpiled into Python and the Python code behaves correctly."""

    blip_args = ["--transpile", "python", "--prog"]
    blip_result = run_blip(blip_args, ref.blip_code)

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
