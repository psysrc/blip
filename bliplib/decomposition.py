"""Decomposition engine."""

import re

from bliplib.ir import DecompPattern, Identifier, PatternElement, StringLiteral, Wildcard

# Non-greedy throughout: a capture takes as little as possible, only going to the next literal rather than the last one.
_CAPTURE = "(.*?)"
_WILDCARD = ".*?"

# A Blip string may contain newlines, and a bare `.` would refuse to cross one.
FLAGS = re.DOTALL


def pattern_regex(pattern: DecompPattern) -> str:
    """Convert a decomposition pattern into a regular expression, to be used with `fullmatch` and `FLAGS`."""

    def fragment(element: PatternElement) -> str:
        match element:
            case StringLiteral():
                return re.escape(element.value)

            case Identifier():
                return _CAPTURE

            case Wildcard():
                return _WILDCARD

    return "".join(fragment(element) for element in pattern)


def pattern_captures(pattern: DecompPattern) -> list[str]:
    """The names a decomposition pattern captures, in order."""

    return [element.name for element in pattern if isinstance(element, Identifier)]


def describe_pattern(pattern: DecompPattern) -> str:
    """Render a decomposition pattern into something close to the Blip source that produced it."""

    def described(element: PatternElement) -> str:
        match element:
            case StringLiteral():
                return f'"{element.value}"'

            case Identifier():
                return element.name

            case Wildcard():
                return "*"

    return " ".join(described(element) for element in pattern)
