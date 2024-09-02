"""
Implements the Parser class.
"""

from .tokenizer import Tokenizer


class Parser:
    """
    The BLiP Parser.

    Performs syntactic analysis of the tokenized source code to produce an Abstract Syntax Tree (AST).
    The AST can then be compiled into a target language, or interpreted.
    """

    def __init__(self, source: str):
        self.__tokenizer = Tokenizer(source)

        self.__current_token = self.__tokenizer.next_token()

    def parse(self) -> dict:
        """
        Parse the source and return the AST.

        If parsing fails at any point, a SyntaxError will be raised.
        """

        return self.__parse_program()

    def __parse_program(self) -> dict:
        return {
            "type": "program",
            "input": None,
            "statements": [],
            "output": None,
        }
