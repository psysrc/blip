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

    def __consume_token(self, *token_types: str) -> str:
        """
        Consume the next token in the stream.
        If the token type does not match one of the provided token types, a `ParserError` is raised.
        Returns the value of the consumed token.
        """

        if self.__current_token.type not in token_types:
            actual_token_type = self.__current_token.type
            raise ParserError(f"Failed to consume token (expected one of '{token_types}', got '{actual_token_type}')")

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

    def __parse_identifier(self) -> dict:
        identifier = self.__consume_token("IDENTIFIER")

        return {
            "type": "identifier",
            "name": identifier,
        }

    def __parse_expression(self) -> dict:
        match self.__current_token.type:
            case "IDENTIFIER":
                return self.__parse_identifier()
            case "LITERAL":
                return self.__parse_literal()
            case _:
                err = f"Unexpected token '{self.__current_token}' while parsing expression"
                raise ParserError(err)

    def __parse_assignment_statement(self) -> dict:
        identifier = self.__parse_identifier()

        self.__consume_token("=")

        expression = self.__parse_expression()

        self.__consume_token("EOL", "EOF")

        return {
            "type": "assignment",
            "variable": identifier,
            "value": expression,
        }

    def __parse_return_statement(self) -> dict:
        self.__consume_token("RETURN")

        expression = self.__parse_expression()

        self.__consume_token("EOL", "EOF")

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
