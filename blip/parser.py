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

        If parsing fails at any point, a ParserError will be raised.
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
        statements = self.__parse_statements()

        return {
            "type": "program",
            "statements": statements,
        }

    def __parse_statements(self) -> list:
        statements = []

        while self.__current_token.type != "EOF":
            match self.__current_token.type:
                case "EOL":
                    self.__consume_token("EOL")

                case "IDENTIFIER":
                    statements.append(self.__parse_assignment_statement())

                case "RETURN":
                    statements.append(self.__parse_return_statement())

                case _:
                    err = f"Unexpected token '{self.__current_token}' while parsing program statements"
                    raise ParserError(err)

        return statements

    def __parse_assignment_statement(self):
        identifier = self.__consume_token("IDENTIFIER")

        if self.__current_token.type != "=":
            raise ParserError(f"Unexpected token '{self.__current_token}' while parsing assignment (expected '=')")

        self.__consume_token("=")

        value = self.__parse_literal()

        return {
            "type": "assignment",
            "variable": {
                "type": "identifier",
                "name": identifier,
            },
            "value": value,
        }

    def __parse_return_statement(self) -> dict:
        self.__consume_token("RETURN")
        expression = self.__parse_literal()

        if self.__current_token.type == "EOF":
            self.__consume_token("EOF")
        else:
            self.__consume_token("EOL")

        return {
            "type": "return",
            "expression": expression,
        }

    def __parse_literal(self) -> dict:
        literal_text = self.__consume_token("LITERAL")

        return {
            "type": "literal",
            "value": literal_text[1:-1],
        }
