from blip.parser import Parser


def test_dummy():
    parser = Parser("")

    assert parser.parse() == {
        "type": "program",
        "input": {
            "type": "input",
        },
        "output": {
            "type": "output",
        },
        "statements": [],
    }
