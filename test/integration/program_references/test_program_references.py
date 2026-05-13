"""
These are the integration tests for the reference programs in the `docs/refs/` directory.
This ensures the Blip code can be parsed, interpreted, and transpiled into all supported languages.
"""

import pytest
import warnings
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs
from test.common.ref_progs.tests import run_parser_test, run_interpreter_test


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, perform all necessary testing."""

    run_parser_test(ref)
    run_interpreter_test(ref)


def test_number_of_reference_programs():
    """
    Check that the correct number of reference programs were tested.
    This is a belts-and-braces test to make sure the test suite is functioning correctly.
    """

    expected_programs = 14

    actual_programs = len(get_reference_programs())

    if actual_programs != expected_programs:
        warnings.warn(
            f"Expected to run {expected_programs} reference program tests but actually ran {actual_programs}"
            "\nIf you've added or removed reference programs, you probably just need to update the number of expected programs."
            "\nHowever, if this warning is unexpected, you should check that the test suite is functioning correctly!"
        )
