"""
Defines the Interpreter class.
"""


class Interpreter:
    def __init__(self, source: str) -> None:
        if not source:
            raise RuntimeError()

    def run(self, input_string: str) -> str:
        return input_string
