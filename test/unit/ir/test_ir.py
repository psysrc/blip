"""
Unit tests for the BlipIR object model in `bliplib/ir/`.

The round trip is checked against every reference program; the rest of these tests cover the validation that `load` performs,
since that is what lets every consumer stop checking the shape for itself.
"""

import pytest
from bliplib.errors import BlipError
from bliplib.ir import (
    Assignment,
    BooleanLiteral,
    Concatenation,
    Decomposition,
    Directives,
    FixedDirective,
    IRError,
    Identifier,
    Index,
    IntegerLiteral,
    ListLiteral,
    Program,
    RangeDirective,
    Return,
    StringLiteral,
    Wildcard,
    load,
    load_directive,
    load_pattern_element,
    load_statement,
    load_value,
)
from bliplib.parser import Parser
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_reference_programs
from typing import Any


@pytest.mark.parametrize("ref", get_reference_programs())
def test_reference_program_ir_serialisation_round_trip(ref: ReferenceProgram):
    assert load(ref.blip_ir).to_dict() == ref.blip_ir


def test_ir_error_is_a_blip_error():
    assert issubclass(IRError, BlipError)


def test_nested_program_loads_into_the_expected_tree():
    program = load(Parser().parse("ret input[0]"))

    assert program == Program(statements=[Return(expression=Index(target=Identifier(name="input"), index=IntegerLiteral(value=0)))])


def test_every_statement_kind_loads():
    program = load(Parser().parse('name = "bob" "@" domain\nemail -> user "@" *\nret name'))

    assert program == Program(
        statements=[
            Assignment(
                target=Identifier(name="name"),
                expression=Concatenation(operands=[StringLiteral(value="bob"), StringLiteral(value="@"), Identifier(name="domain")]),
            ),
            Decomposition(
                target=Identifier(name="email"),
                pattern=[Identifier(name="user"), StringLiteral(value="@"), Wildcard()],
            ),
            Return(expression=Identifier(name="name")),
        ]
    )


def test_literals_and_lists_load():
    program = load(Parser().parse('things = ["a", 1, true]\nempty = []\nret things'))

    assert program.statements[0] == Assignment(
        target=Identifier(name="things"),
        expression=ListLiteral(elements=[StringLiteral(value="a"), IntegerLiteral(value=1), BooleanLiteral(value=True)]),
    )
    assert program.statements[1] == Assignment(target=Identifier(name="empty"), expression=ListLiteral(elements=[]))


def test_directives_load():
    program = load(Parser().parse("!in username email\n!out 1..3\nret username"))

    assert program.directives == Directives(input=FixedDirective(count=2, names=["username", "email"]), output=RangeDirective(min=1, max=3))


def test_absent_directives_are_distinct_from_empty_directives():
    """`None` means the program declared no directives; `Directives()` means it declared an empty set of them."""

    without = {"type": "program", "statements": []}
    empty = {"type": "program", "statements": [], "directives": {}}

    assert load(without).directives is None
    assert load(empty).directives == Directives()

    assert load(without).to_dict() == without
    assert load(empty).to_dict() == empty


def test_fixed_directive_without_names_omits_the_key():
    fixed = {"type": "fixed", "value": 2}

    assert load_directive(fixed) == FixedDirective(count=2, names=None)
    assert load_directive(fixed).to_dict() == fixed


def test_open_ended_range_directive_round_trips():
    for directive in [{"type": "range", "min": 1, "max": None}, {"type": "range", "min": None, "max": 3}]:
        assert load_directive(directive).to_dict() == directive


def test_blip_type_is_not_serialised_while_it_is_unset():
    """Stage 1 has no type model, so every value loads with no type and nothing is written for it."""

    program = load(Parser().parse("ret input[0]"))
    returned = program.statements[0]
    assert isinstance(returned, Return)

    assert returned.expression.blip_type is None
    assert "blip_type" not in returned.expression.to_dict()


def test_an_annotation_is_rejected_until_stage_3_adds_the_codec():
    """Stage 1 predates `blip_type`, so it is an unknown key. Stage 3 deliberately changes this."""

    with pytest.raises(IRError):
        load_value({"type": "identifier", "name": "x", "blip_type": "string"})


@pytest.mark.parametrize(
    "blip_ir",
    [
        pytest.param({}, id="root has no type"),
        pytest.param({"type": 7, "statements": []}, id="type is not a string"),
        pytest.param({"type": "return", "expression": {"type": "identifier", "name": "x"}}, id="root is not a program"),
        pytest.param({"type": "program"}, id="program is missing statements"),
        pytest.param({"type": "program", "statements": {}}, id="statements is not a list"),
        pytest.param({"type": "program", "statements": [], "colour": "blue"}, id="program has an unknown key"),
        pytest.param({"type": "program", "statements": [], "directives": {"sideways": {}}}, id="directives has an unknown key"),
        pytest.param({"type": "program", "statements": [{"type": "identifier", "name": "x"}]}, id="value used as a statement"),
        pytest.param({"type": "program", "statements": ["nope"]}, id="statements holds something that is not a node"),
        pytest.param({"type": "program", "statements": [], "directives": "nope"}, id="directives is not an object"),
        pytest.param({"type": "program", "statements": [{"type": "return", "expression": []}]}, id="expression is not a node"),
    ],
)
def test_malformed_program_raises_ir_error(blip_ir: dict[str, Any]):
    with pytest.raises(IRError):
        load(blip_ir)


@pytest.mark.parametrize(
    "blip_ir",
    [
        pytest.param("not a node", id="a string"),
        pytest.param(None, id="None"),
        pytest.param([], id="a list"),
        pytest.param(7, id="an integer"),
    ],
)
def test_a_node_that_is_not_an_object_raises_ir_error(blip_ir: Any):
    """
    Every loader must reject a non-object at runtime.

    The public loaders are annotated `dict[str, Any]`, but indexing one yields `Any`, so the type checker can only vouch for the
    root of the tree - it cannot tell that a nested value is a node at all.
    """

    for loader in [load, load_value, load_statement, load_pattern_element, load_directive]:
        with pytest.raises(IRError):
            loader(blip_ir)


@pytest.mark.parametrize(
    "blip_ir",
    [
        pytest.param({"type": "expression", "value": {"type": "identifier", "name": "x"}}, id="the removed expression wrapper"),
        pytest.param({"type": "nonsense"}, id="unknown value kind"),
        pytest.param({"type": "identifier"}, id="identifier is missing its name"),
        pytest.param({"type": "identifier", "name": 7}, id="identifier name is not a string"),
        pytest.param({"type": "identifier", "name": "x", "extra": 1}, id="identifier has an unknown key"),
        pytest.param({"type": "string_literal", "value": 7}, id="string literal holds an integer"),
        pytest.param({"type": "integer_literal", "value": "7"}, id="integer literal holds a string"),
        pytest.param({"type": "integer_literal", "value": True}, id="integer literal holds a boolean"),
        pytest.param({"type": "boolean_literal", "value": 1}, id="boolean literal holds an integer"),
        pytest.param({"type": "list", "elements": {}}, id="list elements is not a list"),
        pytest.param({"type": "list", "elements": [{"type": "nonsense"}]}, id="list holds an unknown kind"),
        pytest.param({"type": "concatenation", "operands": [{"type": "return"}]}, id="concatenation holds a statement"),
        pytest.param(
            {"type": "index", "identifier": {"type": "string_literal", "value": "x"}, "index": {"type": "integer_literal", "value": 0}},
            id="index target is not an identifier",
        ),
        pytest.param(
            {"type": "index", "identifier": "nope", "index": {"type": "integer_literal", "value": 0}}, id="index target is not a node"
        ),
    ],
)
def test_malformed_value_raises_ir_error(blip_ir: dict[str, Any]):
    with pytest.raises(IRError):
        load_value(blip_ir)


@pytest.mark.parametrize(
    "blip_ir",
    [
        pytest.param({"type": "decomposition_wildcard", "extra": 1}, id="wildcard has an unknown key"),
        pytest.param({"type": "integer_literal", "value": 0}, id="integer literal is not a pattern element"),
        pytest.param(
            {"type": "index", "identifier": {"type": "identifier", "name": "x"}, "index": {"type": "integer_literal", "value": 0}},
            id="indexing is not a pattern element",
        ),
    ],
)
def test_malformed_pattern_element_raises_ir_error(blip_ir: dict[str, Any]):
    with pytest.raises(IRError):
        load_pattern_element(blip_ir)


@pytest.mark.parametrize(
    "blip_ir",
    [
        pytest.param({"type": "fixed"}, id="fixed is missing its count"),
        pytest.param({"type": "fixed", "value": None}, id="fixed count is None"),
        pytest.param({"type": "fixed", "value": 1, "names": "bob"}, id="fixed names is not a list"),
        pytest.param({"type": "fixed", "value": 1, "names": [7]}, id="fixed names holds a non-string"),
        pytest.param({"type": "range", "min": 1}, id="range is missing its max"),
        pytest.param({"type": "range", "min": "1", "max": None}, id="range min is not an integer"),
        pytest.param({"type": "sideways", "value": 1}, id="unknown directive kind"),
    ],
)
def test_malformed_directive_raises_ir_error(blip_ir: dict[str, Any]):
    with pytest.raises(IRError):
        load_directive(blip_ir)


def test_a_malformed_node_deep_in_the_tree_is_rejected():
    blip_ir = {
        "type": "program",
        "statements": [
            {"type": "return", "expression": {"type": "list", "elements": [{"type": "integer_literal", "value": "nope"}]}},
        ],
    }

    with pytest.raises(IRError):
        load(blip_ir)


def test_statement_loader_rejects_an_unknown_kind():
    with pytest.raises(IRError):
        load_statement({"type": "nonsense"})
