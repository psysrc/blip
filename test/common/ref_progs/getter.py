from pathlib import Path

from test.common.ref_progs.classes import ReferenceProgram
from test.common.ref_progs.parser import ReferenceParser

REF_PROGRAM_DIR = Path("docs/refs")

__reference_programs: list[ReferenceProgram] | None = None


def get_reference_program_files() -> list[Path]:
    """The markdown files holding reference programs."""

    return sorted(path for path in REF_PROGRAM_DIR.glob("*.md") if path.name != "README.md")


def get_reference_programs() -> list[ReferenceProgram]:
    global __reference_programs
    if __reference_programs is None:
        __reference_programs = []

        for ref_prog_file in get_reference_program_files():
            markdown_text = ref_prog_file.read_text()

            found_programs = ReferenceParser(markdown_text).get_reference_programs()

            __reference_programs.extend(found_programs)

    return __reference_programs


def get_compiling_reference_programs() -> list[ReferenceProgram]:
    """The reference programs that are expected to compile, so they have BlipIR and executions to check."""

    return [ref for ref in get_reference_programs() if not ref.expects_compile_error()]


def get_failing_reference_programs() -> list[ReferenceProgram]:
    """The reference programs that are expected to be rejected before they run, so there is nothing to execute."""

    return [ref for ref in get_reference_programs() if ref.expects_compile_error()]
