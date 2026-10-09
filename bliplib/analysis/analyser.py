"""
Implements the Blip Analyser: the pass that gives every value in a program a type.

Analysis is a BlipIR-to-BlipIR transformation. It walks the tree collecting constraints, hands them to the `Unifier` to solve,
and then writes the solved types back onto the value nodes.

Inference and resolution are two separate walks for one reason: a type may not be known when the node carrying it is first
seen. `[]` is `list[?1]`, and `?1` is only pinned down by a later use. So the first walk records what it inferred for each
value, holes and all, and the second walk turns each of those into a ground type and stores it on the node. A hole is never
stored on a node - `blip_type` cannot hold one - so a node's type is either absent or serialisable, with nothing in between.
"""

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
from bliplib.ir.types import List, Scalar


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
        self.__inferred: list[tuple[Value, InferredType]] = []

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

        for value, inferred in self.__inferred:
            value.blip_type = self.__unifier.ground(inferred, "Static analysis final pass")

    def __bind_input_directive(self, directives: Directives | None) -> None:
        """A named input directive binds each of its names as a string. A counted or ranged one binds nothing."""

        if directives is None:
            return

        match directives.input:
            case FixedDirective(names=[*names]):
                for name in names:
                    if name == INPUT:
                        raise SemanticError(f"Input directives cannot bind to '{INPUT}'; name is reserved")

                    self.__environment.bind(name, Scalar.STRING)

            case _:
                return

    def __analyse_statement(self, statement: Statement) -> None:
        match statement:
            case Assignment():
                self.__bind_identifier(statement.target, self.__infer(statement.expression))

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

        returned = self.__infer(statement.expression)

        match self.__unifier.resolve(returned):
            case List(element=element):
                self.__unifier.unify(element, Scalar.STRING, "A program can only return a string or a list of strings")

            case Scalar() as scalar:
                self.__unifier.unify(scalar, Scalar.STRING, "A program can only return a string or a list of strings")

            case Var():
                raise SemanticError(
                    "Cannot infer type of return A program must return a string or a list of strings, but this could be either"
                )

    def __analyse_decomposition(self, statement: Decomposition) -> None:
        """Decomposition takes a string apart, so its target is a string and every name it captures is a string."""

        target = self.__infer(statement.target)
        self.__unifier.unify(target, Scalar.STRING, f"Only a string can be decomposed, and '{statement.target.name}' is not")

        self.__check_pattern_adjacency(statement.pattern)

        for element in statement.pattern:
            self.__analyse_pattern_element(element)

    def __check_pattern_adjacency(self, pattern: list[PatternElement]) -> None:
        """
        Every capturing element in a pattern is either last or followed by a string literal.

        A capture runs up to the literal that follows it, so two capturing elements side by side leave the first with nothing to say
        where it ends. No input can satisfy that, which is what makes it a static error rather than a failed match. This is not a
        typing rule, but it is the same kind of input-independent wrongness, and the analyser is the pass that owns those.
        """

        for element, following in pairwise(pattern):
            if isinstance(element, StringLiteral) or isinstance(following, StringLiteral):
                continue

            raise SemanticError(
                f"Ambiguous decomposition pattern: {describe_pattern_element(element)} is followed by {describe_pattern_element(following)}"
            )

    def __analyse_pattern_element(self, element: PatternElement) -> None:
        match element:
            case Identifier():
                self.__bind_identifier(element, Scalar.STRING)

            case StringLiteral():
                self.__infer(element)

            case Wildcard():
                # A wildcard matches anything and captures nothing, so it has no type and binds no name
                return

    def __bind_identifier(self, identifier: Identifier, inferred: InferredType) -> None:
        """
        Bind an identifier to a type, and record the type of the identifier that names it.

        Variables are monomorphic: one type for their whole life. Binding an identifier that is already bound therefore unifies rather
        than rebinds, which refines a hole the earlier type still had but rejects a genuine change of type. When both types
        are already grounded, unification is exactly a comparison, so `x = "a"` followed by `x = 1` is still an error.
        """

        existing = self.__environment.get_bound_type(identifier.name)

        if existing is None:
            self.__environment.bind(identifier.name, inferred)
            bound = inferred
        else:
            if identifier.name == INPUT:
                raise SemanticError(f"'{INPUT}' is reserved and cannot be re-assigned")

            self.__unifier.unify(
                inferred, existing, f"Binding identifier '{identifier.name}' to inferred type '{describe_inferred_type(inferred)}'"
            )
            bound = existing

        self.__record(identifier, bound)

    def __infer(self, value: Value) -> InferredType:
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
                return self.__environment.lookup(value.name)

            case Concatenation():
                for operand in value.operands:
                    self.__unifier.unify(self.__infer(operand), Scalar.STRING, "Only strings can be concatenated")

                return Scalar.STRING

            case Index():
                element = self.__unifier.fresh()
                target = self.__infer(value.target)

                self.__unifier.unify(target, List(element), f"Only a list can be indexed, and '{value.target.name}' is not")
                self.__unifier.unify(self.__infer(value.index), Scalar.INTEGER, "A list index must be an integer")

                return element

            case ListLiteral():
                # Every element shares one type, because a list is homogeneous. For `[]` nothing constrains it, which is why
                # an empty list that the program never uses has no determinable type.
                element = self.__unifier.fresh()

                for item in value.elements:
                    self.__unifier.unify(self.__infer(item), element, "Every element of a list must have the same type")

                return List(element)

    def __record(self, value: Value, inferred: InferredType) -> None:
        self.__inferred.append((value, inferred))


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
