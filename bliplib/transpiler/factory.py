from bliplib.errors import TranspilerError
from bliplib.transpiler.interface import Transpiler
from bliplib.transpiler.python import PythonTranspiler


def get_transpiler(name: str) -> Transpiler:
    """Factory function to make a transpiler, given its name. Raises `TranspilerError` for an unknown transpiler name."""

    match name:
        case "python":
            return PythonTranspiler()
        case _:
            raise TranspilerError(f"Transpiler '{name}' does not exist")
