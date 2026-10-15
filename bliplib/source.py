"""
Source positions, and how a diagnostic is rendered from one.

A `Span` is a slice of the source text: an offset and a length, with no line or column in it. Offsets are the primitive
because the tokenizer needs one anyway in order to walk the source, and counting lines as it went would be more state to
keep right - which is exactly where an off-by-one hides.

Line and column are therefore *derived*, by `SourceMap`, which is the only thing here that holds the source text. That is
also why rendering lives in this module rather than in the CLI: a diagnostic is a function of a span and the text it points
into, and a function of two arguments is far easier to test than a branch of `main()`.

Spans are deliberately absent from serialised BlipIR. A `.blipir` is a portable artifact, so an offset stored in one points
into a `.blip` that may have been edited since, may not have been shipped alongside it, or may never have existed. An
absent location is honest; a stale one is confidently wrong.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    """A slice of the source text."""

    offset: int
    length: int

    @property
    def end(self) -> int:
        return self.offset + self.length

    def covering(self, other: Span) -> Span:
        """Create a new span that spans this span and the other span."""

        start = min(self.offset, other.offset)
        end = max(self.end, other.end)
        length = end - start

        return Span(offset=start, length=length)


@dataclass(frozen=True)
class Note:
    """
    A second place worth pointing at, with a line saying why it matters.

    A type conflict is a disagreement between two places, and naming only one of them leaves the reader to find the other.
    The note travels as a *span* rather than as text because the analyser, which raises these, has no source to turn an
    offset into a line and column with - that is the CLI's job, and this is what gets it there.
    """

    location: Span
    message: str


class SourceMap:
    """
    A source text, together with the index needed to turn an offset into a line and column.

    The offsets at which lines start are found once, at construction, so each lookup is a binary search rather than a scan
    of the whole file. Lines and columns are 1-based, because that is what an editor shows and what every other compiler
    prints.
    """

    def __init__(self, source: str, path: str = "<stdin>"):
        self.__source = source
        self.__path = path

        # Where each line begins. Line 1 begins at 0, and every newline begins the line after it.
        self.__line_starts = [0, *[offset + 1 for offset, character in enumerate(source) if character == "\n"]]

    @property
    def path(self) -> str:
        return self.__path

    def get_line_column(self, offset: int) -> tuple[int, int]:
        """Get a (line, column) tuple of an offset into the source."""

        # `bisect_right` gives the number of line starts at or before this offset, which is the 1-based line number
        line = bisect_right(self.__line_starts, offset)

        return line, offset - self.__line_starts[line - 1] + 1

    def get_line_text(self, line_number: int) -> str:
        """Get the line text from a line number, excluding its terminating newline character(s)."""

        start = self.__line_starts[line_number - 1]

        # The next line begins one past this line's newline, so the newline itself is the character before it
        if line_number < len(self.__line_starts):
            end = self.__line_starts[line_number] - 1
        else:
            end = len(self.__source)

        # A CRLF source leaves the carriage return behind, and it would print as a stray column
        return self.__source[start:end].rstrip("\r")

    def describe(self, span: Span) -> str:
        """A span as `line:column`, for naming a second site inside a message rather than pointing at it."""

        line, column = self.get_line_column(span.offset)

        return f"{line}:{column}"

    def render(self, message: str, span: Span | None, error_type: str = "error") -> str:
        """
        Render a full diagnostic: a located headline, then the offending line with a caret under the span.

        A `None` span still produces the headline, so an error that cannot say where it happened - one from a loaded
        `.blipir`, which carries no spans - degrades to naming the file rather than to a bare string.
        """

        if span is None:
            return f"{self.__path}: {error_type}: {message}"

        line, column = self.get_line_column(span.offset)
        text = self.get_line_text(line)

        # The caret stays on the span's own line: underlining half of a construct is clearer than running off the end of
        # the line and having to explain what the rest of the carets meant. A zero-length span still gets one caret.
        caret_width = max(1, min(span.length, len(text) - column + 1))

        gutter = " " * len(str(line))

        return "\n".join(
            [
                f"{self.__path}:{line}:{column}: {error_type}: {message}",
                f"{gutter} |",
                f"{line} | {text}",
                f"{gutter} | {' ' * (column - 1)}{'^' * caret_width}",
            ]
        )
