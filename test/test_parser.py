from bliplib.parser import Parser


def test_nothing_program():
    parser = Parser("")

    assert parser.parse() == {
        "type": "program",
        "statements": [],
    }


def test_hello_world_program():
    parser = Parser('ret "Hello, World!"')

    assert parser.parse() == {
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


def test_hello_world_program_single_quotes():
    parser = Parser("ret 'Hello, World!'")

    assert parser.parse() == {
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


def test_variable_with_string_literal():
    parser = Parser("myname = 'John'")

    assert parser.parse() == {
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
        ],
    }


def test_return_variable():
    parser = Parser("myname = 'John'; ret myname")

    assert parser.parse() == {
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


def test_variable_with_variable():
    parser = Parser("myname = 'John'; username = myname")

    assert parser.parse() == {
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
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "username",
                },
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


def test_string_concatenation():
    parser = Parser("text = 'foo' 'bar' 'baz'")

    assert parser.parse() == {
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


def test_string_decomposition_square_brackets():
    parser = Parser("text -> '[' content ']'")

    assert parser.parse() == {
        "type": "program",
        "statements": [
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
        ],
    }


def test_string_decomposition_email():
    parser = Parser("email -> name '@' *")

    assert parser.parse() == {
        "type": "program",
        "statements": [
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
        ],
    }


def test_identity_program():
    parser = Parser("ret input")

    assert parser.parse() == {
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
