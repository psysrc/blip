"""
Unit tests for the tokenizer.

The tokenizer is reached through the parser everywhere else, so these are the only tests that see a `Token` directly - which
is what spans need, since the parser hands them on to the IR and they are not serialised.
"""

from itertools import pairwise

import pytest

from bliplib.errors import TokenizerError
from bliplib.parser.tokenizer import Token, Tokenizer, TokenKind
from bliplib.source import Span

_SOURCES = [
    pytest.param('ret "Hello World!"', id="a one-line program"),
    pytest.param('name = "bob"\nret name\n', id="several lines"),
    pytest.param('email -> username "@" *\nret username', id="a decomposition"),
    pytest.param("// a header\n\n!in 2\nret input[0]\n", id="comments, blank lines and a directive"),
    pytest.param("a = 1; b = true; ret 'x'", id="semicolon-separated statements"),
    pytest.param('x = "multi\nline\nliteral"\nret x', id="a literal containing newlines"),
    pytest.param('if flag {\n  ret "yes"\n} else {\n  ret "no"\n}\n', id="an if with an else"),
    pytest.param('if email -> user "@" * { ret user }', id="a conditional decomposition on one line"),
    pytest.param("", id="an empty source"),
]


def tokens_of(source: str) -> list[Token]:
    """Every token in a source, ending with the `EOF` sentinel."""

    tokenizer = Tokenizer(source)
    collected = [tokenizer.next_token()]

    while collected[-1].type != "EOF":
        collected.append(tokenizer.next_token())

    return collected


@pytest.mark.parametrize("source", _SOURCES)
def test_every_span_slices_back_to_its_own_token_generics(source: str):
    """Generics: A rule-based check so the test asserts what a span *means*."""

    for token in tokens_of(source):
        sliced = source[token.location.offset : token.location.end]

        assert sliced == token.value, f"{token} has span {token.location}, which slices to {sliced!r}"


def test_every_span_slices_back_to_its_own_token_specifics():
    """Specifics: A data-based check so the test asserts actual data for one specific example."""

    source = 'ret "Hello World!"'
    #         ^   ^             ^
    # Offets: 0   4             18

    tokens = tokens_of(source)

    assert len(tokens) == 3

    assert tokens[0].location == Span(offset=0, length=3)
    assert tokens[1].location == Span(offset=4, length=14)
    assert tokens[2].location == Span(offset=18, length=0)


@pytest.mark.parametrize("source", _SOURCES)
def test_spans_run_forwards_and_never_overlap(source: str):
    """Each token begins at or after the end of the one before it - trivia is the gap between them."""

    tokens = tokens_of(source)

    for earlier, later in pairwise(tokens):
        assert later.location.offset >= earlier.location.end, f"{later} starts before {earlier} ended"


def test_the_last_token_is_always_eof():
    """Returned at the end of every source, including an empty one, and returned again if asked past it."""

    assert Tokenizer("").next_token().type == "EOF"

    tokenizer = Tokenizer("ret 'x'")

    while tokenizer.next_token().type != "EOF":
        pass

    assert tokenizer.next_token().type == "EOF"


def test_eof_is_an_empty_span_just_past_the_source():
    """There is nothing left to underline at the end of a file, only the place where it ran out."""

    source = "ret 'x'"

    eof = tokens_of(source)[-1]

    assert eof.location.offset == len(source)
    assert eof.location.length == 0


def test_a_span_is_an_offset_into_the_whole_source_not_into_its_line():
    """The tokenizer walks the source with an offset instead of consuming it, so later lines keep counting up."""

    source = "a = 1\nb = 2\nc = 3\n"

    identifiers = [token for token in tokens_of(source) if token.type == "IDENTIFIER"]

    assert [token.location.offset for token in identifiers] == [0, 6, 12]


def test_trivia_is_skipped_without_taking_the_following_token_span():
    """A comment and the whitespace around it yield no tokens, and the token after them still points at itself."""

    source = '// explain\n   ret   "x"'

    tokens = [token for token in tokens_of(source) if token.type not in {"EOL", "EOF"}]

    assert [(token.type, token.location.offset) for token in tokens] == [
        ("RETURN", source.index("ret")),
        ("STRING_LITERAL", source.index('"x"')),
    ]


def test_a_newline_is_an_eol_rather_than_whitespace():
    """
    Pattern order is load-bearing: `\\n` is matched before the whitespace pattern that would otherwise swallow it.

    `EOL` terminates a statement, so a newline skipped as trivia would silently join two lines into one.
    """

    assert [token.type for token in tokens_of("a\nb")] == ["IDENTIFIER", "EOL", "IDENTIFIER", "EOF"]


def test_a_keyword_is_matched_before_the_identifier_that_contains_it():
    """The other half of the ordering guarantee - `ret` must win over the identifier pattern, but only on a word boundary."""

    assert [token.type for token in tokens_of("ret")] == ["RETURN", "EOF"]
    assert [token.type for token in tokens_of("retry")] == ["IDENTIFIER", "EOF"]


def test_the_control_flow_keywords_are_matched_before_identifiers():
    """`if` and `else` are subject to the same ordering rule, so a name that merely starts with one stays a name."""

    assert [token.type for token in tokens_of("if")] == ["IF", "EOF"]
    assert [token.type for token in tokens_of("else")] == ["ELSE", "EOF"]

    assert [token.type for token in tokens_of("iffy")] == ["IDENTIFIER", "EOF"]
    assert [token.type for token in tokens_of("elsewhere")] == ["IDENTIFIER", "EOF"]


def test_braces_are_their_own_tokens():
    assert [token.type for token in tokens_of("{}")] == ["{", "}", "EOF"]


def test_unknown_syntax_is_quoted_from_where_it_failed():
    """Quoting from the start of the source instead would describe the wrong part of a program entirely."""

    with pytest.raises(TokenizerError, match="'£5'"):
        tokens_of("first = 1\nsecond = £5\n")


def test_a_span_is_not_part_of_a_tokens_identity():
    """Two tokens of the same kind and text are equal wherever they came from, so a test can say what was lexed."""

    tokens = tokens_of("x\nx")

    assert tokens[0] == tokens[2]
    assert tokens[0].location != tokens[2].location


def test_token_renders_in_expected_format():
    token = Token(TokenKind.IDENTIFIER, "foo", location=Span(offset=0, length=0))

    assert str(token) == "IDENTIFIER['foo']"


def test_token_containing_newlines_renders_correctly():
    token = Token(TokenKind.EOL, "\n", location=Span(offset=0, length=0))

    assert str(token) == "EOL['\\n']"


@pytest.mark.parametrize(
    "trivia",
    [
        pytest.param(" " * 5000, id="a long run of spaces"),
        pytest.param("\t" * 5000, id="a long run of tabs"),
        pytest.param("# comment\n" * 5000, id="a long run of comments"),
        pytest.param(" \t" * 5000, id="a long run of mixed whitespace"),
    ],
)
def test_a_long_run_of_trivia_does_not_exhaust_the_stack(trivia: str):
    """
    How much trivia separates two tokens is unbounded, so skipping it must not cost stack.

    Skipping by recursion made a perfectly well-formed program with enough indentation or enough comments in it raise
    `RecursionError` from inside the tokenizer.
    """

    tokens = tokens_of(f"ret{trivia}'ok'")

    assert [token.type for token in tokens if token.type != "EOL"] == ["RETURN", "STRING_LITERAL", "EOF"]


def test_a_run_of_whitespace_does_not_swallow_the_newline_that_ends_it():
    """Trivia is matched greedily, so it has to exclude `\\n` outright rather than rely on `EOL` being tried first."""

    tokens = tokens_of("ret   \n'ok'")

    assert [token.type for token in tokens] == ["RETURN", "EOL", "STRING_LITERAL", "EOF"]


def test_a_carriage_return_is_trivia_but_the_newline_after_it_is_not():
    """A CRLF source still has to produce exactly one `EOL` per line."""

    tokens = tokens_of("ret\r\n'ok'\r\n")

    assert [token.type for token in tokens] == ["RETURN", "EOL", "STRING_LITERAL", "EOL", "EOF"]
