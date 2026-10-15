from bliplib.source import Span


class BlipError(RuntimeError):
    """
    Generic error class for all Blip-related errors.

    `location` marks where in the source code the error is, where applicable.
    """

    def __init__(self, message: str, location: Span | None = None) -> None:
        super().__init__(message)

        self.location = location


class TokenizerError(BlipError):
    """Error during tokenization of Blip source code."""


class ParserError(BlipError):
    """Error while parsing Blip source code into BlipIR."""


class IRError(BlipError):
    """Malformed BlipIR."""


class SemanticError(BlipError):
    """Error during static analysis of BlipIR (the Blip program is not well-formed)."""


class InterpreterError(BlipError):
    """Error while interpreting a Blip program."""


class TranspilerError(BlipError):
    """Error during transpilation of Blip into a target language."""
