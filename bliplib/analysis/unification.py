"""
Implements unification: the algorithm that works out what the holes in two types must be for the types to become identical.

It is the only place a type error is raised, and the only place anything about a hole is learned.
"""

from bliplib.analysis.types import InferredType, Var, describe_inferred_type
from bliplib.errors import SemanticError
from bliplib.ir.types import BlipType, List, Scalar


class Unifier:
    """
    Solves type constraints by filling holes.

    Every hole this hands out is recorded in one substitution, so the whole state of inference is in one place. Resolving a
    type therefore means asking the unifier, not inspecting the type: a `Var` on its own means nothing without the unifier
    that issued it.
    """

    def __init__(self):
        self.__substitution: dict[int, InferredType] = {}
        self.__holes_issued = 0

    def fresh(self) -> Var:
        """Issue a new, unbound hole."""

        self.__holes_issued += 1
        return Var(self.__holes_issued)

    def resolve(self, inferred: InferredType) -> InferredType:
        """
        Resolve a hole unification chain.

        Holes chain together because unifying two holes binds one to the other, so this walks to the end of the chain.
        The result is either a concrete type, or another hole that is still unknown.
        """

        while isinstance(inferred, Var) and inferred.id in self.__substitution:
            inferred = self.__substitution[inferred.id]

        return inferred

    def unify(self, first: InferredType, second: InferredType) -> None:
        """Constrain two types to be the same type, filling holes as needed."""

        first = self.resolve(first)
        second = self.resolve(second)

        match (first, second):
            case (Var(), Var()) if first == second:
                # Identical holes`, e.g. ?1 and ?1
                return

            case (Var(id=hole), _):
                self.__fill_hole(hole, second)

            case (_, Var(id=hole)):
                self.__fill_hole(hole, first)

            case (List(element=left_element), List(element=right_element)):
                self.unify(left_element, right_element)

            case (Scalar(), Scalar()) if first == second:
                # Identical scalars, e.g. "string" and "string"
                return

            case _:
                # TODO: This is used verbatim by the caller but doesn't necessarily have to be
                # Consider rewriting this and updating the caller
                raise SemanticError(f"expected '{self.__describe(second)}', found '{self.__describe(first)}'")

    def ground(self, inferred: InferredType) -> BlipType:
        """
        Ground the inferred type to a concrete type with no holes. If the inferred type has any holes, raise a `SemanticError`.
        """

        resolved = self.resolve(inferred)

        match resolved:
            case Scalar():
                return resolved

            case List(element=element):
                return List(self.ground(element))

            case Var():
                # The hole's number would mean nothing to anyone reading their own program
                raise SemanticError("no constraint determines it")

    def __fill_hole(self, hole_id: int, inferred: InferredType) -> None:
        """Record what a hole stands for, having first checked that it does not stand for something containing itself."""

        if self.__occurs(hole_id, inferred):
            # `?1 = list[?1]` is an infinite type. Without this check the substitution would become cyclic.
            raise SemanticError("the type would have to contain itself")

        self.__substitution[hole_id] = inferred

    def __describe(self, inferred: InferredType) -> str:
        """Render a type for an error message, resolved as deeply as possible so that an already-known hole does not leak in."""

        return describe_inferred_type(self.__resolve_deep(inferred))

    def __resolve_deep(self, inferred: InferredType) -> InferredType:
        """Resolve at every depth, leaving any hole that nothing has been learned about yet in place."""

        resolved = self.resolve(inferred)

        match resolved:
            case List(element=element):
                return List(self.__resolve_deep(element))

            case _:
                return resolved

    def __occurs(self, hole: int, inferred: InferredType) -> bool:
        """Report whether a hole appears anywhere inside a type."""

        resolved = self.resolve(inferred)

        match resolved:
            case Var(id=other):
                return other == hole

            case List(element=element):
                return self.__occurs(hole, element)

            case Scalar():
                return False
