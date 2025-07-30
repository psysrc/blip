"""
Implements the Interpreter class.
"""


class Interpreter:
    def __init__(self, blip_ir: dict) -> None:
        self.__code = blip_ir

    def run(self, input_strings: list[str]) -> list[str]:
        match self.__code:
            case {
                "type": "program",
                "statements": [
                    {
                        "type": "return",
                        "expression": {
                            "type": "literal",
                            "value": the_string,
                        },
                    }
                ],
            }:
                return [the_string]

            case _:
                raise RuntimeError()
