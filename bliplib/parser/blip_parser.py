"""Implements the Parser class."""

from bliplib.errors import ParserError, TokenizerError
from bliplib.ir import (
    Assignment,
    BooleanLiteral,
    Concatenation,
    Condition,
    Decomposition,
    DecompPattern,
    DecompTest,
    Directive,
    Directives,
    FixedDirective,
    Identifier,
    If,
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
from bliplib.source import Span

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
        self.__consumed_span: Span | None = None

    def parse(self, source: str) -> Program:
        """
        Parse the source and return the Blip IR AST.
        If parsing fails at any point, a `ParserError` will be raised.

        Note the resulting program is un-analysed and all `blip_type` fields will be `None`.
        """

        try:
            self.__tokenizer = Tokenizer(source)
            self.__current_token = self.__tokenizer.next_token()
            self.__consumed_span = None

            program = self.__parse_program()
            return program

        except TokenizerError as err:
            raise ParserError(str(err), err.location) from err

        finally:
            self.__tokenizer = None
            self.__current_token = None
            self.__consumed_span = None

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

    @property
    def __span(self) -> Span:
        """
        The span of the token at the head of the stream.

        Read this *before* consuming to get a leaf node's own span, or before parsing a whole construct to get the start of a
        composite one.
        """

        return self.__token.location

    def __span_from(self, start: Span) -> Span:
        """
        The span reaching from `start` through the token most recently consumed.

        This is how a node built from several tokens gets its span: capture `__span` before parsing it and call this
        afterwards, and the result covers exactly the tokens the node was made of - brackets and keywords included. Reading
        the spans back off the child nodes would work too, but theirs are `Span | None`, and this keeps the arithmetic in the
        one place that knows every span is real.
        """

        if self.__consumed_span is None:
            # Nothing has been consumed, so `start` is all there is. Unreachable while building a node, which by definition
            # has consumed at least one token
            return start

        return start.covering(self.__consumed_span)

    def __consume_token(self, *token_types: str) -> str:
        """
        Consume the next token in the stream.
        If the token type does not match one of the provided token types, a `ParserError` is raised.
        Returns the value of the consumed token.
        """

        if self.__token.type not in token_types:
            actual_token_type = self.__token.type
            raise ParserError(f"Failed to consume token (expected one of '{token_types}', got '{actual_token_type}')", self.__span)

        token_value = self.__token.value
        self.__consumed_span = self.__token.location

        self.__current_token = self.__stream.next_token()

        return token_value

    def __parse_program(self) -> Program:
        declared_input: Directive | None = None
        declared_output: Directive | None = None

        # Parse optional top-level directives (e.g. !in / !out).
        # TODO: Current a repeated directive replaces the earlier one. In future, repeated directives should be an error.
        while self.__token.type in {"EOL", "DIRECTIVE_IN", "DIRECTIVE_OUT"}:
            if self.__token.type == "EOL":
                self.__consume_token("EOL")
                continue

            start = self.__span

            if self.__token.type == "DIRECTIVE_IN":
                self.__consume_token("DIRECTIVE_IN")
                declared_input = self.__parse_directive_body(start)
            else:
                self.__consume_token("DIRECTIVE_OUT")
                declared_output = self.__parse_directive_body(start)

            self.__consume_token("EOL", "EOF")

        statements = self.__parse_statements()

        declared_any = declared_input is not None or declared_output is not None
        directives = Directives(input=declared_input, output=declared_output) if declared_any else None

        return Program(statements=statements, directives=directives)

    def __parse_statements(self, *terminators: str) -> list[Statement]:
        """
        Parse statements until a terminator is at the head of the stream, leaving the terminator unconsumed.

        `EOF` always stops it, on top of whatever is passed. A block that never closes therefore stops at the end of the
        source instead of running off it, and leaves `__parse_block` to report the brace it was waiting for.
        """

        statements: list[Statement] = []

        while self.__token.type != "EOF" and self.__token.type not in terminators:
            match self.__token.type:
                case "EOL":
                    self.__consume_token("EOL")

                case "IDENTIFIER":
                    statements.append(self.__parse_ambiguous_identifier_statement())

                case "RETURN":
                    statements.append(self.__parse_return_statement())

                case "IF":
                    statements.append(self.__parse_if_statement())

                case _:
                    err = f"Unexpected token {self.__token} while parsing program statements"
                    raise ParserError(err, self.__span)

        return statements

    def __consume_statement_terminator(self) -> None:
        """
        Consume whatever ends a statement.

        A newline or the end of the source ends one, and is consumed. A closing brace ends one too - the last statement in a
        block needs no newline after it - but that brace belongs to the block, so it is left for `__parse_block` to take.
        """

        if self.__token.type == "}":
            return

        self.__consume_token("EOL", "EOF")

    def __parse_block(self) -> list[Statement]:
        """Parse a braced block, consuming both braces."""

        self.__consume_token("{")
        statements = self.__parse_statements("}")
        self.__consume_token("}")

        return statements

    def __parse_if_statement(self) -> If:
        """
        Parse an `if` and its optional `else`.

        Unlike every other statement, this consumes no terminator after the closing brace. A block already ends
        unambiguously, and demanding a newline after it would reject `} else {`; the statement loop absorbs the `EOL` that
        usually follows.
        """

        start = self.__span
        self.__consume_token("IF")

        condition = self.__parse_condition()
        body = self.__parse_block()

        otherwise: list[Statement] | None = None

        if self.__token.type == "ELSE":
            self.__consume_token("ELSE")
            otherwise = self.__parse_block()

        return If(condition=condition, body=body, otherwise=otherwise, location=self.__span_from(start))

    def __parse_condition(self) -> Condition:
        """Parse an `if` condition."""

        start = self.__span
        expression = self.__parse_expression()

        if self.__token.type != "->":
            return expression

        if not isinstance(expression, Identifier):
            raise ParserError("Only a variable can be decomposed", expression.location)

        self.__consume_token("->")
        pattern = self.__parse_decomposition_pattern("{")

        # The condition ends at its last pattern element, not at the brace that opens the block
        return DecompTest(target=expression, pattern=pattern, location=self.__span_from(start))

    def __parse_ambiguous_identifier_statement(self) -> Statement:
        start = self.__span
        identifier = self.__parse_identifier()

        match self.__token.type:
            case "=":
                return self.__parse_assignment_statement(identifier, start)
            case "->":
                return self.__parse_decomposition_statement(identifier, start)
            case _:
                err = f"Unexpected token {self.__token} while parsing ambiguous identifier statement"
                raise ParserError(err, self.__span)

    def __parse_decomposition_statement(self, identifier: Identifier, start: Span) -> Decomposition:
        self.__consume_token("->")

        pattern = self.__parse_decomposition_pattern()

        terminator = self.__span_from(start)
        self.__consume_statement_terminator()

        # The statement ends at its last pattern element, not at the newline that terminates it
        return Decomposition(target=identifier, pattern=pattern, location=terminator)

    def __parse_decomposition_pattern(self, *terminators: str) -> DecompPattern:
        """
        Parse the elements of a decomposition pattern, stopping before a terminator without consuming it.

        `EOL` and `EOF` always stop it, on top of whatever is passed. For a statement that is the end of it; for a condition
        it means the `{` never arrived, and `__parse_block` is the one that says so.
        """

        pattern: DecompPattern = []

        while self.__token.type not in {"EOL", "EOF", "}", *terminators}:
            match self.__token.type:
                case "IDENTIFIER":
                    pattern.append(self.__parse_identifier())
                case "STRING_LITERAL":
                    pattern.append(self.__parse_string_literal())
                case "*":
                    pattern.append(self.__parse_decomposition_wildcard())

                case _:
                    raise ParserError(f"Unexpected token {self.__token.type} while parsing decomposition pattern", self.__span)

        return pattern

    def __parse_decomposition_wildcard(self) -> Wildcard:
        span = self.__span
        self.__consume_token("*")

        return Wildcard(location=span)

    def __parse_identifier(self) -> Identifier:
        span = self.__span
        identifier = self.__consume_token("IDENTIFIER")

        return Identifier(name=identifier, location=span)

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
                raise ParserError(err, self.__span)

    def __parse_list(self) -> ListLiteral:
        start = self.__span
        self.__consume_token("[")

        elements: list[Value] = []
        while self.__token.type != "]":
            elements.append(self.__parse_expression())
            if self.__token.type == ",":
                self.__consume_token(",")

        self.__consume_token("]")

        # From the opening bracket to the closing one, so that an empty `[]` still has something to point at
        return ListLiteral(elements=elements, location=self.__span_from(start))

    def __parse_ambiguous_possible_concatenation(self) -> Value:
        start = self.__span
        primary_expressions: list[Value] = []

        while self.__token.type in {"IDENTIFIER", "STRING_LITERAL"}:
            match self.__token.type:
                case "IDENTIFIER":
                    primary_expressions.append(self.__parse_ambiguous_identifier_or_index_primary_expression())
                case "STRING_LITERAL":
                    primary_expressions.append(self.__parse_string_literal())
                case _:
                    err = f"Unexpected token {self.__token} while parsing possible concatenation"
                    raise ParserError(err, self.__span)

        if len(primary_expressions) == 1:
            return primary_expressions[0]

        return Concatenation(operands=primary_expressions, location=self.__span_from(start))

    def __parse_ambiguous_identifier_or_index_primary_expression(self) -> Identifier | Index:
        start = self.__span
        identifier = self.__parse_identifier()

        if self.__token.type == "[":
            return self.__parse_index(identifier, start)
        else:
            return identifier

    def __parse_index(self, identifier: Identifier, start: Span) -> Index:
        self.__consume_token("[")

        index: Value

        match self.__token.type:
            case "INTEGER_LITERAL":
                index = self.__parse_integer_literal()
            case "IDENTIFIER":
                index = self.__parse_identifier()
            case _:
                raise ParserError(f"Unexpected token {self.__token} while parsing index", self.__span)

        self.__consume_token("]")

        return Index(target=identifier, index=index, location=self.__span_from(start))

    def __parse_integer_literal(self) -> IntegerLiteral:
        span = self.__span
        literal_int = self.__consume_token("INTEGER_LITERAL")

        return IntegerLiteral(value=int(literal_int), location=span)

    def __parse_assignment_statement(self, identifier: Identifier, start: Span) -> Assignment:
        self.__consume_token("=")

        expression = self.__parse_expression()

        span = self.__span_from(start)
        self.__consume_statement_terminator()

        return Assignment(target=identifier, expression=expression, location=span)

    def __parse_return_statement(self) -> Return:
        start = self.__span
        self.__consume_token("RETURN")

        expression = self.__parse_expression()

        span = self.__span_from(start)
        self.__consume_statement_terminator()

        return Return(expression=expression, location=span)

    def __parse_directive_body(self, start: Span) -> Directive:
        """`start` is the span of the `!in` or `!out` keyword, so that a directive's span covers the whole declaration."""

        # Possible forms:
        # 1) INTEGER_LITERAL                      => fixed count
        # 2) INTEGER_LITERAL '..' INTEGER_LITERAL => range
        # 3) INTEGER_LITERAL '..'                 => range min..
        # 4) '..' INTEGER_LITERAL                 => range ..max
        # 5) '..'                                 => range bounded at neither end
        # 6) IDENTIFIER IDENTIFIER ...            => fixed named

        if self.__token.type == "INTEGER_LITERAL":
            lower = int(self.__consume_token("INTEGER_LITERAL"))

            if self.__token.type == "..":
                self.__consume_token("..")

                if self.__token.type == "INTEGER_LITERAL":
                    upper = int(self.__consume_token("INTEGER_LITERAL"))
                else:
                    upper = None

                return RangeDirective(min=lower, max=upper, location=self.__span_from(start))

            return FixedDirective(count=lower, location=self.__span_from(start))

        if self.__token.type == "..":
            self.__consume_token("..")

            if self.__token.type == "INTEGER_LITERAL":
                upper = int(self.__consume_token("INTEGER_LITERAL"))

                return RangeDirective(min=None, max=upper, location=self.__span_from(start))

            return RangeDirective(min=None, max=None, location=self.__span_from(start))

        if self.__token.type == "IDENTIFIER":
            names = []
            while self.__token.type == "IDENTIFIER":
                names.append(self.__consume_token("IDENTIFIER"))

            return FixedDirective(count=len(names), names=names, location=self.__span_from(start))

        raise ParserError(f"Unexpected token {self.__token} in directive body", self.__span)

    def __parse_string_literal(self) -> StringLiteral:
        span = self.__span
        literal_text = self.__consume_token("STRING_LITERAL")

        # The span covers the quotes, which the value does not: a caret under a literal should include its delimiters
        return StringLiteral(value=literal_text[1:-1], location=span)

    def __parse_boolean_literal(self) -> BooleanLiteral:
        span = self.__span
        literal_text = self.__consume_token("BOOLEAN_LITERAL")

        return BooleanLiteral(value=literal_text == "true", location=span)
