"""
Implements the Parser class.
"""

from .tokenizer import Tokenizer, Token


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

    def __consume_token(self, expected_token_type: str) -> str:
        """
        Consumes the next token in the stream.
        If the token type does not match the provided token_type, an exception is raised.
        Returns the value of the consumed token.
        """

        if self.__current_token.type != expected_token_type:
            actual_token_type = self.__current_token.type
            raise ParserError(f"Failed to consume token (expected '{expected_token_type}', got '{actual_token_type}')")

        token_value = self.__current_token.value

        self.__current_token = self.__tokenizer.next_token()

        return token_value

    def __parse_program(self) -> dict:
        statements = self.__parse_program_statements()

        return {
            "type": "program",
            "statements": statements,
        }

    def __parse_program_statements(self) -> list[dict]:
        match self.__current_token:
            case Token(type="IDENTIFIER"):
                statement = self.__parse_ambiguous_identifier_statement()

            case _:
                raise ParserError(f"Unexpected token {self.__current_token.type} '{self.__current_token.value}'"
                                  " while parsing statement")

        return [
            statement
        ]

    def __parse_ambiguous_identifier_statement(self) -> dict:
        identifier = self.__consume_token("IDENTIFIER")

        match self.__current_token:
            case Token(type="->"):
                self.__consume_token("->")
                expression = self.__consume_token("IDENTIFIER")

                return {
                    "type": "into",
                    "source_identifier": {
                        "type": "identifier",
                        "name": identifier,
                    },
                    "expression": {
                        "type": "identifier",
                        "name": expression,
                    }
                }

            case Token(type="<-"):
                self.__consume_token("<-")
                expression = self.__consume_token("IDENTIFIER")

                return {
                    "type": "from",
                    "target_identifier": {
                        "type": "identifier",
                        "name": identifier,
                    },
                    "expression": {
                        "type": "identifier",
                        "name": expression,
                    }
                }

            case _:
                raise ParserError(f"Unexpected token {self.__current_token.type} '{self.__current_token.value}'"
                                  " while parsing identifier statement")

