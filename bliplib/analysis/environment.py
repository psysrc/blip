"""
Implements the environment: the variables in scope and the type each one has.
"""

from collections.abc import Generator
from contextlib import contextmanager
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
    A stack of scopes, innermost last.

    A lookup searches outwards from the innermost scope, and a new name is bound in the innermost one. The two together are
    what makes a block's bindings local to it: a name the block invents is popped with the block, while a name that already
    existed is found in an outer scope and so is never shadowed by a new binding.

    The outermost scope is the program's own, and holds `input` from the start.
    """

    def __init__(self):
        self.__scopes: list[dict[str, Binding]] = [{INPUT: Binding(inferred=List(Scalar.STRING))}]

    @contextmanager
    def child_scope(self) -> Generator[dict[str, Binding], None, None]:
        """
        Open a scope for the duration of the block, and yield the mapping its own bindings land in.

        The mapping outlives the scope on purpose: an `if` has to ask what each of its branches bound *after* that branch has
        been analysed, to decide which of those names survive the join. Popping the scope only takes it out of the search
        path; it does not empty what was collected.
        """

        scope: dict[str, Binding] = {}
        self.__scopes.append(scope)

        try:
            yield scope

        finally:
            self.__scopes.pop()

    def lookup(self, name: str, location: Span | None = None) -> InferredType:
        """Return the type bound to a name, or raise if the name is not bound. `location` is where the name was used."""

        binding = self.get_binding(name)

        if binding is None:
            raise SemanticError(f"'{name}' is used but never bound", location)

        return binding.inferred

    def get_binding(self, name: str) -> Binding | None:
        """What a name is bound to and where, searching outwards from the innermost scope. `None` if it is not bound."""

        for scope in reversed(self.__scopes):
            binding = scope.get(name)

            if binding is not None:
                return binding

        return None

    def bind(self, name: str, inferred: InferredType, location: Span | None = None) -> None:
        """Bind a name to a type in the innermost scope, for the first time."""

        if name == INPUT:
            raise SemanticError(f"'{INPUT}' is reserved and cannot be bound", location)

        self.__scopes[-1][name] = Binding(inferred=inferred, location=location)
