from dataclasses import dataclass, field


@dataclass
class ReferenceProgramExecution:
    input_strings: list[str]
    output_strings: list[str]
    expect_success: bool


@dataclass
class ReferenceProgram:
    """
    One program from `docs/refs/`, which is both documentation and a test case.

    A program that cannot compile records the error it is expected to raise in place of its BlipIR and its executions, so
    `blip_ir` is `None` exactly when `compile_error` is set.

    It may also record `compile_diagnostic`: the whole message, location and caret that the error renders into. That makes
    the quality of an error message part of the test suite rather than something only noticed when someone happens to read
    it. It is optional, so a program can record the error class alone.
    """

    name: str
    blip_code: str
    blip_ir: dict | None = None
    executions: list[ReferenceProgramExecution] = field(default_factory=list)
    compile_error: str | None = None
    compile_diagnostic: str | None = None

    def expects_compile_error(self) -> bool:
        return self.compile_error is not None
