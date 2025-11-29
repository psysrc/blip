import pytest
from bliplib.parser import Parser
from bliplib.parser.tokenizer import Token, TokenizerError


def test_syntax_error_raises_tokenizer_error():
    with pytest.raises(TokenizerError):
        Parser("%67£$QGR _++ )(GFds")


def test_token_str():
    token = Token("string_literal", "hello")

    assert str(token) == "TOKEN['string_literal' | 'hello']"


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


def test_int_variable():
    parser = Parser("num = 5")

    assert parser.parse() == {
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
        ],
    }


def test_variable_index_with_integer_literal():
    parser = Parser("ret input[0]")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "return",
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
        ],
    }


def test_variable_index_with_integer_variable():
    parser = Parser("idx = 0; ret input[idx]")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "idx",
                },
                "expression": {
                    "type": "expression",
                    "value": {
                        "type": "integer_literal",
                        "value": 0,
                    },
                },
            },
            {
                "type": "return",
                "expression": {
                    "type": "expression",
                    "value": {
                        "type": "index",
                        "identifier": {
                            "type": "identifier",
                            "name": "input",
                        },
                        "index": {
                            "type": "identifier",
                            "name": "idx",
                        },
                    },
                },
            },
        ],
    }


def test_empty_list_variable():
    parser = Parser("list = []")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "list",
                },
                "expression": {
                    "type": "expression",
                    "value": {
                        "type": "list",
                        "elements": [],
                    },
                },
            },
        ],
    }


def test_list_variable_one_element():
    parser = Parser('list = ["a"]')

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "list",
                },
                "expression": {
                    "type": "expression",
                    "value": {
                        "type": "list",
                        "elements": [
                            {
                                "type": "expression",
                                "value": {
                                    "type": "string_literal",
                                    "value": "a",
                                },
                            },
                        ],
                    },
                },
            },
        ],
    }


def test_list_variable_many_elements():
    parser = Parser('list = ["a", "b", "c"]')

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "list",
                },
                "expression": {
                    "type": "expression",
                    "value": {
                        "type": "list",
                        "elements": [
                            {
                                "type": "expression",
                                "value": {
                                    "type": "string_literal",
                                    "value": "a",
                                },
                            },
                            {
                                "type": "expression",
                                "value": {
                                    "type": "string_literal",
                                    "value": "b",
                                },
                            },
                            {
                                "type": "expression",
                                "value": {
                                    "type": "string_literal",
                                    "value": "c",
                                },
                            },
                        ],
                    },
                },
            },
        ],
    }
