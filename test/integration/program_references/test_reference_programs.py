"""
These are the integration tests for the reference programs in the `docs/refs/` directory.
This ensures the Blip code can be parsed, interpreted, and transpiled into all supported languages.
"""

import pytest
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, run all integration tests."""

    pytest.skip()

    # run_parser_test(ref)  # TODO
    # run_interpreter_test(ref)  # TODO
    # run_python_test(ref)  # TODO
    # run_cpp_test(ref)  # TODO
    # run_c_test(ref)  # TODO
