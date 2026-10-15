"""
These are the BlipIR unit tests for the reference programs in the `docs/refs/` directory.

This ensures the Blip code parses, loads and analyses into the BlipIR each program records. It is a parse-*and*-analyse test:
the `#### Blip IR` blocks carry type annotations, so producing them needs the analyser as well as the parser.

Programs with a `#### Compilation` section are checked the other way round: they must raise the error they record.
"""

import pytest

from bliplib.analysis import analyse
from bliplib.errors import BlipError, ParserError, SemanticError
from bliplib.ir import Program
from bliplib.parser import Parser
from bliplib.source import SourceMap
from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.getter import get_compiling_reference_programs, get_failing_reference_programs

# The errors a `#### Compilation` section may name. A program that fails to compile fails in one of these two ways.
COMPILE_ERRORS: dict[str, type[BlipError]] = {
    "ParserError": ParserError,
    "SemanticError": SemanticError,
}


def compile_program(blip_code: str) -> Program:
    """Run the whole front end: parse, load and analyse."""

    return analyse(Parser().parse(blip_code))


@pytest.mark.parametrize("ref", get_compiling_reference_programs())
def test_reference_program_ir(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, test that the Blip code becomes the correct annotated BlipIR."""

    try:
        program = compile_program(ref.blip_code)
    except BlipError as err:
        pytest.fail(reason=f"Program reference '{ref.name}': Failed to compile: {type(err).__name__}: {err}")

    assert program.to_dict() == ref.blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"


@pytest.mark.parametrize("ref", get_failing_reference_programs())
def test_reference_program_fails_to_compile(ref: ReferenceProgram):
    """Given a `ReferenceProgram` with a `#### Compilation` section, test that it raises the error it records."""

    assert ref.compile_error in COMPILE_ERRORS, (
        f"Program reference '{ref.name}': '{ref.compile_error}' is not a known compile error, expected one of {sorted(COMPILE_ERRORS)}"
    )

    with pytest.raises(COMPILE_ERRORS[ref.compile_error]):
        compile_program(ref.blip_code)


# How each compile error is labelled in a diagnostic, matching what the CLI prints for it.
ERROR_TYPES: dict[str, str] = {
    "ParserError": "parser error",
    "SemanticError": "semantic error",
}


@pytest.mark.parametrize("ref", get_failing_reference_programs())
def test_reference_program_renders_the_diagnostic_it_records(ref: ReferenceProgram):
    """A program that records a diagnostic must render exactly that diagnostic, carets and notes included."""

    if ref.compile_diagnostic is None:
        return  # Gracefully pass the test

    with pytest.raises(BlipError) as raised:
        compile_program(ref.blip_code)

    err = raised.value
    error_type = ERROR_TYPES.get(ref.compile_error, "error")
    rendered = SourceMap(ref.blip_code, path="<stdin>").render_diagnostic(str(err), err.location, err.notes, error_type)

    assert rendered == ref.compile_diagnostic, f"Program reference '{ref.name}': diagnostic does not match the one recorded"
