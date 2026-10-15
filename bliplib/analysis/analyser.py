"""
Implements the Blip Analyser: the pass that gives every value in a program a type.

Analysis is a BlipIR-to-BlipIR transformation. It walks the tree collecting constraints, hands them to the `Unifier` to solve,
and then writes the solved types back onto the value nodes.

Inference and resolution are two separate walks for one reason: a type may not be known when the node carrying it is first
seen. `[]` is `list[?1]`, and `?1` is only pinned down by a later use. So the first walk records what it inferred for each
value, holes and all, and the second walk turns each of those into a ground type and stores it on the node. A hole is never
stored on a node - `blip_type` cannot hold one - so a node's type is either absent or serialisable, with nothing in between.
"""

from collections.abc import Sequence
from itertools import pairwise

from bliplib.analysis.environment import INPUT, Environment
from bliplib.analysis.types import InferredType, Var, describe_inferred_type
from bliplib.analysis.unification import Unifier
from bliplib.errors import SemanticError
from bliplib.ir.nodes import (
    Assignment,
    BooleanLiteral,
    Concatenation,
    Decomposition,
    DecompPattern,
    Directives,
    FixedDirective,
    Identifier,
    Index,
    IntegerLiteral,
    ListLiteral,
    PatternElement,
    Program,
    Return,
    Statement,
    StringLiteral,
    Value,
    Wildcard,
)
from bliplib.ir.types import BlipType, List, Scalar
from bliplib.source import Note, Span


def analyse(program: Program) -> Program:
    """
    Give every value in the program a type, and return the same program.

    Raises `SemanticError` on the first problem found. Nothing is written onto the tree unless the whole program analyses, so a
    rejected program is never left half-annotated.
    """

    return Analyser().analyse(program)


class Analyser:
    def __init__(self):
        self.__unifier = Unifier()
        self.__environment = Environment()

        # A mapping for all values in the program to their inferred types as they are discovered
        self.__inferred_types: list[tuple[Value, InferredType]] = []

    def analyse(self, program: Program) -> Program:
        self.__discover_all_inferred_types(program)
        self.__resolve_inferred_types()

        return program

    def __discover_all_inferred_types(self, program: Program) -> None:
        """Discover the inferred types of all values in the program, populating `self.__inferred`."""

        self.__bind_input_directive(program.directives)

        for statement in program.statements:
            self.__analyse_statement(statement)

    def __resolve_inferred_types(self) -> None:
        """Resolve all inferred types into a grounded concrete type."""

        for value, inferred in self.__inferred_types:
            value.blip_type = self.__ground(inferred, value)

    def __bind_input_directive(self, directives: Directives | None) -> None:
        """A named input directive binds each of its names as a string. A counted or ranged one binds nothing."""

        if directives is None:
            return

        match directives.input:
            case FixedDirective(names=[*names]) as directive:
                for name in names:
                    if name == INPUT:
                        raise SemanticError(f"input directives cannot bind to '{INPUT}'; the name is reserved", directive.location)

                    self.__environment.bind(name, Scalar.STRING, directive.location)

            case _:
                return

    def __analyse_statement(self, statement: Statement) -> None:
        match statement:
            case Assignment():
                self.__bind_identifier_type(statement.target, self.__infer_type(statement.expression), statement.expression.location)

            case Return():
                self.__analyse_return(statement)

            case Decomposition():
                self.__analyse_decomposition(statement)

    def __analyse_return(self, statement: Return) -> None:
        """
        A program returns a string or a list of strings.

        That is a disjunction, which unification cannot express, so it is settled by shape first: a list has its element
        constrained to a string, a scalar is constrained to be a string, and a bare hole never says which was meant.
        """

        returned = self.__infer_type(statement.expression)
        location = statement.expression.location
        reason = "a program can only return a string or a list of strings"

        match self.__unifier.resolve(returned):
            case List(element=element):
                self.__constrain_type(element, Scalar.STRING, reason, location)

            case Scalar() as scalar:
                self.__constrain_type(scalar, Scalar.STRING, reason, location)

            case Var():
                raise SemanticError("return expression has unknown type", location)

    def __analyse_decomposition(self, statement: Decomposition) -> None:
        """Decomposition takes a string apart, so its target is a string and every name it captures is a string."""

        target = self.__infer_type(statement.target)
        self.__constrain_type(
            target,
            Scalar.STRING,
            "only a string can be decomposed",
            statement.target.location,
            self.__binding_note(statement.target.name),
        )

        self.__check_pattern_literals_are_not_empty(statement.pattern)
        self.__check_pattern_adjacency(statement.pattern)
        self.__check_pattern_captures_are_distinct(statement.pattern)

        for element in statement.pattern:
            self.__analyse_pattern_element(element)

    def __check_pattern_literals_are_not_empty(self, pattern: DecompPattern) -> None:
        """Literals in a pattern cannot be empty.

        An empty literal matches at every position, so it says nothing about the string. Worse, it smuggles a pattern past the
        adjacency rule below: `x -> first "" second` separates two captures with a literal that cannot tell them apart, so it
        would be accepted and leave `first` empty for every input, while the identical `x -> first second` is rejected.
        """

        for element in pattern:
            if isinstance(element, StringLiteral) and element.value == "":
                raise SemanticError("a decomposition pattern cannot contain an empty string literal", element.location)

    def __check_pattern_adjacency(self, pattern: DecompPattern) -> None:
        """
        Every capturing element in a pattern is either last or followed by a string literal.

        A capture runs up to the literal that follows it, so two capturing elements side by side leave the first with nothing to say
        where it ends. No input can satisfy that, which is what makes it a static error rather than a failed match. This is not a
        typing rule, but it is the same kind of input-independent wrongness, and the analyser is the pass that owns those.
        """

        for element, following in pairwise(pattern):
            if isinstance(element, StringLiteral) or isinstance(following, StringLiteral):
                continue

            notes = []
            if following.location is not None:
                notes.append(Note(following.location, f"{describe_pattern_element(following)} follows it, with nothing in between"))

            raise SemanticError(
                f"ambiguous decomposition pattern: {describe_pattern_element(element)} is followed by "
                f"{describe_pattern_element(following)}",
                element.location,
                notes,
            )

    def __check_pattern_captures_are_distinct(self, pattern: DecompPattern) -> None:
        """A pattern can only capture each name at most once."""

        captured: dict[str, Span | None] = {}

        for element in pattern:
            if not isinstance(element, Identifier):
                continue

            if element.name in captured:
                first = captured[element.name]
                notes = [Note(first, f"'{element.name}' is already captured here")] if first is not None else []

                raise SemanticError(f"a decomposition pattern cannot capture '{element.name}' more than once", element.location, notes)

            captured[element.name] = element.location

    def __analyse_pattern_element(self, element: PatternElement) -> None:
        match element:
            case Identifier():
                self.__bind_identifier_type(element, Scalar.STRING)

            case StringLiteral():
                self.__infer_type(element)

            case Wildcard():
                # A wildcard matches anything and captures nothing, so it has no type and binds no name
                return

    def __bind_identifier_type(self, identifier: Identifier, inferred: InferredType, location: Span | None = None) -> None:
        """
        Bind an identifier to a type, and record the type of the identifier that names it.

        Variables are monomorphic: one type for their whole life. Binding an identifier that is already bound therefore unifies rather
        than rebinds, which refines a hole the earlier type still had but rejects a genuine change of type. When both types
        are already grounded, unification is exactly a comparison, so `x = "a"` followed by `x = 1` is still an error.
        """

        # Where the offending type came from. For a decomposition capture that is the identifier itself; for an assignment
        # it is the expression on the right, which is the part a reader needs to look at.
        location = location if location is not None else identifier.location

        existing = self.__environment.get_bound_type(identifier.name)

        if existing is None:
            self.__environment.bind(identifier.name, inferred, identifier.location)
            bound = inferred
        else:
            if identifier.name == INPUT:
                raise SemanticError(f"'{INPUT}' is reserved and cannot be re-assigned", identifier.location)

            self.__constrain_type(
                inferred,
                existing,
                f"cannot assign to '{identifier.name}'",
                location,
                self.__binding_note(identifier.name),
            )
            bound = existing

        self.__record(identifier, bound)

    def __infer_type(self, value: Value) -> InferredType:
        """Infer a value's type, recording it so that the resolution pass can ground it later."""

        inferred = self.__infer_uncollected(value)
        self.__record(value, inferred)

        return inferred

    def __infer_uncollected(self, value: Value) -> InferredType:
        match value:
            case StringLiteral():
                return Scalar.STRING

            case IntegerLiteral():
                return Scalar.INTEGER

            case BooleanLiteral():
                return Scalar.BOOLEAN

            case Identifier():
                return self.__environment.lookup(value.name, value.location)

            case Concatenation():
                for operand in value.operands:
                    self.__constrain_type(
                        self.__infer_type(operand),
                        Scalar.STRING,
                        "only strings can be concatenated",
                        operand.location,
                        self.__binding_note_for(operand),
                    )

                return Scalar.STRING

            case Index():
                element = self.__unifier.fresh()
                target = self.__infer_type(value.target)

                self.__constrain_type(
                    target,
                    List(element),
                    "only a list can be indexed",
                    value.target.location,
                    self.__binding_note(value.target.name),
                )
                self.__constrain_type(
                    self.__infer_type(value.index),
                    Scalar.INTEGER,
                    "a list index must be an integer",
                    value.index.location,
                    self.__binding_note_for(value.index),
                )

                return element

            case ListLiteral():
                # Every element shares one type, because a list is homogeneous. For `[]` nothing constrains it, which is why
                # an empty list that the program never uses has no determinable type.
                element = self.__unifier.fresh()

                for item in value.elements:
                    self.__constrain_type(
                        self.__infer_type(item), element, "every element of a list must have the same type", item.location
                    )

                return List(element)

    def __constrain_type(
        self,
        found: InferredType,
        expected: InferredType,
        reason: str,
        location: Span | None = None,
        notes: Sequence[Note] = (),
    ) -> None:
        """Require two types to be the same, and explain it if they cannot be."""

        try:
            self.__unifier.unify(found, expected)

        except SemanticError as err:
            raise SemanticError(f"{reason}: {err}", location, notes) from err

    def __ground(self, inferred: InferredType, value: Value) -> BlipType:
        """Resolve an inferred type to a concrete one, naming the value if nothing ever pinned it down."""

        try:
            return self.__unifier.ground(inferred)

        except SemanticError as err:
            raise SemanticError(f"cannot infer the type of {describe_value(value)}: {err}", value.location) from err

    def __record(self, value: Value, inferred: InferredType) -> None:
        self.__inferred_types.append((value, inferred))

    def __binding_note(self, name: str) -> list[Note]:
        """
        A note pointing at where a name was bound, for an error about its type.

        Empty when there is nothing useful to point at: `input` is bound before any source is read, and a program loaded
        from a `.blipir` carries no spans at all. A conflict then reports one site instead of two, which is the honest
        outcome rather than a guess.
        """

        location = self.__environment.get_bound_location(name)

        if location is None:
            return []

        inferred = self.__environment.get_bound_type(name)
        described = describe_inferred_type(self.__unifier.resolve(inferred)) if inferred is not None else "something"

        return [Note(location, f"'{name}' was bound as '{described}' here")]

    def __binding_note_for(self, value: Value) -> list[Note]:
        """The same note, when the offending expression may or may not turn out to be a plain variable."""

        return self.__binding_note(value.name) if isinstance(value, Identifier) else []


def describe_pattern_element(element: PatternElement) -> str:
    """Render a decomposition pattern element into a human-friendly string."""

    match element:
        case Identifier():
            return f"the capture '{element.name}'"

        case Wildcard():
            return "a wildcard"

        case StringLiteral():
            return f"the literal '{element.value}'"


def describe_value(value: Value) -> str:
    """Render the `Value` into a human-friendly string."""

    match value:
        case Identifier():
            return f"the variable '{value.name}'"

        case ListLiteral():
            return "a list"

        case _:
            return "an expression"
