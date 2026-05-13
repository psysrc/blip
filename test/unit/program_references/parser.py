import warnings
from test.common.ref_progs.getter import get_reference_programs


def test_number_of_reference_programs():
    """
    Due to the complexity of parsing the reference program markdown, it's sensible to have a dedicated test to ensure the correct
    number of reference programs are found. This is a belts-and-braces test to make sure the test suite is functioning correctly.
    """

    expected_programs = 14

    actual_programs = len(get_reference_programs())

    if actual_programs != expected_programs:
        warnings.warn(
            f"Expected to run {expected_programs} reference program tests but actually ran {actual_programs}"
            "\nIf you've added or removed reference programs, you probably just need to update the number of expected programs."
            "\nHowever, if this warning is unexpected, you should check that the test suite is functioning correctly!"
        )
