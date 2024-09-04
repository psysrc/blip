from blip.parser import Parser


def test_identity_program():
    parser = Parser("IN -> OUT")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "into",
                "source_identifier": {
                    "type": "identifier",
                    "name": "IN",
                },
                "expression": {
                    "type": "identifier",
                    "name": "OUT",
                }
            }
        ],
    }
