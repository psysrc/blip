"""
Implements the environment: the variables in scope and the type each one has.
"""

from bliplib.analysis.types import InferredType
from bliplib.errors import SemanticError
from bliplib.ir.types import List, Scalar

# The built-in variable holding the program's input strings. It is always bound, and binding it again is an error.
INPUT = "input"


class Environment:
    """
    A single flat scope.

    Blip has no block constructs implemented yet, so one global scope is all that is needed. The analysis design settles how `if`,
    loops and conditional decomposition will bind names when they land, which is why this is a class rather than a bare dict:
    adding a scope stack later should preferably not disturb its callers.
    """

    def __init__(self):
        self.__variables: dict[str, InferredType] = {INPUT: List(Scalar.STRING)}

    def lookup(self, name: str) -> InferredType:
        """Return the type bound to a name, or raise if the name is not bound."""

        if name not in self.__variables:
            raise SemanticError(f"'{name}' is used but never bound")

        return self.__variables[name]

    def get_bound_type(self, name: str) -> InferredType | None:
        """Return the type bound to a name, or `None` if it is not bound. Does not raise."""

        return self.__variables.get(name)

    def bind(self, name: str, inferred: InferredType) -> None:
        """Bind a name to a type for the first time."""

        if name == INPUT:
            raise SemanticError(f"'{INPUT}' is reserved and cannot be bound")

        self.__variables[name] = inferred
