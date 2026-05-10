from bliplib.transpiler.interface import Transpiler


class PythonTranspiler(Transpiler):
    def transpile_function(self, blip_ir: dict) -> str:
        raise NotImplementedError("Python function transpiling")

    def transpile_program(self, blip_ir: dict) -> str:
        raise NotImplementedError("Python program transpiling")
