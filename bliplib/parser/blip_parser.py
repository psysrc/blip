"""Implements the Parser class."""

from bliplib.errors import ParserError, TokenizerError
from bliplib.ir import (
    Assignment,
    BooleanLiteral,
    Concatenation,
    Decomposition,
    DecompPattern,
    Directive,
    Directives,
    FixedDirective,
    Identifier,
    Index,
    IntegerLiteral,
    ListLiteral,
    Program,
    RangeDirective,
    Return,
    Statement,
    StringLiteral,
    Value,
    Wildcard,
)

from .tokenizer import Token, Tokenizer


class Parser:
    """
    The Blip Parser.

    Performs tokenization and evaluates the syntax of the source code to produce Blip IR (an Abstract Syntax Tree (AST)).
    The BlipIR can then be analysed, and afterwards transpiled into a target language or directly interpreted.
    """

    def __init__(self):
        self.__tokenizer: Tokenizer | None = None
        self.__current_token: Token | None = None

    def parse(self, source: str) -> Program:
        """
        Parse the source and return the Blip IR AST.
        If parsing fails at any point, a `ParserError` will be raised.

        Note the resulting program is un-analysed and all `blip_type` fields will be `None`.
        """

        try:
            self.__tokenizer = Tokenizer(source)
            self.__current_token = self.__tokenizer.next_token()

            program = self.__parse_program()
            return program

        except TokenizerError as err:
            raise ParserError("Tokenization failure") from err

        finally:
            self.__tokenizer = None
            self.__current_token = None

    @property
    def __stream(self) -> Tokenizer:
        """
        The token stream being parsed.
        Only exists during a `parse()` call, so accessing it outside of one raises a `ParserError`.
        """

        if self.__tokenizer is None:
            raise ParserError("No source is currently being parsed")

        return self.__tokenizer

    @property
    def __token(self) -> Token:
        """
        The token at the head of the stream.
        Only exists during a `parse()` call, so accessing it outside of one raises a `ParserError`.
        """

        if self.__current_token is None:
            raise ParserError("No source is currently being parsed")

        return self.__current_token

    def __consume_token(self, *token_types: str) -> str:
        """
        Consume the next token in the stream.
        If the token type does not match one of the provided token types, a `ParserError` is raised.
        Returns the value of the consumed token.
        """

        if self.__token.type not in token_types:
            actual_token_type = self.__token.type
            raise ParserError(f"Failed to consume token (expected one of '{token_types}', got '{actual_token_type}')")

        token_value = self.__token.value

        self.__current_token = self.__stream.next_token()

        return token_value

    def __parse_program(self) -> Program:
        declared_input: Directive | None = None
        declared_output: Directive | None = None

        # Parse optional top-level directives (e.g. !in / !out). A repeated directive replaces the earlier one.
        while self.__token.type in {"DIRECTIVE_IN", "DIRECTIVE_OUT"}:
            if self.__token.type == "DIRECTIVE_IN":
                self.__consume_token("DIRECTIVE_IN")
                declared_input = self.__parse_directive_body()
            else:
                self.__consume_token("DIRECTIVE_OUT")
                declared_output = self.__parse_directive_body()

            self.__consume_token("EOL", "EOF")

        statements = self.__parse_statements()

        declared_any = declared_input is not None or declared_output is not None
        directives = Directives(input=declared_input, output=declared_output) if declared_any else None

        return Program(statements=statements, directives=directives)

    def __parse_statements(self) -> list[Statement]:
        statements: list[Statement] = []

        while self.__token.type != "EOF":
            match self.__token.type:
                case "EOL":
                    self.__consume_token("EOL")

                case "IDENTIFIER":
                    statements.append(self.__parse_ambiguous_identifier_statement())

                case "RETURN":
                    statements.append(self.__parse_return_statement())

                case _:
                    err = f"Unexpected token {self.__token} while parsing program statements"
                    raise ParserError(err)

        return statements

    def __parse_ambiguous_identifier_statement(self) -> Statement:
        identifier = self.__parse_identifier()

        match self.__token.type:
            case "=":
                return self.__parse_assignment_statement(identifier)
            case "->":
                return self.__parse_decomposition_statement(identifier)
            case _:
                err = f"Unexpected token {self.__token} while parsing ambiguous identifier statement"
                raise ParserError(err)

    def __parse_decomposition_statement(self, identifier: Identifier) -> Decomposition:
        self.__consume_token("->")

        pattern: DecompPattern = []

        while self.__token.type not in {"EOL", "EOF"}:
            match self.__token.type:
                case "IDENTIFIER":
                    pattern.append(self.__parse_identifier())
                case "STRING_LITERAL":
                    pattern.append(self.__parse_string_literal())
                case "*":
                    pattern.append(self.__parse_decomposition_wildcard())

                case _:
                    raise ParserError(f"Unexpected token {self.__token.type} while parsing decomposition statement")

        self.__consume_token("EOL", "EOF")

        return Decomposition(target=identifier, pattern=pattern)

    def __parse_decomposition_wildcard(self) -> Wildcard:
        self.__consume_token("*")
        return Wildcard()

    def __parse_identifier(self) -> Identifier:
        identifier = self.__consume_token("IDENTIFIER")

        return Identifier(name=identifier)

    def __parse_expression(self) -> Value:
        match self.__token.type:
            case "INTEGER_LITERAL":
                return self.__parse_integer_literal()
            case "BOOLEAN_LITERAL":
                return self.__parse_boolean_literal()
            case "IDENTIFIER" | "STRING_LITERAL":
                return self.__parse_ambiguous_possible_concatenation()
            case "[":
                return self.__parse_list()
            case _:
                err = f"Unexpected token {self.__token} while parsing primary expression"
                raise ParserError(err)

    def __parse_list(self) -> ListLiteral:
        self.__consume_token("[")

        elements: list[Value] = []
        while self.__token.type != "]":
            elements.append(self.__parse_expression())
            if self.__token.type == ",":
                self.__consume_token(",")

        self.__consume_token("]")

        return ListLiteral(elements=elements)

    def __parse_ambiguous_possible_concatenation(self) -> Value:
        primary_expressions: list[Value] = []

        while self.__token.type in {"IDENTIFIER", "STRING_LITERAL"}:
            match self.__token.type:
                case "IDENTIFIER":
                    primary_expressions.append(self.__parse_ambiguous_identifier_or_index_primary_expression())
                case "STRING_LITERAL":
                    primary_expressions.append(self.__parse_string_literal())
                case _:
                    err = f"Unexpected token {self.__token} while parsing possible concatenation"
                    raise ParserError(err)

        if len(primary_expressions) == 1:
            return primary_expressions[0]

        return Concatenation(operands=primary_expressions)

    def __parse_ambiguous_identifier_or_index_primary_expression(self) -> Identifier | Index:
        identifier = self.__parse_identifier()

        if self.__token.type == "[":
            return self.__parse_index(identifier)
        else:
            return identifier

    def __parse_index(self, identifier: Identifier) -> Index:
        self.__consume_token("[")

        index: Value

        match self.__token.type:
            case "INTEGER_LITERAL":
                index = self.__parse_integer_literal()
            case "IDENTIFIER":
                index = self.__parse_identifier()
            case _:
                raise ParserError(f"Unexpected token {self.__token} while parsing index")

        self.__consume_token("]")

        return Index(target=identifier, index=index)

    def __parse_integer_literal(self) -> IntegerLiteral:
        literal_int = self.__consume_token("INTEGER_LITERAL")

        return IntegerLiteral(value=int(literal_int))

    def __parse_assignment_statement(self, identifier: Identifier) -> Assignment:
        self.__consume_token("=")

        expression = self.__parse_expression()

        self.__consume_token("EOL", "EOF")

        return Assignment(target=identifier, expression=expression)

    def __parse_return_statement(self) -> Return:
        self.__consume_token("RETURN")

        expression = self.__parse_expression()

        self.__consume_token("EOL", "EOF")

        return Return(expression=expression)

    def __parse_directive_body(self) -> Directive:
        # Possible forms:
        # 1) INTEGER_LITERAL                      => fixed count
        # 2) INTEGER_LITERAL '..' INTEGER_LITERAL => range
        # 3) INTEGER_LITERAL '..'                 => range min..
        # 4) '..' INTEGER_LITERAL                 => range ..max
        # 5) IDENTIFIER IDENTIFIER ...            => fixed named

        if self.__token.type == "INTEGER_LITERAL":
            lower = int(self.__consume_token("INTEGER_LITERAL"))

            if self.__token.type == "..":
                self.__consume_token("..")

                if self.__token.type == "INTEGER_LITERAL":
                    upper = int(self.__consume_token("INTEGER_LITERAL"))
                else:
                    upper = None

                return RangeDirective(min=lower, max=upper)

            return FixedDirective(count=lower)

        if self.__token.type == "..":
            self.__consume_token("..")

            if self.__token.type == "INTEGER_LITERAL":
                upper = int(self.__consume_token("INTEGER_LITERAL"))
                return RangeDirective(min=None, max=upper)

            raise ParserError("Malformed directive range")

        if self.__token.type == "IDENTIFIER":
            names = []
            while self.__token.type == "IDENTIFIER":
                names.append(self.__consume_token("IDENTIFIER"))

            return FixedDirective(count=len(names), names=names)

        raise ParserError(f"Unexpected token {self.__token} in directive body")

    def __parse_string_literal(self) -> StringLiteral:
        literal_text = self.__consume_token("STRING_LITERAL")

        return StringLiteral(value=literal_text[1:-1])

    def __parse_boolean_literal(self) -> BooleanLiteral:
        literal_text = self.__consume_token("BOOLEAN_LITERAL")

        return BooleanLiteral(value=literal_text == "true")
