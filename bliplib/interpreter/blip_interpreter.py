"""
Implements the Interpreter class.
"""

from typing import Optional


class InterpreterError(RuntimeError):
    pass


type BlipType = str | list[str] | int


class Interpreter:
    def __init__(self, blip_ir: dict) -> None:
        self.__code = blip_ir
        self.__variables: dict[str, str | list[str]]

    def run(self, input_strings: list[str]) -> list[str]:
        self.__variables: dict[str, str | list[str]] = {}

        return self.__interpret_program(input_strings)

    def __ensure_code_type(self, code: dict, code_type: str):
        if code["type"] != code_type:
            raise InterpreterError(f"Expected code type '{code_type}' but got '{code['type']}'")

    def __interpret_program(self, input_strings: list[str]) -> list[str]:
        self.__variables["input"] = input_strings

        match self.__code:
            case {"type": "program", "statements": [*statements]}:
                for statement in statements:
                    result = self.__interpret_statement(statement)
                    if result is not None:
                        return result

            case _:
                raise InterpreterError("Unexpected program code")

        raise InterpreterError("Program halted without returning a value")

    def __interpret_statement(self, statement: dict) -> Optional[list[str]]:
        match statement:
            case {"type": "return"}:
                return self.__interpret_return(statement)

            case _:
                raise InterpreterError(f"Unexpected statement '{statement}'")

    def __interpret_return(self, code: dict) -> list[str]:
        self.__ensure_code_type(code, "return")

        expression = code["expression"]
        match expression:
            case {"type": "literal"}:
                return [self.__interpret_literal(expression)]

            case {"type": "identifier"}:
                data = self.__interpret_identifier(expression)

                match data:
                    case string if isinstance(string, str):
                        return [string]
                    case [*items] if all(isinstance(item, str) for item in items):
                        return data
                    case _:
                        raise InterpreterError(f"Unexpected expression type in return statement: '{type(data)}'")

            case _:
                raise InterpreterError(f"Unexpected expression in return statement '{expression}'")

    def __interpret_literal(self, code: dict) -> str:
        self.__ensure_code_type(code, "literal")

        value = code["value"]

        if not isinstance(value, str):
            raise InterpreterError(f"Expected string literal but value type is '{type(value)}'")

        return value

    def __interpret_identifier(self, code: dict) -> BlipType:
        self.__ensure_code_type(code, "identifier")

        name = code["name"]

        if name not in self.__variables:
            raise InterpreterError(f"Identifier '{name}' does not exist")

        return self.__variables[name]
