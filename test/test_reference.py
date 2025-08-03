import pytest
from dataclasses import dataclass
from bliplib.parser import Parser
from bliplib.interpreter import Interpreter, InterpreterError


@dataclass
class BlipInterpreterTest:
    input_strings: list[str]
    success: bool
    output_strings: list[str]


@dataclass
class BlipReference:
    blip_code: str
    blip_ir: dict
    interpreter_tests: list[BlipInterpreterTest]


def __test_reference(reference: BlipReference):
    """Given a `Reference`, perform all necessary testing."""

    parser = Parser(reference.blip_code)
    blip_ir = parser.parse()

    assert blip_ir == reference.blip_ir

    interpreter = Interpreter(blip_ir)

    for test in reference.interpreter_tests:
        if test.success:
            output = interpreter.run(test.input_strings)
            assert output == test.output_strings
        else:
            with pytest.raises(InterpreterError):
                interpreter.run(test.input_strings)


def test_hello_world():
    ref = BlipReference(
        blip_code='ret "Hello, World!"',
        blip_ir={
            "type": "program",
            "statements": [
                {
                    "type": "return",
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "string_literal",
                            "value": "Hello, World!",
                        },
                    },
                },
            ],
        },
        interpreter_tests=[
            BlipInterpreterTest(input_strings=[], success=True, output_strings=["Hello, World!"]),
            BlipInterpreterTest(input_strings=["nothing", "here", "matters"], success=True, output_strings=["Hello, World!"]),
        ],
    )

    __test_reference(ref)
