class BlipError(RuntimeError):
    """Generic error class for all Blip-related errors."""


class TokenizerError(BlipError):
    """An error emitted by the Blip tokenizer."""


class ParserError(BlipError):
    """An error emitted by the Blip parser."""


class InterpreterError(BlipError):
    """An error emitted by the Blip interpreter."""
