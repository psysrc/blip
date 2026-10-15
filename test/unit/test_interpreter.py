"""
Unit tests for the interpreter.

The reference programs under `docs/refs/` are the comprehensive suite; these cover the errors the interpreter is still
responsible for. That list is short by design: the program arrives loaded and analysed, so a malformed tree is an `IRError`
from the loader and a type error is a `SemanticError` from the analyser. What is left depends on the input, which no amount of
static analysis can rule out.
"""

import pytest

from bliplib.analysis import analyse
from bliplib.errors import InterpreterError, SemanticError
from bliplib.interpreter import Interpreter
from bliplib.parser import Parser


def interpret(blip_code: str, input_strings: list[str]) -> list[str]:
    program = analyse(Parser().parse(blip_code))

    return Interpreter(program).run(input_strings)


def test_a_program_that_never_returns_is_an_error():
    with pytest.raises(InterpreterError, match="halted without returning"):
        interpret('x = "unused"', [])


def test_an_empty_program_never_returns():
    with pytest.raises(InterpreterError, match="halted without returning"):
        interpret("", [])


def test_indexing_past_the_end_is_an_error():
    """Whether a list has an element 0 depends on the input, so this stays a runtime check."""

    with pytest.raises(InterpreterError, match="out of bounds"):
        interpret("ret input[0]", [])


def test_a_decomposition_whose_literal_is_missing_is_an_error():
    """Whether a pattern matches depends on the input, so this stays a runtime check too."""

    with pytest.raises(InterpreterError, match="Decomposition failed"):
        interpret('email = input[0]\nemail -> user "@" *\nret user', ["not-an-email"])


def test_adjacent_capturing_pattern_elements_never_reach_the_interpreter():
    """
    A capturing element has to be followed by a literal, or there is nothing to tell it where to stop.

    This is input-independent, so the analyser should reject this before it reaches the interpreter.
    """

    with pytest.raises(SemanticError, match="Ambiguous decomposition pattern"):
        interpret('x = "ab"\nx -> a b\nret a', [])


@pytest.mark.parametrize(
    ("blip_code", "input_strings"),
    [
        pytest.param('!in 2\nret "ok"', ["only one"], id="too few inputs for a fixed directive"),
        pytest.param("!in username email\nret username", ["one", "two", "three"], id="too many inputs for a named directive"),
        pytest.param('!in 1..2\nret "ok"', ["a", "b", "c"], id="too many inputs for a ranged directive"),
    ],
)
def test_directive_arity_is_checked_against_the_input(blip_code: str, input_strings: list[str]):
    """Arity depends on how many strings arrive, which is why the design leaves it out of static analysis."""

    with pytest.raises(InterpreterError, match="validation failed"):
        interpret(blip_code, input_strings)


def test_indexing_with_a_variable_works():
    assert interpret("idx = 0\nret input[idx]", ["first", "second"]) == ["first"]


def test_values_of_every_type_round_trip_through_a_variable():
    assert interpret('n = 987\nb = true\ns = "blue"\nret [s, "black"]', []) == ["blue", "black"]
