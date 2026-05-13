"""
These are the unit tests for the reference programs in the `docs/refs/` directory.
This ensures the Blip code can be parsed and produces the correct outputs when interpreted.
"""

import pytest
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs
from test.common.ref_progs.tests import run_parser_test, run_interpreter_test


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, run all unit tests."""

    run_parser_test(ref)
    run_interpreter_test(ref)
