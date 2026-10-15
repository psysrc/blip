"""Unit tests for source spans and diagnostic rendering."""

import textwrap

import pytest

from bliplib.source import SourceMap, Span


def test_a_span_knows_where_it_ends():
    assert Span(offset=4, length=3).end == 7


def test_covering_spans_both_operands():
    first = Span(offset=4, length=3)
    last = Span(offset=12, length=5)

    assert first.covering(last) == Span(offset=4, length=13)


def test_covering_does_not_care_which_way_round_it_is_given():
    """A node's first and last token are known by position in the source, not by the order the parser happened to see them."""

    first = Span(offset=4, length=3)
    last = Span(offset=12, length=5)

    assert last.covering(first) == first.covering(last)


def test_covering_a_span_with_itself_is_that_span():
    span = Span(offset=4, length=3)

    assert span.covering(span) == span


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        pytest.param(0, (1, 1), id="the very start"),
        pytest.param(2, (1, 3), id="within the first line"),
        pytest.param(3, (1, 4), id="the newline ending the first line"),
        pytest.param(4, (2, 1), id="the start of the second line"),
        pytest.param(6, (2, 3), id="within the second line"),
        pytest.param(8, (3, 1), id="the start of the last line"),
        pytest.param(11, (3, 4), id="just past the last character"),
    ],
)
def test_line_and_column_are_derived_from_an_offset(offset: int, expected: tuple[int, int]):
    source_map = SourceMap("abc\ndef\nghi")

    assert source_map.get_line_column(offset) == expected


def test_line_column_at_the_very_end_of_the_source():
    """An error can point just past the last character - that is where `EOF` is."""

    source_map = SourceMap("abc")

    assert source_map.get_line_column(3) == (1, 4)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        pytest.param(1, "abc", id="the first line"),
        pytest.param(2, "def", id="a middle line"),
        pytest.param(3, "", id="the empty line left by a trailing newline"),
    ],
)
def test_line_text_excludes_the_terminator(line: int, expected: str):
    source_map = SourceMap("abc\ndef\n")

    assert source_map.get_line_text(line) == expected


def test_line_text_drops_carriage_returns():
    source_map = SourceMap("abc\r\ndef\r\n")

    assert source_map.get_line_text(1) == "abc"


def test_describe_names_a_position_without_pointing_at_it():
    """Used for the *other* site in a two-site message, where only one site gets the caret."""

    source_map = SourceMap("abc\ndef\n")

    assert source_map.describe(Span(offset=5, length=1)) == "2:2"


def test_render_draws_a_caret_under_the_whole_span():
    source = 'name = "bob"\ntotal = count "items"\n'
    source_map = SourceMap(source, path="prog.blip")

    rendered = source_map.render("cannot concatenate 'integer'", Span(offset=source.index("count"), length=len("count")))

    expected = textwrap.dedent("""
        prog.blip:2:9: error: cannot concatenate 'integer'
          |
        2 | total = count "items"
          |         ^^^^^
    """).strip()

    assert rendered == expected


def test_render_without_a_span_still_names_the_file():
    """BlipIR loaded from a `.blipir` carries no spans, so its errors have to degrade to something rather than nothing."""

    source_map = SourceMap("abc\n", path="prog.blip")

    assert source_map.render("malformed BlipIR", None) == "prog.blip: error: malformed BlipIR"


def test_render_accepts_a_severity():
    source_map = SourceMap("abc\n", path="prog.blip")

    rendered = source_map.render("careful", Span(offset=0, length=1), severity="warning")

    expected = textwrap.dedent("""
        prog.blip:1:1: warning: careful
          |
        1 | abc
          | ^
    """).strip()

    assert rendered == expected


def test_render_gives_a_zero_length_span_one_caret():
    """`EOF` has nothing to underline, but an error at the end of a file still has to point somewhere."""

    source_map = SourceMap("abc", path="prog.blip")

    rendered = source_map.render("unexpected end of input", Span(offset=3, length=0))

    expected = textwrap.dedent("""
        prog.blip:1:4: error: unexpected end of input
          |
        1 | abc
          |    ^
    """).strip()

    assert rendered == expected


def test_render_clamps_a_caret_to_the_end_of_the_line():
    """A span is never widened past the line it starts on - carets running off the end would need explaining."""

    source_map = SourceMap("ab\ncd\n", path="prog.blip")

    rendered = source_map.render("too wide", Span(offset=0, length=99))

    expected = textwrap.dedent("""
        prog.blip:1:1: error: too wide
          |
        1 | ab
          | ^^
    """).strip()

    assert rendered == expected


def test_render_widens_the_gutter_for_a_long_line_number():
    """The caret line has to stay aligned with the source line however many digits the line number has."""

    source_map = SourceMap("\n" * 41 + "oops\n", path="prog.blip")

    rendered = source_map.render("here", Span(offset=41, length=4))

    expected = textwrap.dedent("""
        prog.blip:42:1: error: here
           |
        42 | oops
           | ^^^^
    """).strip()

    assert rendered == expected
