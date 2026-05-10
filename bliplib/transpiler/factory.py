from bliplib.transpiler.interface import Transpiler
from bliplib.transpiler.python import PythonTranspiler


def get_transpiler(name: str) -> Transpiler:
    match name:
        case "python":
            return PythonTranspiler()
        case _:
            err = f"Transpiler '{name}' does not exist"
            raise RuntimeError(err)
