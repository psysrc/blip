from bliplib.interpreter import Interpreter


def test_interpreter_hello_world():
    code = {
        "type": "program",
        "statements": [
            {
                "type": "return",
                "expression": {
                    "type": "literal",
                    "value": "Hello, World!",
                },
            }
        ],
    }

    input_strings: list[str] = []
    output_strings: list[str] = Interpreter(code).run(input_strings)

    assert len(output_strings) == 1
    assert output_strings[0] == "Hello, World!"
