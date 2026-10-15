"""
Implements the Tokenizer class.
"""

import re
from dataclasses import dataclass, field

from bliplib.errors import TokenizerError
from bliplib.source import Span

# Patterns are tried in order and the first match wins, so a keyword has to come before the identifier pattern that would
# match it too, and `\n` has to come before the whitespace pattern that would swallow it.
#
# None of them is `^`-anchored, which is load-bearing rather than tidiness. They are matched with `pattern.match(source,
# offset)` against the whole source instead of against a slice of what is left, and `^` only matches at a real line start -
# so an anchored pattern fails at every non-zero offset, with or without `re.MULTILINE`. `match()` anchors at the offset by
# definition, and leaves the rest of the string visible, which is what lets a trailing `\b` still see what follows it.
#
# A token type of `None` marks trivia: the match advances the offset and yields no token.
_TOKEN_PATTERNS: tuple[tuple[re.Pattern[str], str | None], ...] = tuple(
    (re.compile(pattern), token_type)
    for pattern, token_type in (
        (r"#.*", None),  # Single-line comments (ignore)
        (r"//.*", None),  # Single-line comments (ignore)
        (r"\n", "EOL"),
        (r";", "EOL"),
        (r"\s", None),  # Non-EOL Whitespace (ignore)
        (r"->", "->"),
        (r"<-", "<-"),
        (r"=", "="),
        (r"\*", "*"),
        (r"\|", "|"),
        (r"\[", "["),
        (r"\]", "]"),
        (r",", ","),
        (r"!in\b", "DIRECTIVE_IN"),
        (r"!out\b", "DIRECTIVE_OUT"),
        (r"\.\.", ".."),
        (r"ret\b", "RETURN"),
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
        if self.__source_is_exhausted():
            return Token(type="EOF", value="", location=Span(offset=self.__offset, length=0))

        for pattern, token_type in _TOKEN_PATTERNS:
            match = pattern.match(self.__source, self.__offset)

            if match:
                token_value = match.group()
                start = self.__offset
                self.__offset += len(token_value)

                if token_type:
                    return Token(type=token_type, value=token_value, location=Span(offset=start, length=len(token_value)))

                return self.__get_next_token_from_stream()

        unknown = self.__source[self.__offset : self.__offset + _UNKNOWN_SYNTAX_CONTEXT].partition("\n")[0]
        raise TokenizerError(f"Unknown syntax near characters '{unknown}'", Span(offset=self.__offset, length=len(unknown)))

    def __source_is_exhausted(self) -> bool:
        return self.__offset >= len(self.__source)
