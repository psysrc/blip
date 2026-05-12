"""
Implements the Parser class.
"""

from .tokenizer import Tokenizer, Token
from bliplib.errors import ParserError, TokenizerError


class Parser:
    """
    The Blip Parser.

    Performs tokenization and syntactic analysis of the source code to produce BlipIR (an Abstract Syntax Tree (AST)).
    The BlipIR can then be transpiled into a target language, or directly interpreted.
    """

    def __init__(self):
        self.__tokenizer: Tokenizer | None = None
        self.__current_token: Token | None = None

    def parse(self, source: str) -> dict:
        """
        Parse the source and return the AST.

        If parsing fails at any point, a ParserError will be raised.
        """

        try:
            self.__tokenizer = Tokenizer(source)
            self.__current_token = self.__tokenizer.next_token()

            ast = self.__parse_program()
            return ast

        except TokenizerError as err:
            raise ParserError("Tokenization failure") from err

        finally:
            self.__tokenizer = None
            self.__current_token = None

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
        directives = {}

        # Parse optional top-level directives (e.g. !in / !out)
        while self.__current_token.type in {"DIRECTIVE_IN", "DIRECTIVE_OUT"}:
            directives.update(self.__parse_directive())

        statements = self.__parse_statements()

        program = {
            "type": "program",
            "statements": statements,
        }

        if directives:
            program["directives"] = directives

        return program

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
                    err = f"Unexpected token {self.__current_token} while parsing program statements"
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
                err = f"Unexpected token {self.__current_token} while parsing ambiguous identifier statement"
                raise ParserError(err)

    def __parse_decomposition_statement(self, identifier: dict) -> dict:
        self.__consume_token("->")

        operands = []

        while self.__current_token.type not in {"EOL", "EOF"}:
            match self.__current_token.type:
                case "IDENTIFIER":
                    operands.append(self.__parse_ambiguous_identifier_or_index_primary_expression())
                case "STRING_LITERAL":
                    operands.append(self.__parse_string_literal())
                case "*":
                    operands.append(self.__parse_decomposition_wildcard())

                case _:
                    raise ParserError(f"Unexpected token {self.__current_token.type} while parsing decomposition statement")

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
        match self.__current_token.type:
            case "INTEGER_LITERAL":
                value = self.__parse_integer_literal()
            case "BOOLEAN_LITERAL":
                value = self.__parse_boolean_literal()
            case "IDENTIFIER" | "STRING_LITERAL":
                value = self.__parse_ambiguous_possible_concatenation()
            case "[":
                value = self.__parse_list()
            case _:
                err = f"Unexpected token {self.__current_token} while parsing primary expression"
                raise ParserError(err)

        return {
            "type": "expression",
            "value": value,
        }

    def __parse_list(self) -> dict:
        self.__consume_token("[")

        elements = []
        while self.__current_token.type != "]":
            elements.append(self.__parse_expression())
            if self.__current_token.type == ",":
                self.__consume_token(",")

        self.__consume_token("]")

        return {
            "type": "list",
            "elements": elements,
        }

    def __parse_ambiguous_possible_concatenation(self) -> dict:
        primary_expressions = []

        while self.__current_token.type in {"IDENTIFIER", "STRING_LITERAL"}:
            match self.__current_token.type:
                case "IDENTIFIER":
                    primary_expressions.append(self.__parse_ambiguous_identifier_or_index_primary_expression())
                case "STRING_LITERAL":
                    primary_expressions.append(self.__parse_string_literal())
                case _:
                    err = f"Unexpected token {self.__current_token} while parsing possible concatenation"
                    raise ParserError(err)

        if len(primary_expressions) == 1:
            return primary_expressions[0]

        return {
            "type": "concatenation",
            "operands": primary_expressions,
        }

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
                raise ParserError(f"Unexpected token {self.__current_token} while parsing index")

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

    def __parse_directive(self) -> dict:
        match self.__current_token.type:
            case "DIRECTIVE_IN":
                self.__consume_token("DIRECTIVE_IN")
                payload = self.__parse_directive_body()
                self.__consume_token("EOL", "EOF")
                return {"input": payload}

            case "DIRECTIVE_OUT":
                self.__consume_token("DIRECTIVE_OUT")
                payload = self.__parse_directive_body()
                self.__consume_token("EOL", "EOF")
                return {"output": payload}

            case _:
                raise ParserError(f"Unexpected directive token {self.__current_token}")

    def __parse_directive_body(self) -> dict:
        # Possible forms:
        # 1) INTEGER_LITERAL                      => fixed count
        # 2) INTEGER_LITERAL '..' INTEGER_LITERAL => range
        # 3) INTEGER_LITERAL '..'                 => range min..
        # 4) '..' INTEGER_LITERAL                 => range ..max
        # 5) IDENTIFIER IDENTIFIER ...            => named fixed

        if self.__current_token.type == "INTEGER_LITERAL":
            lower = int(self.__consume_token("INTEGER_LITERAL"))

            if self.__current_token.type == "..":
                self.__consume_token("..")

                if self.__current_token.type == "INTEGER_LITERAL":
                    upper = int(self.__consume_token("INTEGER_LITERAL"))
                else:
                    upper = None

                return {"type": "range", "min": lower, "max": upper}

            return {"type": "fixed", "value": lower}

        if self.__current_token.type == "..":
            self.__consume_token("..")

            if self.__current_token.type == "INTEGER_LITERAL":
                upper = int(self.__consume_token("INTEGER_LITERAL"))
                return {"type": "range", "min": None, "max": upper}

            raise ParserError("Malformed directive range")

        if self.__current_token.type == "IDENTIFIER":
            names = []
            while self.__current_token.type == "IDENTIFIER":
                names.append(self.__consume_token("IDENTIFIER"))

            return {"type": "fixed", "value": len(names), "names": names}

        raise ParserError(f"Unexpected token {self.__current_token} in directive body")

    def __parse_string_literal(self) -> dict:
        literal_text = self.__consume_token("STRING_LITERAL")

        return {
            "type": "string_literal",
            "value": literal_text[1:-1],
        }

    def __parse_boolean_literal(self) -> dict:
        literal_text = self.__consume_token("BOOLEAN_LITERAL")

        return {
            "type": "boolean_literal",
            "value": True if literal_text == "true" else False,
        }
