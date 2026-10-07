"""
Unit tests for unification in `bliplib/analysis/unification.py`.

These cover the mechanics no Blip program can currently reach - chained holes, the occurs check - and the error paths that the
reference programs, being all valid, never exercise.
"""

import pytest
from bliplib.analysis import Unifier, Var, describe_inferred_type
from bliplib.errors import SemanticError
from bliplib.ir.types import List, Scalar

CONTEXT = "while testing"


@pytest.fixture
def unifier():
    return Unifier()


def test_each_fresh_hole_is_distinct(unifier: Unifier):
    assert unifier.fresh() != unifier.fresh()


def test_an_unbound_hole_resolves_to_itself(unifier: Unifier):
    hole = unifier.fresh()

    assert unifier.resolve(hole) == hole


def test_unifying_a_hole_with_a_type_fills_the_hole(unifier: Unifier):
    hole = unifier.fresh()
    unifier.unify(hole, Scalar.STRING, CONTEXT)

    assert unifier.resolve(hole) == Scalar.STRING


def test_a_hole_is_filled_from_either_side(unifier: Unifier):
    hole = unifier.fresh()
    unifier.unify(Scalar.INTEGER, hole, CONTEXT)

    assert unifier.resolve(hole) == Scalar.INTEGER


def test_holes_chain(unifier: Unifier):
    """Unifying two holes binds one to the other, so resolving means walking to the end of the chain."""

    first, second, third = unifier.fresh(), unifier.fresh(), unifier.fresh()

    unifier.unify(first, second, CONTEXT)
    unifier.unify(second, third, CONTEXT)
    unifier.unify(third, Scalar.BOOLEAN, CONTEXT)

    assert unifier.resolve(first) == Scalar.BOOLEAN


def test_unifying_a_hole_with_itself_learns_nothing(unifier: Unifier):
    hole = unifier.fresh()
    unifier.unify(hole, hole, CONTEXT)

    assert unifier.resolve(hole) == hole


def test_unifying_two_lists_recurses_into_their_elements(unifier: Unifier):
    hole = unifier.fresh()
    unifier.unify(List(hole), List(Scalar.STRING), CONTEXT)

    assert unifier.resolve(hole) == Scalar.STRING


def test_unifying_nested_lists_recurses_all_the_way_down(unifier: Unifier):
    hole = unifier.fresh()
    unifier.unify(List(List(hole)), List(List(Scalar.INTEGER)), CONTEXT)

    assert unifier.resolve(hole) == Scalar.INTEGER


def test_unifying_two_identical_scalars_is_allowed(unifier: Unifier):
    unifier.unify(Scalar.STRING, Scalar.STRING, CONTEXT)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        pytest.param(Scalar.STRING, Scalar.INTEGER, id="two different scalars"),
        pytest.param(Scalar.STRING, List(Scalar.STRING), id="a scalar and a list"),
        pytest.param(List(Scalar.STRING), List(Scalar.INTEGER), id="lists of different elements"),
        pytest.param(List(List(Scalar.STRING)), List(Scalar.STRING), id="lists nested to different depths"),
    ],
)
def test_types_that_cannot_be_made_equal_raise(unifier: Unifier, left: object, right: object):
    with pytest.raises(SemanticError):
        unifier.unify(left, right, CONTEXT)  # type: ignore[arg-type] - deliberately mismatched


def test_the_occurs_check_rejects_an_infinite_type(unifier: Unifier):
    """`?1 = list[?1]` has no finite solution. Without this check the substitution turns cyclic and grounding never ends."""

    hole = unifier.fresh()

    with pytest.raises(SemanticError):
        unifier.unify(hole, List(hole), CONTEXT)


def test_the_occurs_check_looks_at_every_depth(unifier: Unifier):
    hole = unifier.fresh()

    with pytest.raises(SemanticError):
        unifier.unify(hole, List(List(hole)), CONTEXT)


def test_the_occurs_check_sees_through_a_chain(unifier: Unifier):
    first, second = unifier.fresh(), unifier.fresh()
    unifier.unify(first, second, CONTEXT)

    with pytest.raises(SemanticError):
        unifier.unify(second, List(first), CONTEXT)


def test_grounding_digs_all_the_way_down(unifier: Unifier):
    inner, outer = unifier.fresh(), unifier.fresh()

    unifier.unify(inner, Scalar.STRING, CONTEXT)
    unifier.unify(outer, List(inner), CONTEXT)

    assert unifier.ground(List(outer), CONTEXT) == List(List(Scalar.STRING))


def test_grounding_an_unbound_hole_raises(unifier: Unifier):
    """This is what makes a resolved tree serialisable: a hole can never reach a value node's type."""

    with pytest.raises(SemanticError):
        unifier.ground(unifier.fresh(), CONTEXT)


def test_grounding_a_hole_nested_in_a_list_raises(unifier: Unifier):
    with pytest.raises(SemanticError):
        unifier.ground(List(unifier.fresh()), CONTEXT)


def test_an_error_message_resolves_what_it_already_knows(unifier: Unifier):
    """A hole that has been filled should appear in a message as what it stands for, not as `?1`."""

    hole = unifier.fresh()
    unifier.unify(hole, Scalar.STRING, CONTEXT)

    with pytest.raises(SemanticError, match=r"list\[string\]"):
        unifier.unify(List(hole), Scalar.INTEGER, CONTEXT)


@pytest.mark.parametrize(
    ("inferred", "expected"),
    [
        pytest.param(Scalar.STRING, "string", id="a scalar"),
        pytest.param(List(Scalar.INTEGER), "list[integer]", id="a list"),
        pytest.param(List(List(Scalar.BOOLEAN)), "list[list[boolean]]", id="a nested list"),
        pytest.param(Var(7), "?7", id="a hole"),
        pytest.param(List(Var(7)), "list[?7]", id="a list of holes"),
    ],
)
def test_describe_renders_a_type_for_a_message(inferred: object, expected: str):
    assert describe_inferred_type(inferred) == expected  # type: ignore[arg-type] - exercising every shape
