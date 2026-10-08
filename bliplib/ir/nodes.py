"""
Implements the BlipIR object model.

BlipIR is loaded from a `dict` into a tree of nodes, which consumers walk instead of destructuring a `dict` defensively.
This module is the only place that knows the on-disk JSON shape: `from_dict` reads it and `to_dict` writes it, and the two sit
side by side on every class so that a change cannot break the round trip unnoticed.

Three properties hold:

- `load()` validates. Anything malformed raises `IRError`, so a consumer never has to re-check the shape.
- Nodes are mutable, and their fields are public, because the analyser fills `blip_type` in place from Stage 2 onwards.
- The round trip is exact: `load(d).to_dict() == d` for any well-formed `d`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bliplib.errors import IRError
from bliplib.ir.types import BlipType, List, Scalar, format_type, parse_type

# The key a value node carries its type under. `type` is taken by the node kind.
ANNOTATION = "blip_type"
ANNOTATED = (ANNOTATION,)


def _as_dict(blip_ir: object, what_error: str) -> dict[str, Any]:
    """
    Narrow an arbitrary JSON value to a node.

    Indexing a `dict[str, Any]` yields `Any`, which the type checker will hand to a `dict[str, Any]` parameter without
    complaint, so nothing below the root of the tree can be taken on trust. Every loader narrows through here first, and
    because the private loaders take `object`, the type checker enforces that rather than leaving it to good intentions.
    """

    if not isinstance(blip_ir, dict):
        raise IRError(f"Expected {what_error} to be a dict, but got {type(blip_ir).__name__}")

    return blip_ir


def _type_of(node: dict[str, Any], what_error: str) -> str:
    """Read the `type` tag that says which type of node this is."""

    kind = node.get("type")

    if kind is None:
        raise IRError(f"Expected {what_error} to have a 'type' key, but its keys are {sorted(node)}")

    if not isinstance(kind, str):
        raise IRError(f"Expected the 'type' of {what_error} to be a string, but got {type(kind).__name__}")

    return kind


def _validate_node(node: dict[str, Any], kind: str, required: tuple[str, ...], optional: tuple[str, ...] = ()) -> None:
    """Validate that `node` is a node of the given type (`kind`) carrying exactly the expected keys."""

    if node.get("type") != kind:
        raise IRError(f"Expected a '{kind}' node, but got '{node.get('type')}'")

    keys = set(node) - {"type"}

    missing = sorted(set(required) - keys)
    if missing:
        raise IRError(f"A '{kind}' node is missing the key(s) {missing}")

    unknown = sorted(keys - set(required) - set(optional))
    if unknown:
        raise IRError(f"A '{kind}' node has unknown key(s) {unknown}")


def _get_string(node: dict[str, Any], key: str, kind: str) -> str:
    value = node.get(key)
    if not isinstance(value, str):
        raise IRError(f"Expected '{key}' of a '{kind}' node to be a string, but got {type(value).__name__}")

    return value


def _get_integer(node: dict[str, Any], key: str, kind: str) -> int:
    value = node.get(key)

    # `bool` is a subclass of `int`, so explicitly check if the value is a boolean
    if not isinstance(value, int) or isinstance(value, bool):
        raise IRError(f"Expected '{key}' of a '{kind}' node to be an integer, but got {type(value).__name__}")

    return value


def _get_optional_integer(node: dict[str, Any], key: str, kind: str) -> int | None:
    return None if node.get(key) is None else _get_integer(node, key, kind)


def _get_boolean(node: dict[str, Any], key: str, kind: str) -> bool:
    value = node.get(key)
    if not isinstance(value, bool):
        raise IRError(f"Expected '{key}' of a '{kind}' node to be a boolean, but got {type(value).__name__}")

    return value


def _get_blip_type(node: dict[str, Any], kind: str) -> BlipType | None:
    """Read a value node's type annotation. Absent is legal - the parser emits none, and `--no-analysis` dumps none."""

    annotation = node.get(ANNOTATION)

    if annotation is None:
        return None

    if not isinstance(annotation, str):
        raise IRError(f"Expected '{ANNOTATION}' of a '{kind}' node to be a string, but got {type(annotation).__name__}")

    return parse_type(annotation)


def _get_sequence(node: dict[str, Any], key: str, kind: str) -> list[Any]:
    value = node.get(key)
    if not isinstance(value, list):
        raise IRError(f"Expected '{key}' of a '{kind}' node to be a list, but got {type(value).__name__}")

    return value


@dataclass
class ValueNode:
    """
    Base class for every BlipIR value node.

    Values are the only nodes that represent a Blip type. `blip_type` starts as `None`, and the analyser fills it in once its
    resolution pass has a ground type to write. A hole is never stored here - it is not even assignable - so a value node either
    has no type yet or has one that can be serialised.
    """

    blip_type: BlipType | None = field(default=None, kw_only=True)

    def _value_to_dict(self, kind: str, **fields: Any) -> dict[str, Any]:
        node: dict[str, Any] = {"type": kind}

        if self.blip_type is not None:
            # Written straight after `type`, so a reader meets a node's kind and its type together
            node["blip_type"] = format_type(self.blip_type)

        node.update(fields)
        return node


@dataclass
class StringLiteral(ValueNode):
    value: str

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> StringLiteral:
        _validate_node(blip_ir, "string_literal", ("value",), ANNOTATED)
        return cls(value=_get_string(blip_ir, "value", "string_literal"), blip_type=_get_blip_type(blip_ir, "string_literal"))

    def to_dict(self) -> dict[str, Any]:
        return self._value_to_dict("string_literal", value=self.value)


@dataclass
class IntegerLiteral(ValueNode):
    value: int

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> IntegerLiteral:
        _validate_node(blip_ir, "integer_literal", ("value",), ANNOTATED)
        return cls(value=_get_integer(blip_ir, "value", "integer_literal"), blip_type=_get_blip_type(blip_ir, "integer_literal"))

    def to_dict(self) -> dict[str, Any]:
        return self._value_to_dict("integer_literal", value=self.value)


@dataclass
class BooleanLiteral(ValueNode):
    value: bool

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> BooleanLiteral:
        _validate_node(blip_ir, "boolean_literal", ("value",), ANNOTATED)
        return cls(value=_get_boolean(blip_ir, "value", "boolean_literal"), blip_type=_get_blip_type(blip_ir, "boolean_literal"))

    def to_dict(self) -> dict[str, Any]:
        return self._value_to_dict("boolean_literal", value=self.value)


@dataclass
class Identifier(ValueNode):
    name: str

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Identifier:
        _validate_node(blip_ir, "identifier", ("name",), ANNOTATED)
        return cls(name=_get_string(blip_ir, "name", "identifier"), blip_type=_get_blip_type(blip_ir, "identifier"))

    def to_dict(self) -> dict[str, Any]:
        return self._value_to_dict("identifier", name=self.name)


@dataclass
class Concatenation(ValueNode):
    operands: list[Value]

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Concatenation:
        _validate_node(blip_ir, "concatenation", ("operands",), ANNOTATED)
        return cls(
            operands=[_load_value(operand) for operand in _get_sequence(blip_ir, "operands", "concatenation")],
            blip_type=_get_blip_type(blip_ir, "concatenation"),
        )

    def to_dict(self) -> dict[str, Any]:
        return self._value_to_dict("concatenation", operands=[operand.to_dict() for operand in self.operands])


@dataclass
class Index(ValueNode):
    target: Identifier
    index: Value

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Index:
        _validate_node(blip_ir, "index", ("identifier", "index"), ANNOTATED)
        return cls(
            target=_load_identifier(blip_ir["identifier"]), index=_load_value(blip_ir["index"]), blip_type=_get_blip_type(blip_ir, "index")
        )

    def to_dict(self) -> dict[str, Any]:
        return self._value_to_dict("index", identifier=self.target.to_dict(), index=self.index.to_dict())


@dataclass
class ListLiteral(ValueNode):
    elements: list[Value]

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> ListLiteral:
        _validate_node(blip_ir, "list", ("elements",), ANNOTATED)
        return cls(
            elements=[_load_value(element) for element in _get_sequence(blip_ir, "elements", "list")],
            blip_type=_get_blip_type(blip_ir, "list"),
        )

    def to_dict(self) -> dict[str, Any]:
        return self._value_to_dict("list", elements=[element.to_dict() for element in self.elements])


@dataclass
class Wildcard:
    """The `*` of a decomposition pattern. It matches anything and binds nothing, so it carries no type."""

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Wildcard:
        _validate_node(blip_ir, "decomposition_wildcard", ())
        return cls()

    def to_dict(self) -> dict[str, Any]:
        return {"type": "decomposition_wildcard"}


@dataclass
class Assignment:
    target: Identifier
    expression: Value

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Assignment:
        _validate_node(blip_ir, "assignment", ("identifier", "expression"))
        return cls(target=_load_identifier(blip_ir["identifier"]), expression=_load_value(blip_ir["expression"]))

    def to_dict(self) -> dict[str, Any]:
        return {"type": "assignment", "identifier": self.target.to_dict(), "expression": self.expression.to_dict()}


@dataclass
class Return:
    expression: Value

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Return:
        _validate_node(blip_ir, "return", ("expression",))
        return cls(expression=_load_value(blip_ir["expression"]))

    def to_dict(self) -> dict[str, Any]:
        return {"type": "return", "expression": self.expression.to_dict()}


@dataclass
class Decomposition:
    target: Identifier
    pattern: list[PatternElement]

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Decomposition:
        _validate_node(blip_ir, "decomposition", ("identifier", "pattern"))

        return cls(
            target=_load_identifier(blip_ir["identifier"]),
            pattern=[_load_pattern_element(element) for element in _get_sequence(blip_ir, "pattern", "decomposition")],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "decomposition",
            "identifier": self.target.to_dict(),
            "pattern": [element.to_dict() for element in self.pattern],
        }


@dataclass
class FixedDirective:
    """A directive demanding an exact count of strings, optionally naming each one (`!in username email`)."""

    count: int
    names: list[str] | None = None

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> FixedDirective:
        _validate_node(blip_ir, "fixed", ("value",), ("names",))

        names: list[str] | None = None
        if "names" in blip_ir:
            names = []
            for name in _get_sequence(blip_ir, "names", "fixed"):
                if not isinstance(name, str):
                    raise IRError(f"Expected every name of a 'fixed' directive to be a string, but got {type(name).__name__}")
                names.append(name)

        return cls(count=_get_integer(blip_ir, "value", "fixed"), names=names)

    def to_dict(self) -> dict[str, Any]:
        node: dict[str, Any] = {"type": "fixed", "value": self.count}

        if self.names is not None:
            node["names"] = list(self.names)

        return node


@dataclass
class RangeDirective:
    """A directive permitting a range of counts (`!in 1..3`). An open end is `None`."""

    min: int | None
    max: int | None

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> RangeDirective:
        _validate_node(blip_ir, "range", ("min", "max"))
        return cls(min=_get_optional_integer(blip_ir, "min", "range"), max=_get_optional_integer(blip_ir, "max", "range"))

    def to_dict(self) -> dict[str, Any]:
        return {"type": "range", "min": self.min, "max": self.max}


@dataclass
class Directives:
    """The program's optional `!in` and `!out` directives."""

    input: Directive | None = None
    output: Directive | None = None

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Directives:
        # Directives carry no `type` tag, so there is no `_validate_node` call to make here
        unknown = sorted(set(blip_ir) - {"input", "output"})
        if unknown:
            raise IRError(f"'directives' has unknown key(s) {unknown}")

        return cls(
            input=_load_directive(blip_ir["input"]) if "input" in blip_ir else None,
            output=_load_directive(blip_ir["output"]) if "output" in blip_ir else None,
        )

    def to_dict(self) -> dict[str, Any]:
        node: dict[str, Any] = {}

        if self.input is not None:
            node["input"] = self.input.to_dict()

        if self.output is not None:
            node["output"] = self.output.to_dict()

        return node


@dataclass
class Program:
    """A whole Blip program: the root of every BlipIR tree."""

    statements: list[Statement]

    # `None` means the program declared no directives at all, which is distinct from declaring an empty set of them
    directives: Directives | None = None

    @classmethod
    def from_dict(cls, blip_ir: dict[str, Any]) -> Program:
        _validate_node(blip_ir, "program", ("statements",), ("directives",))

        return cls(
            statements=[_load_statement(statement) for statement in _get_sequence(blip_ir, "statements", "program")],
            directives=_load_directives(blip_ir["directives"]) if "directives" in blip_ir else None,
        )

    def to_dict(self) -> dict[str, Any]:
        node: dict[str, Any] = {
            "type": "program",
            "statements": [statement.to_dict() for statement in self.statements],
        }

        if self.directives is not None:
            node["directives"] = self.directives.to_dict()

        return node


# These unions are closed, so a `match` over one can be checked for exhaustiveness
Value = StringLiteral | IntegerLiteral | BooleanLiteral | Identifier | Concatenation | Index | ListLiteral
PatternElement = Identifier | StringLiteral | Wildcard
Statement = Assignment | Return | Decomposition
Directive = FixedDirective | RangeDirective


# Each loader comes in two halves. The private half takes `object`, because a node pulled out of a parent is `Any` and could be
# anything at all; it narrows with `_as_dict` and is what the rest of this module calls. The public half takes
# `dict[str, Any]`, which documents what a caller should hand over, and is a thin delegation to the private half.
#
# Taking `object` in the private half is what gives this teeth: the type checker refuses to pass an `object` on to a
# `dict[str, Any]` parameter, so every `from_dict` below is guaranteed to have been narrowed before it is reached.


def _derive_type(value: Value) -> BlipType | None:
    """
    Work out a value's type from its own kind and its children, or return `None` where that is not possible.

    Only two kinds carry type information the structure does not already pin down: an `identifier`, whose type comes from the
    environment, and an empty `list`, whose element type only inference determines. Everything else is derivable, which is what
    lets the annotations on them be checked rather than believed.
    """

    match value:
        case StringLiteral():
            return Scalar.STRING

        case IntegerLiteral():
            return Scalar.INTEGER

        case BooleanLiteral():
            return Scalar.BOOLEAN

        case Concatenation():
            return Scalar.STRING

        case ListLiteral(elements=[first, *_]):
            # A list is homogeneous, so the first element speaks for all of them. Elements that disagree with each other are a
            # semantic error for the analyser to report, not a malformed file.
            return None if first.blip_type is None else List(first.blip_type)

        case Index():
            match value.target.blip_type:
                case List(element=element):
                    return element

                case _:
                    return None

        case Identifier() | ListLiteral():
            return None


def _check_annotation(value: Value) -> None:
    """
    Reject an annotation that contradicts the node it sits on.

    `{"type": "integer_literal", "blip_type": "string"}` is a file at odds with itself, so something has to decide whether the
    kind or the annotation wins. This decides by rejecting the file, which turns the redundancy in an annotated IR into a
    checksum: a backend consuming a `.blipir` without re-analysing it still gets every derivable annotation verified.
    """

    if value.blip_type is None:
        return

    derived = _derive_type(value)

    if derived is not None and derived != value.blip_type:
        kind = value.to_dict()["type"]
        raise IRError(f"A '{kind}' node is annotated '{format_type(value.blip_type)}' but its structure says '{format_type(derived)}'")


def _load_value(blip_ir: object) -> Value:
    value = _load_value_unchecked(blip_ir)
    _check_annotation(value)

    return value


def _load_value_unchecked(blip_ir: object) -> Value:
    node = _as_dict(blip_ir, "a value")

    match _type_of(node, "a value"):
        case "string_literal":
            return StringLiteral.from_dict(node)
        case "integer_literal":
            return IntegerLiteral.from_dict(node)
        case "boolean_literal":
            return BooleanLiteral.from_dict(node)
        case "identifier":
            return Identifier.from_dict(node)
        case "concatenation":
            return Concatenation.from_dict(node)
        case "index":
            return Index.from_dict(node)
        case "list":
            return ListLiteral.from_dict(node)
        case kind:
            raise IRError(f"'{kind}' is not a BlipIR value")


def _load_pattern_element(blip_ir: object) -> PatternElement:
    node = _as_dict(blip_ir, "a decomposition pattern element")

    match _type_of(node, "a decomposition pattern element"):
        case "identifier":
            return Identifier.from_dict(node)
        case "string_literal":
            return StringLiteral.from_dict(node)
        case "decomposition_wildcard":
            return Wildcard.from_dict(node)
        case kind:
            raise IRError(f"'{kind}' is not a BlipIR decomposition pattern element")


def _load_statement(blip_ir: object) -> Statement:
    node = _as_dict(blip_ir, "a statement")

    match _type_of(node, "a statement"):
        case "assignment":
            return Assignment.from_dict(node)
        case "return":
            return Return.from_dict(node)
        case "decomposition":
            return Decomposition.from_dict(node)
        case kind:
            raise IRError(f"'{kind}' is not a BlipIR statement")


def _load_directive(blip_ir: object) -> Directive:
    node = _as_dict(blip_ir, "a directive")

    match _type_of(node, "a directive"):
        case "fixed":
            return FixedDirective.from_dict(node)
        case "range":
            return RangeDirective.from_dict(node)
        case kind:
            raise IRError(f"'{kind}' is not a BlipIR directive")


def _load_identifier(blip_ir: object) -> Identifier:
    """Load the identifier that an assignment, a decomposition or an index targets. Only an identifier may appear there."""

    return Identifier.from_dict(_as_dict(blip_ir, "an 'identifier' node"))


def _load_directives(blip_ir: object) -> Directives:
    """Load a program's `!in` and `!out` directives. This has no public half, since a caller reaches it through `load`."""

    return Directives.from_dict(_as_dict(blip_ir, "'directives'"))


def load_value(blip_ir: dict[str, Any]) -> Value:
    """Load a single BlipIR value. Raises `IRError` if it is malformed."""

    return _load_value(blip_ir)


def load_pattern_element(blip_ir: dict[str, Any]) -> PatternElement:
    """Load a single BlipIR decomposition pattern element. Raises `IRError` if it is malformed."""

    return _load_pattern_element(blip_ir)


def load_statement(blip_ir: dict[str, Any]) -> Statement:
    """Load a single BlipIR statement. Raises `IRError` if it is malformed."""

    return _load_statement(blip_ir)


def load_directive(blip_ir: dict[str, Any]) -> Directive:
    """Load a single BlipIR directive. Raises `IRError` if it is malformed."""

    return _load_directive(blip_ir)


def load(blip_ir: dict[str, Any]) -> Program:
    """
    Load BlipIR into the object model and validate it.

    Raises `IRError` if the BlipIR is malformed in any way.
    """

    # Nothing in this module loads a whole program recursively, so this needs no private half - it narrows directly
    return Program.from_dict(_as_dict(blip_ir, "a 'program' node"))
