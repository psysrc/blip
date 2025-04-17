from blip.parser import Parser
from pathlib import Path


def test_examples_parse_correctly():
    """
    This test function checks if the examples provided in the 'examples' directory can be parsed correctly.
    It does this by iterating through all files in the 'examples' directory, reading their contents,
    and using the Parser class to parse them.
    """

    examples_dir = Path("examples")

    for example_file in examples_dir.glob("*.blip"):
        blip_code = example_file.read_text()
        parser = Parser(blip_code)

        try:
            parser.parse()

        except Exception as e:
            assert False, f"Parsing failed for {example_file.name}: {e}"
