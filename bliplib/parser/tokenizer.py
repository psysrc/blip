"""
Implements the Tokenizer class.
"""

import re
from dataclasses import dataclass, field

from bliplib.errors import TokenizerError
from bliplib.source import Span

# Patterns are tried in order and the first match wins, so a keyword has to come before the identifier pattern that would
# match it too. `\n` is an `EOL` rather than trivia, so the trivia pattern excludes it outright rather than relying on being
# tried second: it is greedy, and a run of spaces beginning before a newline would otherwise swallow the newline with them.
#
# A token type of `None` is trivia: the match advances the offset but yields no token. This is for whitespace and comments.
_TOKEN_PATTERNS: tuple[tuple[re.Pattern[str], str | None], ...] = tuple(
    (re.compile(pattern), token_type)
    for pattern, token_type in (
        (r"#.*", None),  # Single-line comments (ignore)
        (r"//.*", None),  # Single-line comments (ignore)
        (r"\n", "EOL"),
        (r";", "EOL"),
        (r"[^\S\n]+", None),  # Non-EOL Whitespace (ignore)
        (r"->", "->"),
        (r"<-", "<-"),
        (r"=", "="),
        (r"\*", "*"),
        (r"\|", "|"),
        (r"\[", "["),
        (r"\]", "]"),
        (r"\{", "{"),
        (r"\}", "}"),
        (r",", ","),
        (r"!in\b", "DIRECTIVE_IN"),
        (r"!out\b", "DIRECTIVE_OUT"),
        (r"\.\.", ".."),
        (r"ret\b", "RETURN"),
        (r"if\b", "IF"),
        (r"else\b", "ELSE"),
        (r"true\b", "BOOLEAN_LITERAL"),
        (r"false\b", "BOOLEAN_LITERAL"),
        (r'"[^"]*"', "STRING_LITERAL"),
        (r"'[^']*'", "STRING_LITERAL"),
        (r"[0-9]+", "INTEGER_LITERAL"),
        (r"[a-zA-Z][a-zA-Z0-9_]*\b", "IDENTIFIER"),
    )
)

# How much of the remaining source to quote when nothing matches. Enough to recognise, short enough to read.
_UNKNOWN_SYNTAX_CONTEXT = 10


@dataclass
class Token:
    type: str
    value: str

    location: Span = field(kw_only=True, compare=False, repr=False)

    def __str__(self) -> str:
        escaped_value = self.value.replace("\n", "\\n").replace("\r", "\\r")
        return f"{self.type}['{escaped_value}']"


class Tokenizer:
    """
    The Blip Tokenizer.

    Performs lexical analysis of the input DSL to produce a stream of tokens.
    The tokens can then be parsed by the `Parser` class.
    """

    def __init__(self, source: str):
        self.__source = source
        self.__offset = 0

        self.__current_token = self.__get_next_token_from_stream()

    def next_token(self) -> Token:
        """
        Return the next token in the source stream.

        If `end_of_stream() == True`, a sentinel `EOF` token is returned.

        If no valid token can be found, a TokenizerError is raised.
        """

        token_to_return = self.__current_token

        self.__current_token = self.__get_next_token_from_stream()

        return token_to_return

    def __get_next_token_from_stream(self) -> Token:
        """Scan up to the next real token."""

        while not self.__source_is_exhausted():
            token = self.__scan_one()

            if token is not None:
                return token

        return Token(type="EOF", value="", location=Span(offset=self.__offset, length=0))

    def __scan_one(self) -> Token | None:
        """Consume the next pattern, return its token or `None` if it was trivia (comments/whitespace), and advance the offset."""

        for pattern, token_type in _TOKEN_PATTERNS:
            match = pattern.match(self.__source, self.__offset)

            if match is None:
                continue

            token_value = match.group()
            start = self.__offset
            self.__offset += len(token_value)

            if token_type is None:
                return None

            return Token(type=token_type, value=token_value, location=Span(offset=start, length=len(token_value)))

        unknown = self.__source[self.__offset : self.__offset + _UNKNOWN_SYNTAX_CONTEXT].partition("\n")[0]
        raise TokenizerError(f"Unknown syntax near characters '{unknown}'", Span(offset=self.__offset, length=len(unknown)))

    def __source_is_exhausted(self) -> bool:
        return self.__offset >= len(self.__source)
