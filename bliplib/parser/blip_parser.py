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
                    statements.append(self.__parse_ambiguous_identifier_statement())

                case "RETURN":
                    statements.append(self.__parse_return_statement())

                case _:
                    err = f"Unexpected token '{self.__current_token}' while parsing program statements"
                    raise ParserError(err)

        return statements

    def __parse_ambiguous_identifier_statement(self) -> dict:
        identifier = self.__parse_identifier()

        match self.__current_token.type:
            case "=":
                return self.__parse_assignment_statement(identifier)
            case "->":
                return self.__parse_decomposition_statement(identifier)
            case _:
                err = f"Unexpected token '{self.__current_token}' while parsing ambiguous identifier statement"
                raise ParserError(err)

    def __parse_decomposition_statement(self, identifier: dict) -> dict:
        self.__consume_token("->")

        operands = []

        while self.__current_token.type not in {"EOL", "EOF"}:
            match self.__current_token.type:
                case "IDENTIFIER" | "STRING_LITERAL":
                    operands.append(self.__parse_primary_expression())
                case "*":
                    operands.append(self.__parse_decomposition_wildcard())

                case _:
                    raise ParserError(f"Unexpected token '{self.__current_token.type}' while parsing decomposition statement")

        self.__consume_token("EOL", "EOF")

        return {
            "type": "decomposition",
            "identifier": identifier,
            "pattern": operands,
        }

    def __parse_decomposition_wildcard(self) -> dict:
        self.__consume_token("*")
        return {
            "type": "decomposition_wildcard",
        }

    def __parse_identifier(self) -> dict:
        identifier = self.__consume_token("IDENTIFIER")

        return {
            "type": "identifier",
            "name": identifier,
        }

    def __parse_expression(self) -> dict:
        primary_expressions = []

        while self.__current_token.type in {"IDENTIFIER", "STRING_LITERAL", "INTEGER_LITERAL"}:
            primary_expressions.append(self.__parse_primary_expression())

        if len(primary_expressions) == 1:
            value = primary_expressions[0]
        else:
            value = {
                "type": "concatenation",
                "operands": primary_expressions,
            }

        return {
            "type": "expression",
            "value": value,
        }

    def __parse_primary_expression(self) -> dict:
        match self.__current_token.type:
            case "IDENTIFIER":
                return self.__parse_ambiguous_identifier_or_index_primary_expression()
            case "STRING_LITERAL":
                return self.__parse_string_literal()
            case "INTEGER_LITERAL":
                return self.__parse_integer_literal()
            case _:
                err = f"Unexpected token '{self.__current_token}' while parsing primary expression"
                raise ParserError(err)

    def __parse_ambiguous_identifier_or_index_primary_expression(self) -> dict:
        identifier = self.__parse_identifier()

        if self.__current_token.type == "[":
            return self.__parse_index(identifier)
        else:
            return identifier

    def __parse_index(self, identifier: dict) -> dict:
        self.__consume_token("[")

        match self.__current_token.type:
            case "INTEGER_LITERAL":
                index = self.__parse_integer_literal()
            case "IDENTIFIER":
                index = self.__parse_identifier()
            case _:
                raise ParserError(f"Unexpected token '{self.__current_token}' while parsing index")

        self.__consume_token("]")

        return {
            "type": "index",
            "identifier": identifier,
            "index": index,
        }

    def __parse_integer_literal(self) -> dict:
        literal_int = self.__consume_token("INTEGER_LITERAL")

        return {
            "type": "integer_literal",
            "value": int(literal_int),
        }

    def __parse_assignment_statement(self, identifier: dict) -> dict:
        self.__consume_token("=")

        expression = self.__parse_expression()

        self.__consume_token("EOL", "EOF")

        return {
            "type": "assignment",
            "identifier": identifier,
            "expression": expression,
        }

    def __parse_return_statement(self) -> dict:
        self.__consume_token("RETURN")

        expression = self.__parse_expression()

        self.__consume_token("EOL", "EOF")

        return {
            "type": "return",
            "expression": expression,
        }

    def __parse_string_literal(self) -> dict:
        literal_text = self.__consume_token("STRING_LITERAL")

        return {
            "type": "string_literal",
            "value": literal_text[1:-1],
        }
