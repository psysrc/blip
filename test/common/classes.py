from dataclasses import dataclass


@dataclass
class ReferenceProgramExecution:
    input_strings: list[str]
    output_strings: list[str]
    expect_success: bool


@dataclass
class ReferenceProgram:
    name: str
    blip_code: str
    blip_ir: dict
    executions: list[ReferenceProgramExecution]
