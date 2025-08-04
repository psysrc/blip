from bliplib.parser import Parser


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
