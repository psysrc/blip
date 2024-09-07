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

def test_alternative_identity_program():
    parser = Parser("OUT <- IN")

    assert parser.parse() == {
        "type": "program",
        "statements": [
            {
                "type": "from",
                "target_identifier": {
                    "type": "identifier",
                    "name": "OUT",
                },
                "expression": {
                    "type": "identifier",
                    "name": "IN",
                }
            }
        ],
    }
