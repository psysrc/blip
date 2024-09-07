import pytest
from blip.interpreter import Interpreter


def test_empty_code_raises_error():
    with pytest.raises(RuntimeError):
        Interpreter("")


def test_identity_code_is_ok():
    Interpreter("IN -> OUT")


def test_identity_code_returns_the_input():
    interpreter = Interpreter("IN -> OUT")

    assert interpreter.run("foo") == "foo"
    assert interpreter.run("bar") == "bar"


def test_alternative_identity_code_returns_the_input():
    interpreter = Interpreter("OUT <- IN")

    assert interpreter.run("foo") == "foo"
    assert interpreter.run("bar") == "bar"
