"""Unit tests for the shared decomposition semantics."""

import re

import pytest

from bliplib.analysis import analyse
from bliplib.decomposition import FLAGS, describe_pattern, pattern_captures, pattern_regex
from bliplib.errors import InterpreterError
from bliplib.interpreter import Interpreter
from bliplib.ir import Decomposition, DecompPattern
from bliplib.parser import Parser


def _pattern_of(blip_code: str) -> DecompPattern:
    """The pattern of the first decomposition in a program, compiled the way the CLI compiles it."""

    program = analyse(Parser().parse(blip_code))
    decomposition = next(s for s in program.statements if isinstance(s, Decomposition))

    return decomposition.pattern


def _interpret(blip_code: str, input_strings: list[str]) -> list[str]:
    return Interpreter(analyse(Parser().parse(blip_code))).run(input_strings)


def test_a_literal_is_escaped_so_a_pattern_is_never_read_as_a_regex():
    """Literals in decompositions are always text. They must therefore be properly escaped before handing to the regex library."""

    pattern = _pattern_of('x = "a"\nx -> "a.c[" * "](x+)$"\nret "done"')

    # Every metacharacter here is matched as itself, and the '.' in particular matches a full stop rather than the 'b'
    assert re.fullmatch(pattern_regex(pattern), "a.c[xyz](x+)$", flags=FLAGS) is not None
    assert re.fullmatch(pattern_regex(pattern), "abc[xyz](x+)$", flags=FLAGS) is None


def test_a_wildcard_is_not_a_capture():
    """Group numbers index into the captures, so a wildcard must not consume one."""

    source = 'x = "a@b.c"\nx -> * "@" name "." *\nret name'
    pattern = _pattern_of(source)

    assert pattern_captures(pattern) == ["name"]
    assert _interpret(source, []) == ["b"]


def test_a_pattern_matches_across_a_newline():
    assert _interpret('x = input[0]\nx -> * "-" *\nret "found"', ["a\n-\nb"]) == ["found"]
    assert _interpret("x = input[0]\nx -> whole\nret whole", ["a\nb"]) == ["a\nb"]


def test_an_empty_string_is_decomposable():
    assert _interpret("x = input[0]\nx -> whole\nret whole", [""]) == [""]

    with pytest.raises(InterpreterError, match="Decomposition failed"):
        _interpret('x = input[0]\nx -> * "a" *\nret "found"', [""])


def test_a_failed_decomposition_names_the_pattern_it_expected():
    """The message has to say what was expected, and the pattern is the only description of that there is."""

    with pytest.raises(InterpreterError, match="""'abc' does not match the pattern '"b"'"""):
        _interpret('x = input[0]\nx -> "b"\nret "found"', ["abc"])


def test_a_pattern_is_described_as_the_blip_source_that_produced_it():
    pattern = _pattern_of('x = "a"\nx -> "<" name ">" *\nret name')

    assert describe_pattern(pattern) == '"<" name ">" *'
