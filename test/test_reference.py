import pytest
from bliplib.parser import Parser
from bliplib.interpreter import Interpreter, InterpreterError
from test.reference_parser import ReferenceParser
from test.reference_program import ReferenceProgram


def __test_reference_program(ref: ReferenceProgram):
    """Given a `ReferenceProgram`, perform all necessary testing."""

    parser = Parser(ref.blip_code)
    blip_ir = parser.parse()

    assert blip_ir == ref.blip_ir, f"Program reference '{ref.name}': Incorrect Blip IR"

    interpreter = Interpreter(blip_ir)

    for i, exec in enumerate(ref.executions):
        if exec.success:
            try:
                output = interpreter.run(exec.input_strings)
            except InterpreterError as err:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: {err}")
            else:
                assert output == exec.output_strings, f"Program reference '{ref.name}': Execution #{i + 1}: Incorrect program output"

        else:
            try:
                output = interpreter.run(exec.input_strings)
            except InterpreterError:
                pass
            else:
                pytest.fail(f"Program reference '{ref.name}': Execution #{i + 1}: Did not throw error, output was {output}")


def test_references():
    with open("test/reference.md") as file:
        markdown_text = file.read()

    reference_programs = ReferenceParser(markdown_text).get_reference_programs()

    for prog in reference_programs:
        __test_reference_program(prog)
