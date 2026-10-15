"""Unit tests for the Blip error hierarchy."""

import pytest

from bliplib.errors import BlipError, InterpreterError, IRError, ParserError, SemanticError, TokenizerError, TranspilerError
from bliplib.source import Span

_ERROR_TYPES = [TokenizerError, ParserError, IRError, SemanticError, InterpreterError, TranspilerError]


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_str_is_the_message_alone_even_when_a_span_is_carried(error_type: type[BlipError]):
    assert str(error_type("something went wrong", Span(offset=4, length=2))) == "something went wrong"


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_a_span_is_optional(error_type: type[BlipError]):
    assert error_type("something went wrong").location is None


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_every_error_is_a_blip_error(error_type: type[BlipError]):
    assert issubclass(error_type, BlipError)


def test_a_carried_span_is_readable_by_the_caller():
    span = Span(offset=4, length=2)

    assert SemanticError("nope", span).location == span
