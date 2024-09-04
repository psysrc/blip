import pytest
from blip.interpreter import Interpreter


def test_empty_code_raises_error():
    with pytest.raises(RuntimeError):
        Interpreter("")
