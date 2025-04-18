from blip.parser import Parser


def test_hello_world_program():
    parser = Parser('ret "Hello, World!"')

    assert parser.parse() == {
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


def test_hello_world_program_single_quotes():
    parser = Parser("ret 'Hello, World!'")

    assert parser.parse() == {
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


def test_identity_program():
    parser = Parser("")

    assert parser.parse() == {
        "type": "program",
        "statements": [],
    }


def test_variable_with_literal():
    parser = Parser("myname = 'John'")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "variable": {
                    "type": "identifier",
                    "name": "myname",
                },
                "value": {
                    "type": "literal",
                    "value": "John",
                },
            }
        ],
    }


def test_return_variable():
    parser = Parser("myname = 'John'; ret myname")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "variable": {
                    "type": "identifier",
                    "name": "myname",
                },
                "value": {
                    "type": "literal",
                    "value": "John",
                },
            },
            {
                "type": "return",
                "expression": {
                    "type": "identifier",
                    "name": "myname",
                },
            },
        ],
    }


def test_variable_with_variable():
    parser = Parser("myname = 'John'; username = myname")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "variable": {
                    "type": "identifier",
                    "name": "myname",
                },
                "value": {
                    "type": "literal",
                    "value": "John",
                },
            },
            {
                "type": "assignment",
                "variable": {
                    "type": "identifier",
                    "name": "username",
                },
                "value": {
                    "type": "identifier",
                    "name": "myname",
                },
            },
        ],
    }


def test_string_concatenation():
    parser = Parser("text = 'foo' 'bar' 'baz'")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "variable": {
                    "type": "identifier",
                    "name": "text",
                },
                "value": {
                    "type": "expression",
                    "operands": [
                        {
                            "type": "literal",
                            "value": "foo",
                        },
                        {
                            "type": "literal",
                            "value": "bar",
                        },
                        {
                            "type": "literal",
                            "value": "baz",
                        },
                    ],
                },
            }
        ],
    }


def test_string_decomposition():
    parser = Parser("input -> '[' text ']'")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "decomposition",
                "variable": {
                    "type": "identifier",
                    "name": "input",
                },
                "pattern": {
                    "type": "expression",
                    "operands": [
                        {
                            "type": "literal",
                            "value": "[",
                        },
                        {
                            "type": "identifier",
                            "name": "text",
                        },
                        {
                            "type": "literal",
                            "value": "]",
                        },
                    ],
                },
            }
        ],
    }
