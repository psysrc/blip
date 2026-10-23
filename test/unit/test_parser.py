"""Unit tests for the parser."""

from collections.abc import Generator

import pytest

from bliplib.ir import (
    Assignment,
    BooleanLiteral,
    Concatenation,
    Decomposition,
    DecompTest,
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
    StringLiteral,
    Wildcard,
)
from bliplib.ir.nodes import Located
from bliplib.parser import Parser
from bliplib.parser.blip_parser import ParserError


@pytest.fixture
def parser():
    return Parser()


def __get_located_nodes(node: object, depth: int = 0) -> Generator[tuple[int, Located], None, None]:
    """Every `Located` node in a tree, paired with its depth, parents before children."""

    if isinstance(node, Located):
        yield depth, node
        depth += 1

    for plural in ("statements", "operands", "elements", "pattern", "body", "otherwise"):
        for child in getattr(node, plural, None) or []:
            yield from __get_located_nodes(child, depth)

    for singular in ("target", "expression", "index", "input", "output", "directives", "condition"):
        child = getattr(node, singular, None)
        if child is not None:
            yield from __get_located_nodes(child, depth)


def test_invalid_syntax_raises_tokenizer_error(parser: Parser):
    with pytest.raises(ParserError):
        parser.parse("%67£$QGR _++ )(GFds")


def test_bad_expression_raises_parser_error(parser: Parser):
    with pytest.raises(ParserError):
        parser.parse("ret")


def test_bad_identifier_statement_raises_parser_error(parser: Parser):
    with pytest.raises(ParserError):
        parser.parse("hello hello")


def test_bad_statement_raises_parser_error(parser: Parser):
    with pytest.raises(ParserError):
        parser.parse(",")


def test_bad_decomposition_raises_parser_error(parser: Parser):
    with pytest.raises(ParserError):
        parser.parse("foo -> []")


def test_indexing_in_decomposition_pattern_raises_parser_error(parser: Parser):
    """A decomposition pattern element is a string literal, a capturing variable or a wildcard - never a value expression."""

    with pytest.raises(ParserError):
        parser.parse("foo -> bar[0]")

    with pytest.raises(ParserError):
        parser.parse('foo -> name "@" rest[1]')


def test_bad_index_raises_parser_error(parser: Parser):
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


@pytest.mark.parametrize("name", ["retry", "return", "true_colour", "falsehood", "inputs"])
def test_an_identifier_may_start_with_a_keyword(parser: Parser, name: str):
    """Every keyword is matched on a word boundary, so a name that merely begins with one is an ordinary identifier."""

    assert parser.parse(f'{name} = "x"') == Program(
        statements=[Assignment(target=Identifier(name=name), expression=StringLiteral(value="x"))]
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
    assert parser.parse('!in username email; ret "ok"').directives == Directives(input=FixedDirective(count=2, names=["username", "email"]))


def test_counted_input_directive_names_nothing(parser: Parser):
    assert parser.parse('!in 2; ret "ok"').directives == Directives(input=FixedDirective(count=2, names=None))


@pytest.mark.parametrize(
    ("directive", "expected"),
    [
        pytest.param("!in 1..3", RangeDirective(min=1, max=3), id="a closed range"),
        pytest.param("!in 2..", RangeDirective(min=2, max=None), id="open at the end"),
        pytest.param("!in ..4", RangeDirective(min=None, max=4), id="open at the front"),
        pytest.param("!in ..", RangeDirective(min=None, max=None), id="open at both ends"),
    ],
)
def test_range_input_directive(parser: Parser, directive: str, expected: RangeDirective):
    assert parser.parse(f'{directive}; ret "ok"').directives == Directives(input=expected)


@pytest.mark.parametrize(
    ("directive", "expected"),
    [
        pytest.param("!out 1..3", RangeDirective(min=1, max=3), id="a closed range"),
        pytest.param("!out 2..", RangeDirective(min=2, max=None), id="open at the end"),
        pytest.param("!out ..4", RangeDirective(min=None, max=4), id="open at the front"),
        pytest.param("!out ..", RangeDirective(min=None, max=None), id="open at both ends"),
    ],
)
def test_range_output_directive(parser: Parser, directive: str, expected: RangeDirective):
    assert parser.parse(f'{directive}; ret "ok"').directives == Directives(output=expected)


def test_an_input_directive_bounded_at_neither_end_is_still_a_directive(parser: Parser):
    assert parser.parse('!in ..; ret "ok"').directives == Directives(input=RangeDirective(min=None, max=None))
    assert parser.parse('ret "ok"').directives is None


def test_an_output_directive_bounded_at_neither_end_is_still_a_directive(parser: Parser):
    assert parser.parse('!out ..; ret "ok"').directives == Directives(output=RangeDirective(min=None, max=None))
    assert parser.parse('ret "ok"').directives is None


_IN_2 = Directives(input=FixedDirective(count=2))
_IN_2_OUT_1 = Directives(input=FixedDirective(count=2), output=FixedDirective(count=1))


@pytest.mark.parametrize(
    ("blip_code", "expected"),
    [
        pytest.param('// header\n!in 2; ret "ok"', _IN_2, id="a comment line before the directive"),
        pytest.param('\n!in 2; ret "ok"', _IN_2, id="a blank line before the directive"),
        pytest.param('// one\n// two\n\n!in 2; ret "ok"', _IN_2, id="a licence header block before the directive"),
        pytest.param('!in 2  // trailing\nret "ok"', _IN_2, id="a comment trailing the directive"),
        pytest.param('!in 2\n// why\n!out 1\nret "ok"', _IN_2_OUT_1, id="a comment line between two directives"),
        pytest.param('!in 2\n\n!out 1\nret "ok"', _IN_2_OUT_1, id="a blank line between two directives"),
    ],
)
def test_blank_and_comment_lines_do_not_end_the_directive_section(parser: Parser, blip_code: str, expected: Directives):
    assert parser.parse(blip_code).directives == expected


def test_directives_only_valid_at_beginning_of_program(parser: Parser):
    with pytest.raises(ParserError):
        parser.parse('ret "ok"; !in 1')


def test_a_repeated_directive_replaces_the_earlier_one(parser: Parser):
    assert parser.parse('!in 1; !in 3; ret "ok"').directives == Directives(input=FixedDirective(count=3))


@pytest.mark.parametrize(
    "blip_code",
    [
        pytest.param('ret "Hello World!"', id="a one-line program"),
        pytest.param('name = "bob"; ret name', id="an assignment and a return"),
        pytest.param('email -> username "@" *; ret username', id="a decomposition with a wildcard"),
        pytest.param("empty = []; ret empty", id="an empty list"),
        pytest.param("!in raw; !out 1; ; ret raw", id="directives, blank lines and a comment-free header"),
        pytest.param('// header; ; ret input[0] " and " input[1]', id="indexing and concatenation after a comment"),
        pytest.param("a = 1; b = true; ret 'x'", id="semicolon-separated statements"),
        pytest.param('flag = true; if flag { ret "yes" } ret "no"', id="an if with a boolean condition"),
        pytest.param('e = "a@b"; if e -> user "@" * { ret user } else { ret "none" }', id="a conditional decomposition"),
    ],
)
def test_every_node_span_slices_back_to_the_source_it_came_from(parser: Parser, blip_code: str):
    for _, node in __get_located_nodes(parser.parse(blip_code)):
        assert node.location is not None, f"{type(node).__name__} was parsed without a span"

        sliced = blip_code[node.location.offset : node.location.end]
        assert sliced.strip() == sliced, f"{type(node).__name__} span includes surrounding whitespace: {sliced!r}"


@pytest.mark.parametrize(
    "blip_code",
    [
        pytest.param('name = "bob"; ret name', id="an assignment and a return"),
        pytest.param('email -> username "@" *; ret username', id="a decomposition with a wildcard"),
        pytest.param('ret input[0] " and " input[1]', id="indexing and concatenation"),
        pytest.param('flag = true; if flag { ret "yes" } ret "no"', id="an if with a boolean condition"),
        pytest.param('e = "a@b"; if e -> user "@" * { ret user } else { ret "none" }', id="a conditional decomposition"),
    ],
)
def test_a_node_span_contains_the_spans_of_its_children(parser: Parser, blip_code: str):
    """A composite node is built from its children's tokens, so its span has to reach across all of them."""

    stack: list[tuple[int, Located]] = []

    for depth, node in __get_located_nodes(parser.parse(blip_code)):
        del stack[depth:]

        for _, ancestor in stack:
            assert ancestor.location is not None and node.location is not None
            assert ancestor.location.offset <= node.location.offset, f"{type(node).__name__} starts before its ancestor"
            assert node.location.end <= ancestor.location.end, f"{type(node).__name__} ends after its ancestor"

        stack.append((depth, node))


def test_a_statement_span_covers_the_whole_statement():
    """A statement-level error points at the statement, so its span has to reach past the expression inside it."""

    blip_code = 'name = "bob" "by"; ret name'
    program = Parser().parse(blip_code)

    assert [blip_code[s.location.offset : s.location.end] for s in program.statements if s.location] == [
        'name = "bob" "by"',
        "ret name",
    ]


def test_a_directive_span_covers_its_keyword():
    """`!in username email` is wrong as a whole when it binds a reserved name, so the caret belongs under all of it."""

    blip_code = "!in raw; ret raw; "
    directives = Parser().parse(blip_code).directives

    assert directives is not None and directives.input is not None and directives.input.location is not None
    span = directives.input.location

    assert blip_code[span.offset : span.end] == "!in raw"


def test_a_string_literal_span_covers_its_quotes():
    """The value excludes the delimiters; the span includes them, because that is what a reader sees."""

    blip_code = 'ret "bob"'
    returned = Parser().parse(blip_code).statements[0]

    assert isinstance(returned, Return)
    span = returned.expression.location

    assert span is not None
    assert blip_code[span.offset : span.end] == '"bob"'
    assert returned.expression == StringLiteral(value="bob")


def test_an_empty_list_still_has_a_span():
    blip_code = "empty = []; ret empty; "
    assignment = Parser().parse(blip_code).statements[0]

    assert isinstance(assignment, Assignment)
    span = assignment.expression.location

    assert span is not None
    assert blip_code[span.offset : span.end] == "[]"


def test_a_span_is_not_part_of_a_nodes_identity(parser: Parser):
    assert parser.parse('ret "x"') == parser.parse('\n\n\nret "x"')
    assert parser.parse('ret "x"').statements[0].location != parser.parse('\n\n\nret "x"').statements[0].location


def test_the_parser_leaves_every_type_unset(parser: Parser):
    """Types are the analyser's job. The parser produces a tree with no annotations at all."""

    program = parser.parse('name = "bob"; ret name')

    assignment = program.statements[0]
    assert isinstance(assignment, Assignment)
    assert assignment.target.blip_type is None
    assert assignment.expression.blip_type is None


def test_an_if_with_a_boolean_condition_parses(parser: Parser):
    program = parser.parse('flag = true; if flag { ret "yes" }')

    assert program.statements[1] == If(
        condition=Identifier(name="flag"),
        body=[Return(expression=StringLiteral(value="yes"))],
        otherwise=None,
    )


def test_an_if_with_an_else_parses(parser: Parser):
    program = parser.parse('flag = true; if flag { ret "yes" } else { ret "no" }')

    assert program.statements[1] == If(
        condition=Identifier(name="flag"),
        body=[Return(expression=StringLiteral(value="yes"))],
        otherwise=[Return(expression=StringLiteral(value="no"))],
    )


def test_a_conditional_decomposition_parses(parser: Parser):
    """The `->` after the condition is what tells a decomposition test from an ordinary expression."""

    program = parser.parse('e = "a@b"; if e -> user "@" * { ret user }')

    assert program.statements[1] == If(
        condition=DecompTest(
            target=Identifier(name="e"),
            pattern=[Identifier(name="user"), StringLiteral(value="@"), Wildcard()],
        ),
        body=[Return(expression=Identifier(name="user"))],
        otherwise=None,
    )


def test_an_absent_else_is_distinct_from_an_empty_one(parser: Parser):
    """`None` means the program wrote no `else`; an empty list means it wrote one that does nothing."""

    without = parser.parse("flag = true; if flag { }").statements[1]
    with_empty = parser.parse("flag = true; if flag { } else { }").statements[1]

    assert isinstance(without, If)
    assert isinstance(with_empty, If)

    assert without.otherwise is None
    assert with_empty.otherwise == []


def test_an_empty_block_parses(parser: Parser):
    program = parser.parse("flag = true; if flag { }")

    assert program.statements[1] == If(condition=Identifier(name="flag"), body=[], otherwise=None)


def test_ifs_nest(parser: Parser):
    program = parser.parse('flag = true; if flag { if flag { ret "deep" } }')

    assert program.statements[1] == If(
        condition=Identifier(name="flag"),
        body=[If(condition=Identifier(name="flag"), body=[Return(expression=StringLiteral(value="deep"))], otherwise=None)],
        otherwise=None,
    )


@pytest.mark.parametrize(
    "blip_code",
    [
        pytest.param('flag = true; if flag { ret "yes" } else { ret "no" }', id="a whole if on one line"),
        pytest.param('flag = true; if flag { ret "yes" }', id="a closing brace on the last statement's line"),
        pytest.param('flag = true; x = "a.b"; if flag { x -> head "." tail } ret head', id="a decomposition last in a block"),
        pytest.param('flag = true; if flag { y = "z" } ret y', id="an assignment last in a block"),
    ],
)
def test_a_closing_brace_terminates_the_statement_before_it(parser: Parser, blip_code: str):
    """A block ends unambiguously, so the last statement in one needs no newline after it."""

    parser.parse(blip_code)


def test_an_else_branch_may_follow_the_closing_brace_on_the_same_line(parser: Parser):
    """An `if` consumes no terminator of its own, which is what lets `} else {` work."""

    parser.parse('flag = true; if flag { ret "yes" } else { ret "no" }')


@pytest.mark.parametrize(
    "blip_code",
    [
        pytest.param('flag = true; if flag; ret "yes"', id="a block that never opens"),
        pytest.param('flag = true; if flag { ret "yes"', id="a block that never closes"),
        pytest.param('else { ret "yes" }', id="an else with no if"),
        pytest.param('if { ret "yes" }', id="an if with no condition"),
        pytest.param('flag = true; if flag { ret "yes" } else', id="an else with no block"),
    ],
)
def test_a_malformed_if_raises_parser_error(parser: Parser, blip_code: str):
    with pytest.raises(ParserError):
        parser.parse(blip_code)


def test_only_a_variable_can_be_decomposed_in_a_condition(parser: Parser):
    """The same restriction the decomposition statement has: the target is a name, not an arbitrary expression."""

    with pytest.raises(ParserError, match="Only a variable can be decomposed"):
        parser.parse('if input[0] -> user "@" * { ret user }')
