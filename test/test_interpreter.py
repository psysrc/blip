import pytest
from bliplib.interpreter import Interpreter, InterpreterError


def test_interpreter_hello_world():
    code = {
        "type": "program",
        "statements": [
            {
                "type": "return",
                "expression": {
                    "type": "expression",
                    "value": {
                        "type": "literal",
                        "value": "Hello, World!",
                    },
                },
            }
        ],
    }

    input_strings: list[str] = []
    output_strings: list[str] = Interpreter(code).run(input_strings)

    assert len(output_strings) == 1
    assert output_strings[0] == "Hello, World!"


def test_unexpected_code_causes_interpreter_error():
    code = {"type": "huh?"}

    with pytest.raises(InterpreterError):
        Interpreter(code).run([])


def test_identity_program():
    interpreter = Interpreter(
        {
            "type": "program",
            "statements": [
                {
                    "type": "return",
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "identifier",
                            "name": "input",
                        },
                    },
                }
            ],
        }
    )

    assert interpreter.run([]) == []
    assert interpreter.run(["Hello", "World"]) == ["Hello", "World"]
