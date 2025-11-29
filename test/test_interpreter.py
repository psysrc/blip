import pytest
from bliplib.interpreter import Interpreter, InterpreterError


def test_unexpected_code_causes_interpreter_error():
    code = {"type": "huh?"}

    with pytest.raises(InterpreterError):
        Interpreter(code).run([])


def test_decomposition_square_brackets():
    interpreter = Interpreter(
        {
            "type": "program",
            "statements": [
                {
                    "type": "assignment",
                    "identifier": {
                        "type": "identifier",
                        "name": "text",
                    },
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "string_literal",
                            "value": "[fudge]",
                        },
                    },
                },
                {
                    "type": "decomposition",
                    "identifier": {
                        "type": "identifier",
                        "name": "text",
                    },
                    "pattern": [
                        {
                            "type": "string_literal",
                            "value": "[",
                        },
                        {
                            "type": "identifier",
                            "name": "content",
                        },
                        {
                            "type": "string_literal",
                            "value": "]",
                        },
                    ],
                },
                {
                    "type": "return",
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "identifier",
                            "name": "content",
                        },
                    },
                },
            ],
        }
    )

    assert interpreter.run([]) == ["fudge"]


def test_decomposition_email():
    interpreter = Interpreter(
        {
            "type": "program",
            "statements": [
                {
                    "type": "assignment",
                    "identifier": {
                        "type": "identifier",
                        "name": "email",
                    },
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "string_literal",
                            "value": "bob.john@gmail.com",
                        },
                    },
                },
                {
                    "type": "decomposition",
                    "identifier": {
                        "type": "identifier",
                        "name": "email",
                    },
                    "pattern": [
                        {
                            "type": "identifier",
                            "name": "name",
                        },
                        {
                            "type": "string_literal",
                            "value": "@",
                        },
                        {
                            "type": "decomposition_wildcard",
                        },
                    ],
                },
                {
                    "type": "return",
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "identifier",
                            "name": "name",
                        },
                    },
                },
            ],
        }
    )

    assert interpreter.run([]) == ["bob.john"]


def test_integer_literal_as_expression():
    interpreter = Interpreter(
        {
            "type": "program",
            "statements": [
                {
                    "type": "assignment",
                    "identifier": {
                        "type": "identifier",
                        "name": "num",
                    },
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "integer_literal",
                            "value": 5,
                        },
                    },
                },
                {
                    "type": "return",
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "string_literal",
                            "value": "",
                        },
                    },
                },
            ],
        }
    )

    assert interpreter.run([]) == [""]


def test_list_index_with_integer_literal():
    interpreter = Interpreter(
        {
            "type": "program",
            "statements": [
                {
                    "type": "assignment",
                    "identifier": {
                        "type": "identifier",
                        "name": "first",
                    },
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "index",
                            "identifier": {
                                "type": "identifier",
                                "name": "input",
                            },
                            "index": {
                                "type": "integer_literal",
                                "value": 0,
                            },
                        },
                    },
                },
                {
                    "type": "return",
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "identifier",
                            "name": "first",
                        },
                    },
                },
            ],
        }
    )

    assert interpreter.run(["a"]) == ["a"]
    assert interpreter.run(["a", "b"]) == ["a"]
    assert interpreter.run(["a", "b", "c"]) == ["a"]
