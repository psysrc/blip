"""Unit tests for the transpiler factory in `bliplib/transpiler/factory.py`."""

import pytest

from bliplib.errors import TranspilerError
from bliplib.transpiler.factory import get_transpiler
from bliplib.transpiler.interface import Transpiler
from bliplib.transpiler.python import PythonTranspiler


@pytest.mark.parametrize(
    ("name", "expected_transpiler"),
    [
        pytest.param("python", PythonTranspiler),
    ],
)
def test_a_registered_name_gives_that_transpiler(name: str, expected_transpiler: type):
    actual_transpiler = get_transpiler(name)

    assert isinstance(actual_transpiler, expected_transpiler)
    assert issubclass(expected_transpiler, Transpiler)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("matlab", id="a language with no back end"),
        pytest.param("Python", id="the right language, wrongly cased"),
        pytest.param("", id="no language at all"),
    ],
)
def test_an_unregistered_name_raises_a_transpiler_error(name: str):
    with pytest.raises(TranspilerError):
        get_transpiler(name)
