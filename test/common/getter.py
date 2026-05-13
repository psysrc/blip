from typing import Optional
from pathlib import Path
from test.common.classes import ReferenceProgram
from test.common.parser import ReferenceParser


__reference_programs: Optional[list[ReferenceProgram]] = None


def get_reference_programs() -> list[ReferenceProgram]:
    global __reference_programs
    if __reference_programs is None:
        __reference_programs = []

        ref_program_dir = Path("docs/refs")
        for ref_prog_file in ref_program_dir.glob("*.md"):
            if ref_prog_file.name == "README.md":
                continue

            markdown_text = ref_prog_file.read_text()

            found_programs = ReferenceParser(markdown_text).get_reference_programs()

            __reference_programs.extend(found_programs)

    return __reference_programs
