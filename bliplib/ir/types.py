"""
Implements the Blip type model.

These are the types a Blip value can have, and the only types a `.blipir` file can express.

Inference needs one more - a hole standing for a type that is not yet known - and that deliberately lives in `bliplib/analysis/`
instead. `List` is generic and frozen, which makes its parameter covariant, so a list containing a hole is not assignable to a
`BlipType`. An unresolved hole reaching a serialised IR is therefore a type error, rather than something to remember not to do.
"""

from dataclasses import dataclass
from enum import StrEnum


class Scalar(StrEnum):
    """
    A type with no structure.

    Each member's value is also its serialised form, so this enum is the whole of the scalar codec in both directions.
    """

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"


@dataclass(frozen=True)
class List[T]:
    """
    A homogeneous list.

    Generic in its element type so that one class serves both the ground model here and the inference model in
    `bliplib/analysis/`, rather than there being two list classes to keep in step.
    """

    element: T


# The types a `.blipir` can express. Recursive, so a nested list is nameable.
type BlipType = Scalar | List[BlipType]
