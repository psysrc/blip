import pytest
from bliplib.interpreter import Interpreter, InterpreterError


"""
The tests here are intentionally thin on numbers.
The "Reference Programs" documentation contains a more comprehensive suite of tests for the interpreter (under docs/refs/).
"""


def test_unexpected_code_causes_interpreter_error():
    ir = {"type": "huh?"}

    with pytest.raises(InterpreterError):
        Interpreter(ir).run([])
