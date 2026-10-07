import pytest

from bliplib.parser import Parser
from bliplib.parser.blip_parser import ParserError


@pytest.fixture
def parser():
    return Parser()


def test_invalid_syntax_raises_tokenizer_error(parser):
    with pytest.raises(ParserError):
        parser.parse("%67£$QGR _++ )(GFds")


def test_bad_expression_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse("ret")


def test_bad_identifier_statement_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse("hello hello")


def test_bad_statement_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse(",")


def test_bad_decomposition_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse("foo -> []")


def test_indexing_in_decomposition_pattern_raises_parser_error(parser):
    """A decomposition pattern element is a string literal, a capturing variable or a wildcard - never a value expression."""

    with pytest.raises(ParserError):
        parser.parse("foo -> bar[0]")

    with pytest.raises(ParserError):
        parser.parse('foo -> name "@" rest[1]')


def test_bad_index_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse("foo = bar['z']")


def test_string_decomposition_square_brackets(parser):
    assert parser.parse("text -> '[' content ']'") == {
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


def test_string_decomposition_email(parser):
    assert parser.parse("email -> name '@' *") == {
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


def test_int_variable(parser):
    assert parser.parse("num = 5") == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "num",
                },
                "expression": {
                    "type": "integer_literal",
                    "value": 5,
                },
            },
        ],
    }


def test_variable_index_with_integer_literal(parser):
    assert parser.parse("ret input[0]") == {
        "type": "program",
        "statements": [
            {
                "type": "return",
                "expression": {
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
        ],
    }


def test_variable_index_with_integer_variable(parser):
    assert parser.parse("idx = 0; ret input[idx]") == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "idx",
                },
                "expression": {
                    "type": "integer_literal",
                    "value": 0,
                },
            },
            {
                "type": "return",
                "expression": {
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
        ],
    }


def test_empty_list_variable(parser):
    assert parser.parse("list = []") == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "list",
                },
                "expression": {
                    "type": "list",
                    "elements": [],
                },
            },
        ],
    }


def test_list_variable_one_element(parser):
    assert parser.parse('list = ["a"]') == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "list",
                },
                "expression": {
                    "type": "list",
                    "elements": [
                        {
                            "type": "string_literal",
                            "value": "a",
                        },
                    ],
                },
            },
        ],
    }


def test_list_variable_many_elements(parser):
    assert parser.parse('list = ["a", "b", "c"]') == {
        "type": "program",
        "statements": [
            {
                "type": "assignment",
                "identifier": {
                    "type": "identifier",
                    "name": "list",
                },
                "expression": {
                    "type": "list",
                    "elements": [
                        {
                            "type": "string_literal",
                            "value": "a",
                        },
                        {
                            "type": "string_literal",
                            "value": "b",
                        },
                        {
                            "type": "string_literal",
                            "value": "c",
                        },
                    ],
                },
            },
        ],
    }
