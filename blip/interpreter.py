"""
Defines the Interpreter class.
"""


class Interpreter:
    def __init__(self, source: str) -> None:
        if not source:
            raise RuntimeError()
