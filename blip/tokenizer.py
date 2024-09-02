"""
Implements the Tokenizer class.
"""

import logging
import re
from dataclasses import dataclass


@dataclass
class Token:
    type: str
    value: str

    def __str__(self) -> str:
        return f"{self.type}[{self.value}]"


class TokenizerError(RuntimeError):
    pass


class Tokenizer:
    """
    The BLiP Tokenizer.

    Performs lexical analysis of the input DSL to produce a stream of tokens.
    The tokens can then be parsed by the `Parser` class.
    """

    def __init__(self, source: str):
        self.source = source
        logging.debug("Tokenizer initialised")

        self.current_token = self.__get_next_token_from_stream()

    def next_token(self) -> Token:
        """
        Return the next token in the source stream.

        If `end_of_stream() == True`, a sentinel `EOF` token is returned.

        If no valid token can be found, a SyntaxError is raised.
        """

        token_to_return = self.current_token

        self.current_token = self.__get_next_token_from_stream()

        return token_to_return

    def __get_next_token_from_stream(self) -> Token:
        token_regexes = {
            r"^\s": None,  # Whitespace (ignore)
            r"^//.*": None,  # Single-line comments (ignore)
            r"^IN\b": "IN",
            r"^OUT\b": "OUT",
            r"^->": "->",
            r"^<-": "<-",
            r"^:=": ":=",
            r"^\|": "|",
            r'^"[^"]*"': "LITERAL",
            r"^[a-z][a-z0-9_]*\b": "IDENTIFIER",
        }

        if self.__source_is_empty():
            return Token(type="EOF", value="")

        for regexp, token_type in token_regexes.items():
            match = re.search(regexp, self.source)

            if match:
                token_value = match.group()
                self.source = self.source[len(token_value) :]

                if token_type:
                    logging.debug("Tokenizer matched token '%s' of type '%s'", token_value, token_type)

                    return Token(type=token_type, value=token_value)

                return self.__get_next_token_from_stream()

        raise TokenizerError(f"Unknown syntax near characters '{self.source[:10]}'")

    def end_of_stream(self) -> bool:
        """Returns whether the end of the stream has been reached."""

        return self.current_token.type == "EOF"

    def __source_is_empty(self) -> bool:
        return not bool(self.source)
