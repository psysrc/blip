"""
Implements the environment: the variables in scope and the type each one has.
"""

from dataclasses import dataclass

from bliplib.analysis.types import InferredType
from bliplib.errors import SemanticError
from bliplib.ir.types import List, Scalar
from bliplib.source import Span

# The built-in variable holding the program's input strings. It is always bound, and binding it again is an error.
INPUT = "input"


@dataclass(frozen=True)
class Binding:
    """
    What a name is bound to, and where it was bound.

    The location is what lets a later conflict point at the *earlier* site as well as the offending one - the two-distant-
    sites case that a bare "cannot unify" message leaves the reader to go and find. It is optional because `input` is bound
    before any source is read, and because BlipIR loaded from a `.blipir` carries no spans at all.
    """

    inferred: InferredType
    location: Span | None = None


class Environment:
    """
    A single flat scope.

    Blip has no block constructs implemented yet, so one global scope is all that is needed. The analysis design settles how `if`,
    loops and conditional decomposition will bind names when they land, which is why this is a class rather than a bare dict:
    adding a scope stack later should preferably not disturb its callers.
    """

    def __init__(self):
        self.__variables: dict[str, Binding] = {INPUT: Binding(inferred=List(Scalar.STRING))}

    def lookup(self, name: str, location: Span | None = None) -> InferredType:
        """Return the type bound to a name, or raise if the name is not bound. `location` is where the name was used."""

        if name not in self.__variables:
            # TODO: Remove `location` from here and instead put it in the call site
            raise SemanticError(f"'{name}' is used but never bound", location)

        return self.__variables[name].inferred

    def get_bound_type(self, name: str) -> InferredType | None:
        """Return the type bound to a name, or `None` if it is not bound. Does not raise."""

        binding = self.__variables.get(name)

        return binding.inferred if binding is not None else None

    def get_bound_location(self, name: str) -> Span | None:
        """Where a name was bound, or `None` if it is unbound or was bound before any source existed."""

        binding = self.__variables.get(name)

        return binding.location if binding is not None else None

    def bind(self, name: str, inferred: InferredType, location: Span | None = None) -> None:
        """Bind a name to a type for the first time."""

        if name == INPUT:
            raise SemanticError(f"'{INPUT}' is reserved and cannot be bound", location)

        self.__variables[name] = Binding(inferred=inferred, location=location)
