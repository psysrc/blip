"""
Unit tests for the Blip Analyser in `bliplib/analysis/`.

The reference programs supply the conformance check: every one of them must analyse cleanly, every value node must come out with
a type, and the type inferred for what a program returns must agree with the output its `#### Execution` table records.
"""

from collections.abc import Iterator, Sequence

import pytest

from bliplib.analysis import analyse
from bliplib.errors import SemanticError
from bliplib.ir import (
    Assignment,
    Concatenation,
    Decomposition,
    DecompPattern,
    DecompTest,
    Identifier,
    If,
    Index,
    ListLiteral,
    Program,
    Return,
    Statement,
    Value,
    Wildcard,
)
from bliplib.ir.types import List, Scalar
from bliplib.parser import Parser
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_compiling_reference_programs


def __analyse_source(source: str) -> Program:
    """Parse, load and analyse Blip source, the way every consumer will from Stage 3 onwards."""

    return analyse(Parser().parse(source))


def __values_of(program: Program) -> Iterator[Value]:
    """Every value node in the program, which is exactly the set of nodes that must end up with a type."""

    yield from __values_in_statements(program.statements)


def __values_in_statements(statements: Sequence[Statement]) -> Iterator[Value]:
    """
    The same walk over a list of statements, so that it reaches inside a block as well as the program.

    An `if` that this failed to recurse into would not fail any test - it would quietly shrink what the invariant below is
    checking, which is the more expensive kind of wrong.
    """

    for statement in statements:
        match statement:
            case Assignment():
                yield from __values_within(statement.target)
                yield from __values_within(statement.expression)

            case Return():
                yield from __values_within(statement.expression)

            case Decomposition():
                yield from __values_within(statement.target)
                yield from __values_in_pattern(statement.pattern)

            case If():
                match statement.condition:
                    case DecompTest() as test:
                        yield from __values_within(test.target)
                        yield from __values_in_pattern(test.pattern)

                    case condition:
                        yield from __values_within(condition)

                yield from __values_in_statements(statement.body)
                yield from __values_in_statements(statement.otherwise or [])


def __values_in_pattern(pattern: DecompPattern) -> Iterator[Value]:
    """A wildcard captures nothing and binds no name, so it is the one pattern element with no type to check."""

    for element in pattern:
        if not isinstance(element, Wildcard):
            yield from __values_within(element)


def __values_within(value: Value) -> Iterator[Value]:
    yield value

    match value:
        case Concatenation():
            for operand in value.operands:
                yield from __values_within(operand)

        case Index():
            yield from __values_within(value.target)
            yield from __values_within(value.index)

        case ListLiteral():
            for element in value.elements:
                yield from __values_within(element)

        case _:
            return


def __semantic_error(source: str) -> SemanticError:
    """Analyse source that is expected to be rejected, and hand back the error it raised."""

    with pytest.raises(SemanticError) as raised:
        __analyse_source(source)

    return raised.value


def __get_span_from_error(source: str, error: SemanticError) -> str:
    """The source a span selects, so a test can say what the caret lands on without counting offsets."""

    assert error.location is not None, f"error carries no span: {error}"

    return source[error.location.offset : error.location.end]


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_reference_program_analyses_cleanly(ref: ReferenceProgram):
    """No reference program is rejected: none of the analyser's rules is a behaviour change for code that already exists."""

    __analyse_source(ref.blip_code)


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_every_value_of_a_reference_program_gets_a_type(ref: ReferenceProgram):
    """Invariant 1: analysis succeeding means every value node has a type."""

    program = __analyse_source(ref.blip_code)

    values = list(__values_of(program))
    assert all(value.blip_type is not None for value in values), f"untyped values in '{ref.name}'"


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_inferred_return_type_matches_the_recorded_output(ref: ReferenceProgram):
    """
    Conformance, built entirely out of fixtures that already existed.

    A program whose return type is a string produces exactly one output string; one returning a list of strings may produce any
    number. If inference and the interpreter disagreed about a program, this is where it would show.
    """

    program = __analyse_source(ref.blip_code)
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
        pytest.param('x = "a"; x = 1; ret x', id="reassignment changes a variable's type"),
        pytest.param("ret 5", id="returning an integer"),
        pytest.param("ret true", id="returning a boolean"),
        pytest.param('ret ["a", 1]', id="a heterogeneous list"),
        pytest.param('ret [["a"]]', id="returning a nested list"),
        pytest.param('things = []; ret "ok"', id="an empty list whose element type is never determined"),
        pytest.param("ret missing", id="an unbound identifier"),
        pytest.param('input = "a"; ret "ok"', id="assigning to the reserved input"),
        pytest.param('!in input; ret "ok"', id="an input directive naming the reserved input"),
        pytest.param('x = 5; x -> a "@" b; ret a', id="decomposing something that is not a string"),
        pytest.param('xs = ["a"]; i = "z"; ret xs[i]', id="indexing with a string"),
        pytest.param('x = "a"; ret x[0]', id="indexing something that is not a list"),
        pytest.param('n = 5; name = "a" n; ret name', id="concatenating an integer"),
    ],
)
def test_bad_program_raises_semantic_error(source: str):
    with pytest.raises(SemanticError):
        __analyse_source(source)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('x = "ab"; x -> a b; ret a', id="two captures side by side"),
        pytest.param('x = "ab"; x -> * b; ret b', id="a wildcard and a capture"),
        pytest.param('x = "ab"; x -> a *; ret a', id="a capture and a wildcard"),
        pytest.param('x = "ab"; x -> "<" a b ">"; ret a', id="adjacent captures in the middle of a pattern"),
    ],
)
def test_adjacent_capturing_pattern_elements_raise_semantic_error(source: str):
    """A capture ends where the literal after it begins, so nothing can satisfy a pattern that puts two captures together."""

    with pytest.raises(SemanticError, match="ambiguous decomposition pattern"):
        __analyse_source(source)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('x = "a@b"; x -> a "@" b; ret a', id="captures separated by a literal"),
        pytest.param('x = "a@b"; x -> a "@" *; ret a', id="a trailing wildcard"),
        pytest.param('x = "a@b"; x -> * "@" b; ret b', id="a leading wildcard"),
        pytest.param('x = "ab"; x -> "a" "b"; ret x', id="literals only"),
        pytest.param('x = "ab"; x -> a; ret a', id="a single capture taking everything"),
    ],
)
def test_a_pattern_whose_captures_are_separated_is_accepted(source: str):
    __analyse_source(source)


def test_a_rejected_program_is_not_left_half_annotated():
    """Types are written only once the whole program has analysed, so a rejected program carries none of them."""

    program = Parser().parse('ret "fine"; ret 5')

    with pytest.raises(SemanticError):
        analyse(program)

    assert all(value.blip_type is None for value in __values_of(program))


def test_an_empty_list_takes_its_type_from_how_it_is_used():
    """The showcase for unification: nothing about `[]` says what it holds, and the `ret` is what settles it."""

    program = __analyse_source("things = []; ret things")

    assignment = program.statements[0]
    assert isinstance(assignment, Assignment)
    assert assignment.expression.blip_type == List(Scalar.STRING)
    assert assignment.target.blip_type == List(Scalar.STRING)


def test_reassignment_refines_a_hole_rather_than_rejecting_it():
    """`x = []` leaves a hole, so a later `x = ["a"]` fills it in. That is the same type becoming known, not a type changing."""

    program = __analyse_source('x = []; x = ["a"]; ret x')

    returned = program.statements[-1]
    assert isinstance(returned, Return)
    assert returned.expression.blip_type == List(Scalar.STRING)


def test_indexing_a_list_of_strings_gives_a_string():
    program = __analyse_source("idx = 0; ret input[idx]")

    returned = program.statements[-1]
    assert isinstance(returned, Return)

    index = returned.expression
    assert isinstance(index, Index)
    assert index.blip_type == Scalar.STRING
    assert index.target.blip_type == List(Scalar.STRING)
    assert index.index.blip_type == Scalar.INTEGER


def test_decomposition_binds_every_captured_name_as_a_string():
    program = __analyse_source('email = "a@b"; email -> user "@" *; ret user')

    decomposition = program.statements[1]
    assert isinstance(decomposition, Decomposition)
    assert decomposition.target.blip_type == Scalar.STRING

    captured = [element for element in decomposition.pattern if isinstance(element, Identifier)]
    assert [element.blip_type for element in captured] == [Scalar.STRING]


def test_a_named_input_directive_binds_each_name_as_a_string():
    program = __analyse_source("!in username email; ret username")

    returned = program.statements[-1]
    assert isinstance(returned, Return)
    assert returned.expression.blip_type == Scalar.STRING


def test_input_is_always_a_list_of_strings():
    program = __analyse_source("ret input")

    returned = program.statements[-1]
    assert isinstance(returned, Return)
    assert returned.expression.blip_type == List(Scalar.STRING)


def test_a_nested_list_is_well_typed_even_though_it_cannot_be_returned():
    program = __analyse_source('x = [["a"]]; ret "ok"')

    assignment = program.statements[0]
    assert isinstance(assignment, Assignment)
    assert assignment.expression.blip_type == List(List(Scalar.STRING))


def test_a_name_used_twice_in_one_decomposition_pattern_is_ill_formed():
    with pytest.raises(SemanticError):
        __analyse_source('x = "abc"; x -> dup "b" dup; ret dup')


def test_empty_literals_in_decomposition_are_ill_formed():
    """Empty literals don't affect the pattern, so don't allow them. Keep it simple."""

    with pytest.raises(SemanticError):
        __analyse_source('x = input[0]; x -> "" rest; ret rest')


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param('greeting = "hi"; ret name', "name", id="an unbound identifier"),
        pytest.param('x = "a"; x = 1; ret x', "1", id="the value whose type conflicts"),
        pytest.param('count = 5; ret "total: " count', "count", id="the operand that cannot concatenate"),
        pytest.param('ret ["a", 1]', "1", id="the element that breaks a list's homogeneity"),
        pytest.param('x = []; ret "ok"', "[]", id="the list whose element type is never determined"),
        pytest.param("n = 5; n -> a '.' b; ret a; ", "n", id="a decomposition target that is not a string"),
        pytest.param("x = 'a.b'; x -> p '.' p; ret p; ", "p", id="the second capture of a repeated name"),
        pytest.param("x = 'ab'; x -> p q; ret p; ", "p", id="the first of two adjacent captures"),
        pytest.param("x = 'a'; x -> '' p; ret p; ", "''", id="an empty pattern literal"),
        pytest.param('input = "x"; ret input', "input", id="an attempt to rebind the reserved name"),
        pytest.param("x = []; ret x[0]; ", "x[0]", id="a return whose type could be either"),
    ],
)
def test_a_semantic_error_points_at_the_source_that_caused_it(source: str, expected: str):
    error = __semantic_error(source)

    assert __get_span_from_error(source, error) == expected


@pytest.mark.parametrize(
    ("source", "note_text"),
    [
        pytest.param('x = "a"; x = 1; ret x', "x", id="where a reassigned name was first bound"),
        pytest.param('count = 5; ret "total: " count', "count", id="where a non-string operand was bound"),
        pytest.param("n = 5; n -> a '.' b; ret a; ", "n", id="where a non-string decomposition target was bound"),
        pytest.param("x = 'a.b'; x -> p '.' p; ret p; ", "p", id="the first capture of a repeated name"),
        pytest.param("x = 'ab'; x -> p q; ret p; ", "q", id="the element that follows an ambiguous capture"),
    ],
)
def test_a_two_site_error_points_at_the_other_site_too(source: str, note_text: str):
    error = __semantic_error(source)

    assert len(error.notes) == 1, f"expected one note, got {error.notes}"

    note = error.notes[0]
    assert source[note.location.offset : note.location.end] == note_text


def test_a_conflict_note_names_the_type_the_earlier_site_bound():
    """The point of the note is that the two sites disagree, so it has to say what the earlier one decided."""

    error = __semantic_error('x = "a"; x = 1; ret x')

    assert error.notes[0].message == "'x' was bound as 'string' here"


def test_a_conflict_with_the_built_in_input_has_no_note():
    error = __semantic_error("ret input[0] input; ")

    assert error.location is not None
    assert error.notes == ()


def test_an_undetermined_type_names_the_value():
    error = __semantic_error('x = []; ret "ok"')

    assert "cannot infer the type of a list" in str(error)


def test_the_return_error_reads_as_a_sentence():
    error = __semantic_error("x = []; ret x[0]; ")

    assert str(error) == "return expression has unknown type"


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('ret "total: " missing', id="inside a concatenation"),
        pytest.param('ret ["a", missing]', id="inside a list literal"),
        pytest.param('x = ["a"]; ret x[missing]', id="inside an index"),
        pytest.param("missing -> a '.' b; ret a; ", id="as a decomposition target"),
    ],
)
def test_unbound_identifiers_have_simple_error_messages_inside_complex_statements(source: str):
    error = __semantic_error(source)

    assert str(error) == "'missing' is used but never bound"


def test_a_constraint_failure_keeps_both_the_reason_and_the_detail():
    error = __semantic_error('count = 5; ret "total: " count')

    assert str(error) == "only strings can be concatenated: expected 'string', found 'integer'"


def test_an_undetermined_type_has_a_friendly_error_message():
    error = __semantic_error('x = []; ret "ok"')

    assert str(error) == "cannot infer the type of a list: no constraint determines it"


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('flag = true; if flag {;   ret "yes"; }; ret "no"', id="a boolean condition"),
        pytest.param('e = "a@b"; if e -> user "@" * {;   ret user; } else {;   ret "none"; }', id="a conditional decomposition"),
        pytest.param('flag = true; if flag {;   if flag {;     ret "deep";   }; }; ret "no"', id="nested ifs"),
        pytest.param('flag = true; if flag { x = ["a"] } else { x = [] }; ret x', id="a join that closes a hole"),
    ],
)
def test_every_value_inside_an_if_gets_a_type(source: str):
    """Invariant 1 again, for values a block holds - the walk above has to reach them for this to mean anything."""

    values = list(__values_of(__analyse_source(source)))

    assert values, "the walk found no values at all, so this would pass vacuously"
    assert all(value.blip_type is not None for value in values), f"untyped values in: {source}"


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('if "hello" {;   ret "yes"; }', id="a string"),
        pytest.param("n = 3; if n {;   ret 'yes'; }; ", id="an integer"),
        pytest.param("if input {;   ret 'yes'; }; ", id="a list of strings"),
    ],
)
def test_a_condition_that_is_not_a_boolean_is_rejected(source: str):
    assert "must be a boolean" in str(__semantic_error(source))


def test_a_condition_is_annotated_with_its_type():
    program = __analyse_source("flag = true; if flag { ret 'yes' }; ret 'no'; ")
    conditional = program.statements[1]

    assert isinstance(conditional, If)
    assert isinstance(conditional.condition, Identifier)
    assert conditional.condition.blip_type == Scalar.BOOLEAN


def test_a_condition_that_is_an_unresolved_hole_is_made_boolean():
    """Constraining the condition is a unification, not a comparison, so a hole in the condition gets closed by it."""

    program = __analyse_source("x = []; if x[0] { ret 'yes' }; ret 'no'; ")
    assignment = program.statements[0]

    assert isinstance(assignment, Assignment)
    assert assignment.target.blip_type == List(Scalar.BOOLEAN)


def test_a_capture_is_not_bound_after_the_block_it_guards():
    """A failed match binds nothing, so the names a conditional decomposition captures cannot outlive its block."""

    error = __semantic_error('e = "a@b"; if e -> user "@" * {;   ret "then"; }; ret user')

    assert "'user' is used but never bound" in str(error)


def test_a_name_bound_in_only_one_branch_is_not_bound_afterwards():
    error = __semantic_error('flag = true; if flag { x = "a" }; ret x')

    assert "'x' is used but never bound" in str(error)


def test_a_name_bound_in_every_branch_is_bound_afterwards():
    program = __analyse_source('flag = true; if flag { x = "a" } else { x = "b" }; ret x')
    returned = program.statements[2]

    assert isinstance(returned, Return)
    assert returned.expression.blip_type == Scalar.STRING


def test_an_if_without_an_else_binds_nothing_afterwards():
    """There is no join to make without an `else`: one path through the `if` binds nothing at all."""

    error = __semantic_error('flag = true; if flag { x = "a" } else { y = "b" }; ret x')

    assert "'x' is used but never bound" in str(error)


def test_branches_that_bind_the_same_name_to_different_types_are_rejected():
    """The caret lands on the `else` branch's binding and the note on the body's, so both ends of the conflict are named."""

    source = 'flag = true; if flag { x = "a" } else { x = 1 }; ret x'
    error = __semantic_error(source)

    assert "bound in both branches" in str(error)

    assert __get_span_from_error(source, error) == "x"
    assert error.location is not None
    assert error.location.offset == source.rindex("x =")

    (note,) = error.notes
    assert note.location is not None
    assert note.location.offset == source.index("x =")


def test_a_join_unifies_rather_than_compares():
    """An empty list in one branch is still `list[?]`, so the other branch is what settles its element type."""

    program = __analyse_source('flag = true; if flag { x = [] } else { x = ["a"] }; ret x')
    returned = program.statements[2]

    assert isinstance(returned, Return)
    assert returned.expression.blip_type == List(Scalar.STRING)


def test_a_name_from_an_outer_scope_is_not_shadowed_by_a_branch():
    """Assigning inside a branch unifies with the existing binding, so the monomorphic rule still applies."""

    error = __semantic_error('x = "a"; flag = true; if flag { x = 1 }; ret x')

    assert "cannot assign to 'x'" in str(error)


def test_input_stays_reserved_inside_a_branch():
    error = __semantic_error('flag = true; if flag { input = "x" }; ret "ok"')

    assert "reserved" in str(error)


def test_a_decomposition_condition_must_target_a_string():
    error = __semantic_error("n = 3; if n -> head '.' tail { ret 'yes' }; ")

    assert "only strings can be decomposed" in str(error)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("x = 'a.b'; if x -> first second { ret 'yes' }; ", id="adjacent captures"),
        pytest.param("x = 'a.b'; if x -> dup ',' dup { ret 'yes' }; ", id="a name captured twice"),
        pytest.param("x = 'a.b'; if x -> '' rest { ret 'yes' }; ", id="an empty literal"),
    ],
)
def test_the_pattern_rules_apply_to_a_condition_as_well(source: str):
    """The rules belong to the pattern, not to the statement, so a condition is held to all of them too."""

    __semantic_error(source)
