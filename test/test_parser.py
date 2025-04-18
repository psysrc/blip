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
