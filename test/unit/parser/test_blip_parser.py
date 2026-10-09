"""Unit tests for the parser."""

import pytest

from bliplib.ir import (
    Assignment,
    BooleanLiteral,
    Concatenation,
    Decomposition,
    Directives,
    FixedDirective,
    Identifier,
    Index,
    IntegerLiteral,
    ListLiteral,
    Program,
    RangeDirective,
    Return,
    StringLiteral,
    Wildcard,
)
from bliplib.parser import Parser
from bliplib.parser.blip_parser import ParserError


@pytest.fixture
def parser():
    return Parser()


def test_invalid_syntax_raises_tokenizer_error(parser):
    with pytest.raises(ParserError):
        parser.parse("%67£$QGR _++ )(GFds")


def test_bad_expression_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse("ret")


def test_bad_identifier_statement_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse("hello hello")


def test_bad_statement_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse(",")


def test_bad_decomposition_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse("foo -> []")


def test_indexing_in_decomposition_pattern_raises_parser_error(parser):
    """A decomposition pattern element is a string literal, a capturing variable or a wildcard - never a value expression."""

    with pytest.raises(ParserError):
        parser.parse("foo -> bar[0]")

    with pytest.raises(ParserError):
        parser.parse('foo -> name "@" rest[1]')


def test_bad_index_raises_parser_error(parser):
    with pytest.raises(ParserError):
        parser.parse("foo = bar['z']")


def test_string_decomposition_square_brackets(parser: Parser):
    assert parser.parse("text -> '[' content ']'") == Program(
        statements=[
            Decomposition(
                target=Identifier(name="text"),
                pattern=[StringLiteral(value="["), Identifier(name="content"), StringLiteral(value="]")],
            )
        ]
    )


def test_string_decomposition_email(parser: Parser):
    assert parser.parse("email -> name '@' *") == Program(
        statements=[
            Decomposition(
                target=Identifier(name="email"),
                pattern=[Identifier(name="name"), StringLiteral(value="@"), Wildcard()],
            )
        ]
    )


def test_int_variable(parser: Parser):
    assert parser.parse("num = 5") == Program(statements=[Assignment(target=Identifier(name="num"), expression=IntegerLiteral(value=5))])


def test_boolean_variable(parser: Parser):
    assert parser.parse("flag = true") == Program(
        statements=[Assignment(target=Identifier(name="flag"), expression=BooleanLiteral(value=True))]
    )


def test_concatenation(parser: Parser):
    assert parser.parse('greeting = "hello" " " name') == Program(
        statements=[
            Assignment(
                target=Identifier(name="greeting"),
                expression=Concatenation(operands=[StringLiteral(value="hello"), StringLiteral(value=" "), Identifier(name="name")]),
            )
        ]
    )


def test_a_single_operand_is_not_wrapped_in_a_concatenation(parser: Parser):
    """Juxtaposition is what makes a concatenation, so one operand on its own is just that operand."""

    assert parser.parse('greeting = "hello"') == Program(
        statements=[Assignment(target=Identifier(name="greeting"), expression=StringLiteral(value="hello"))]
    )


def test_variable_index_with_integer_literal(parser: Parser):
    assert parser.parse("ret input[0]") == Program(
        statements=[Return(expression=Index(target=Identifier(name="input"), index=IntegerLiteral(value=0)))]
    )


def test_variable_index_with_integer_variable(parser: Parser):
    assert parser.parse("idx = 0; ret input[idx]") == Program(
        statements=[
            Assignment(target=Identifier(name="idx"), expression=IntegerLiteral(value=0)),
            Return(expression=Index(target=Identifier(name="input"), index=Identifier(name="idx"))),
        ]
    )


def test_empty_list_variable(parser: Parser):
    assert parser.parse("list = []") == Program(
        statements=[Assignment(target=Identifier(name="list"), expression=ListLiteral(elements=[]))]
    )


def test_list_variable_one_element(parser: Parser):
    assert parser.parse('list = ["a"]') == Program(
        statements=[Assignment(target=Identifier(name="list"), expression=ListLiteral(elements=[StringLiteral(value="a")]))]
    )


def test_list_variable_many_elements(parser: Parser):
    assert parser.parse('list = ["a", "b", "c"]') == Program(
        statements=[
            Assignment(
                target=Identifier(name="list"),
                expression=ListLiteral(elements=[StringLiteral(value="a"), StringLiteral(value="b"), StringLiteral(value="c")]),
            )
        ]
    )


def test_a_program_with_no_directives_has_none(parser: Parser):
    """`None` records that nothing was declared, which is distinct from declaring an empty set of directives."""

    assert parser.parse('ret "ok"').directives is None


def test_named_input_directive(parser: Parser):
    assert parser.parse('!in username email\nret "ok"').directives == Directives(input=FixedDirective(count=2, names=["username", "email"]))


def test_counted_input_directive_names_nothing(parser: Parser):
    assert parser.parse('!in 2\nret "ok"').directives == Directives(input=FixedDirective(count=2, names=None))


@pytest.mark.parametrize(
    ("blip_code", "expected"),
    [
        pytest.param("!out 1..3", RangeDirective(min=1, max=3), id="a closed range"),
        pytest.param("!out 2..", RangeDirective(min=2, max=None), id="open at the top"),
        pytest.param("!out ..4", RangeDirective(min=None, max=4), id="open at the bottom"),
    ],
)
def test_range_output_directive(parser: Parser, blip_code: str, expected: RangeDirective):
    assert parser.parse(f'{blip_code}\nret "ok"').directives == Directives(output=expected)


def test_a_repeated_directive_replaces_the_earlier_one(parser: Parser):
    assert parser.parse('!in 1\n!in 3\nret "ok"').directives == Directives(input=FixedDirective(count=3))


def test_the_parser_leaves_every_type_unset(parser: Parser):
    """Types are the analyser's job. The parser produces a tree with no annotations at all."""

    program = parser.parse('name = "bob"\nret name')

    assignment = program.statements[0]
    assert isinstance(assignment, Assignment)
    assert assignment.target.blip_type is None
    assert assignment.expression.blip_type is None
