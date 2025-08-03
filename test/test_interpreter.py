import pytest
from bliplib.interpreter import Interpreter, InterpreterError


def test_interpreter_hello_world():
    interpreter = Interpreter(
        {
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
        }
    )

    assert interpreter.run([]) == ["Hello, World!"]


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
                },
            ],
        }
    )

    assert interpreter.run([]) == []
    assert interpreter.run(["Hello", "World"]) == ["Hello", "World"]


def test_variables():
    interpreter = Interpreter(
        {
            "type": "program",
            "statements": [
                {
                    "type": "assignment",
                    "identifier": {
                        "type": "identifier",
                        "name": "myname",
                    },
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "string_literal",
                            "value": "John",
                        },
                    },
                },
                {
                    "type": "return",
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "identifier",
                            "name": "myname",
                        },
                    },
                },
            ],
        }
    )

    assert interpreter.run([]) == ["John"]


def test_string_concatenation():
    interpreter = Interpreter(
        {
            "type": "program",
            "statements": [
                {
                    "type": "return",
                    "expression": {
                        "type": "expression",
                        "value": {
                            "type": "concatenation",
                            "operands": [
                                {
                                    "type": "string_literal",
                                    "value": "foo",
                                },
                                {
                                    "type": "string_literal",
                                    "value": "bar",
                                },
                                {
                                    "type": "string_literal",
                                    "value": "baz",
                                },
                            ],
                        },
                    },
                },
            ],
        }
    )

    assert interpreter.run([]) == ["foobarbaz"]


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
                            "type": "identifier",
                            "name": "dont_care",
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
