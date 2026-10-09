"""
Unit tests for the Blip Analyser in `bliplib/analysis/`.

The reference programs supply the conformance check: every one of them must analyse cleanly, every value node must come out with
a type, and the type inferred for what a program returns must agree with the output its `#### Execution` table records.
"""

from collections.abc import Iterator

import pytest

from bliplib.analysis import analyse
from bliplib.errors import SemanticError
from bliplib.ir import (
    Assignment,
    Concatenation,
    Decomposition,
    Identifier,
    Index,
    ListLiteral,
    Program,
    Return,
    Value,
    Wildcard,
)
from bliplib.ir.types import List, Scalar
from bliplib.parser import Parser
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_compiling_reference_programs


def analyse_source(source: str) -> Program:
    """Parse, load and analyse Blip source, the way every consumer will from Stage 3 onwards."""

    return analyse(Parser().parse(source))


def values_of(program: Program) -> Iterator[Value]:
    """Every value node in the program, which is exactly the set of nodes that must end up with a type."""

    for statement in program.statements:
        match statement:
            case Assignment():
                yield from _values_within(statement.target)
                yield from _values_within(statement.expression)

            case Return():
                yield from _values_within(statement.expression)

            case Decomposition():
                yield from _values_within(statement.target)

                for element in statement.pattern:
                    if not isinstance(element, Wildcard):
                        yield from _values_within(element)


def _values_within(value: Value) -> Iterator[Value]:
    yield value

    match value:
        case Concatenation():
            for operand in value.operands:
                yield from _values_within(operand)

        case Index():
            yield from _values_within(value.target)
            yield from _values_within(value.index)

        case ListLiteral():
            for element in value.elements:
                yield from _values_within(element)

        case _:
            return


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_reference_program_analyses_cleanly(ref: ReferenceProgram):
    """No reference program is rejected: none of the analyser's rules is a behaviour change for code that already exists."""

    analyse_source(ref.blip_code)


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_every_value_of_a_reference_program_gets_a_type(ref: ReferenceProgram):
    """Invariant 1: analysis succeeding means every value node has a type."""

    program = analyse_source(ref.blip_code)

    values = list(values_of(program))
    assert all(value.blip_type is not None for value in values), f"untyped values in '{ref.name}'"


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_inferred_return_type_matches_the_recorded_output(ref: ReferenceProgram):
    """
    Conformance, built entirely out of fixtures that already existed.

    A program whose return type is a string produces exactly one output string; one returning a list of strings may produce any
    number. If inference and the interpreter disagreed about a program, this is where it would show.
    """

    program = analyse_source(ref.blip_code)
    returns = [statement for statement in program.statements if isinstance(statement, Return)]

    if not returns:
        return  # Program never returns, so there is no return type to check. Pass the test gracefully.

    # TODO: Check all return statements, not just the first one
    # Difficult because we need a way of identifying which return statement was executed

    returned = returns[0].expression.blip_type
    assert returned in (Scalar.STRING, List(Scalar.STRING)), f"'{ref.name}' returns {returned}"

    for i, execution in enumerate(ref.executions):
        if not execution.expect_success:
            continue

        if returned == Scalar.STRING:
            num_outputs = len(execution.output_strings)
            assert num_outputs == 1, (
                f"'{ref.name}' execution #{i + 1}: Returned {num_outputs} strings but return expression has str type (instead of list(str))"
            )


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('x = "a"\nx = 1\nret x', id="reassignment changes a variable's type"),
        pytest.param("ret 5", id="returning an integer"),
        pytest.param("ret true", id="returning a boolean"),
        pytest.param('ret ["a", 1]', id="a heterogeneous list"),
        pytest.param('ret [["a"]]', id="returning a nested list"),
        pytest.param('things = []\nret "ok"', id="an empty list whose element type is never determined"),
        pytest.param("ret missing", id="an unbound identifier"),
        pytest.param('input = "a"\nret "ok"', id="assigning to the reserved input"),
        pytest.param('!in input\nret "ok"', id="an input directive naming the reserved input"),
        pytest.param('x = 5\nx -> a "@" b\nret a', id="decomposing something that is not a string"),
        pytest.param('xs = ["a"]\ni = "z"\nret xs[i]', id="indexing with a string"),
        pytest.param('x = "a"\nret x[0]', id="indexing something that is not a list"),
        pytest.param('n = 5\nname = "a" n\nret name', id="concatenating an integer"),
    ],
)
def test_bad_program_raises_semantic_error(source: str):
    with pytest.raises(SemanticError):
        analyse_source(source)


def test_a_rejected_program_is_not_left_half_annotated():
    """Types are written only once the whole program has analysed, so a rejected program carries none of them."""

    program = Parser().parse('ret "fine"\nret 5')

    with pytest.raises(SemanticError):
        analyse(program)

    assert all(value.blip_type is None for value in values_of(program))


def test_an_empty_list_takes_its_type_from_how_it_is_used():
    """The showcase for unification: nothing about `[]` says what it holds, and the `ret` is what settles it."""

    program = analyse_source("things = []\nret things")

    assignment = program.statements[0]
    assert isinstance(assignment, Assignment)
    assert assignment.expression.blip_type == List(Scalar.STRING)
    assert assignment.target.blip_type == List(Scalar.STRING)


def test_reassignment_refines_a_hole_rather_than_rejecting_it():
    """`x = []` leaves a hole, so a later `x = ["a"]` fills it in. That is the same type becoming known, not a type changing."""

    program = analyse_source('x = []\nx = ["a"]\nret x')

    returned = program.statements[-1]
    assert isinstance(returned, Return)
    assert returned.expression.blip_type == List(Scalar.STRING)


def test_indexing_a_list_of_strings_gives_a_string():
    program = analyse_source("idx = 0\nret input[idx]")

    returned = program.statements[-1]
    assert isinstance(returned, Return)

    index = returned.expression
    assert isinstance(index, Index)
    assert index.blip_type == Scalar.STRING
    assert index.target.blip_type == List(Scalar.STRING)
    assert index.index.blip_type == Scalar.INTEGER


def test_decomposition_binds_every_captured_name_as_a_string():
    program = analyse_source('email = "a@b"\nemail -> user "@" *\nret user')

    decomposition = program.statements[1]
    assert isinstance(decomposition, Decomposition)
    assert decomposition.target.blip_type == Scalar.STRING

    captured = [element for element in decomposition.pattern if isinstance(element, Identifier)]
    assert [element.blip_type for element in captured] == [Scalar.STRING]


def test_a_named_input_directive_binds_each_name_as_a_string():
    program = analyse_source("!in username email\nret username")

    returned = program.statements[-1]
    assert isinstance(returned, Return)
    assert returned.expression.blip_type == Scalar.STRING


def test_input_is_always_a_list_of_strings():
    program = analyse_source("ret input")

    returned = program.statements[-1]
    assert isinstance(returned, Return)
    assert returned.expression.blip_type == List(Scalar.STRING)


def test_a_nested_list_is_well_typed_even_though_it_cannot_be_returned():
    program = analyse_source('x = [["a"]]\nret "ok"')

    assignment = program.statements[0]
    assert isinstance(assignment, Assignment)
    assert assignment.expression.blip_type == List(List(Scalar.STRING))
