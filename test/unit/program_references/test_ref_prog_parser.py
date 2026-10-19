"""
Tests that `docs/refs/` is read correctly checking the markdown parsing against a second, far simpler reading of it.

`ReferenceParser` walks a markdown token stream, which is intricate enough that a program could go missing without any other
test noticing - every suite parametrises over whatever it hands back, so a dropped program silently stops being tested.
"""

import re
from pathlib import Path

import pytest

from test.common.ref_progs.getter import get_reference_program_files, get_reference_programs

# Each program always starts with a `##` heading. `####` section headings are not programs, so the space is what tells them apart.
_PROGRAM_HEADING = re.compile(r"^## +(.+?)\s*$")
_FENCE = re.compile(r"^```")


def get_program_headings(markdown_text: str) -> list[str]:
    """Get every program heading in a document, found without using `ReferenceParser` so the two readings are independent.

    Fenced blocks are skipped because Blip comments also starts with `#`, so a program's own code could otherwise be read
    as a heading.
    """

    headings: list[str] = []
    inside_fence = False

    for line in markdown_text.splitlines():
        if _FENCE.match(line):
            inside_fence = not inside_fence
            continue

        if inside_fence:
            continue

        heading = _PROGRAM_HEADING.match(line)
        if heading is not None:
            headings.append(heading.group(1))

    return headings


def test_every_program_heading_becomes_exactly_one_reference_program():
    """Comparing the names rather than the totals says which program went missing, not just that one did."""

    expected = [heading for path in get_reference_program_files() for heading in get_program_headings(path.read_text())]
    actual = [ref.name for ref in get_reference_programs()]

    # Both sides derive from the same files, so an empty glob would leave this passing with nothing compared
    assert expected, f"no program headings were found in {get_reference_program_files()}"

    assert sorted(actual) == sorted(expected)


@pytest.mark.parametrize("path", get_reference_program_files(), ids=lambda path: path.name)
def test_every_reference_file_holds_at_least_one_program(path: Path):
    assert get_program_headings(path.read_text())


def test_a_program_heading_is_told_apart_from_a_section_heading():
    """`#### Blip code` and friends are sections within a program, and must not be counted as programs themselves."""

    markdown = "## A Program\n\n#### Blip code\n\n#### Execution\n\n## Another Program\n"

    assert get_program_headings(markdown) == ["A Program", "Another Program"]


def test_a_heading_inside_a_fenced_block_is_not_a_program():
    """Blip comments start with `#`, so a program whose code contains one must not invent a program."""

    markdown = '## A Program\n\n```blip\n## not a heading\nret "ok"\n```\n'

    assert get_program_headings(markdown) == ["A Program"]
