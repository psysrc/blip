"""
Implements the types that inference needs and serialisation must never see.

A `Var` is a hole: a type that is not yet determined. `[]` is "a list of something", which is `List(Var)` until the way the
program uses the list says what that something is.

Holes live here rather than in `bliplib/ir/` on purpose. `BlipType` is `Scalar | List[BlipType]`, so a `Var` cannot be assigned
to a value node's `blip_type` and cannot be reached by the serialisation codec - not by convention, but because the type checker
rejects it.
"""

from dataclasses import dataclass

from bliplib.ir.types import List, Scalar


@dataclass(frozen=True)
class Var:
    """
    A hole in a type.

    Frozen, because a hole never changes: what changes is the `Unifier`'s record of what it stands for. Identity is the `id`
    alone, so two holes are the same hole only if they were the same hole to begin with.
    """

    id: int


# A type part-way through inference, which may still contain holes at any depth.
# Note the similarity between this `InferredType` and `BlipType` (in `bliplib/ir/types.py`)
type InferredType = Scalar | List[InferredType] | Var


def describe_inferred_type(inferred: InferredType) -> str:
    """
    Render the `InferredType` into a human-friendly string.

    This must not be mistaken for the serialisation codec: this will render `Var` holes, which BlipIR can never contain,
    and is subject to change in future. The codec in `bliplib/ir/` is the one with a strict serialisation format to honour.
    """

    match inferred:
        case Scalar():
            return str(inferred)
        case List(element=element):
            return f"list[{describe_inferred_type(element)}]"
        case Var(id=hole):
            return f"?{hole}"
