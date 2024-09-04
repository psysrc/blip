import pytest
from blip.interpreter import Interpreter


def test_empty_code_raises_error():
    with pytest.raises(RuntimeError):
        Interpreter("")

def test_identity_code_is_ok():
    interpreter = Interpreter("IN -> OUT")
