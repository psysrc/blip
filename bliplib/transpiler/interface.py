import abc


class Transpiler(abc.ABC):
    @abc.abstractmethod
    def transpile_function(self, blip_ir: dict) -> str:
        pass

    @abc.abstractmethod
    def transpile_program(self, blip_ir: dict) -> str:
        pass
