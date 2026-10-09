import abc

from bliplib.ir import Program


class Transpiler(abc.ABC):
    """Transpiles a Blip program into source code in another language."""

    @abc.abstractmethod
    def transpile_function(self, program: Program) -> str:
        pass

    @abc.abstractmethod
    def transpile_program(self, program: Program) -> str:
        pass
