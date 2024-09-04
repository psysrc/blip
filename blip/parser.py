"""
Implements the Parser class.
"""

from .tokenizer import Tokenizer


class ParserError(RuntimeError):
    pass


class Parser:
    """
    The Blip Parser.

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

    def __consume_token(self, expected_token_type: str) -> None:
        """
        Consumes the next token in the stream.
        If the token type does not match the provided token_type, an exception is raised.
        """

        if self.__current_token.type != expected_token_type:
            actual_token_type = self.__current_token.type
            raise ParserError(f"Unexpected token (expected '{expected_token_type}', got '{actual_token_type}')")

        self.__current_token = self.__tokenizer.next_token()

    def __parse_program(self) -> dict:
        statements = self.__parse_program_statements()

        return {
        "type": "program",
        "statements": statements,
    }

    def __parse_program_statements(self) -> list[dict]:
        return [
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
        ]
