from bliplib.transpiler.interface import Transpiler


def get_transpiler(name: str) -> Transpiler:
    match name:
        case _:
            err = f"Transpiler '{name}' does not exist"
            raise RuntimeError(err)
