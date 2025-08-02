"""
Implements the Interpreter class.
"""

from typing import Optional


class InterpreterError(RuntimeError):
    pass


type BlipType = str | list[str]


class Interpreter:
    def __init__(self, blip_ir: dict) -> None:
        self.__code = blip_ir
        self.__variables: dict[str, BlipType]

    def run(self, input_strings: list[str]) -> list[str]:
        self.__variables = {}

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

            case {"type": "assignment"}:
                return self.__interpret_assignment(statement)

            case _:
                raise InterpreterError(f"Unexpected statement '{statement}'")

    def __interpret_assignment(self, code: dict) -> None:
        self.__ensure_code_type(code, "assignment")

        variable_name: str = code["identifier"]["name"]
        expression = code["expression"]

        value: BlipType = self.__interpret_expression(expression)

        self.__variables[variable_name] = value

    def __interpret_return(self, code: dict) -> list[str]:
        self.__ensure_code_type(code, "return")

        expression: dict = code["expression"]
        value: BlipType = self.__interpret_expression(expression)

        match value:
            case string if isinstance(string, str):
                return [string]
            case [*items] if all(isinstance(item, str) for item in items):
                return items
            case _:
                raise InterpreterError(f"Unexpected expression type in return statement: '{type(value)}'")

    def __interpret_expression(self, code: dict) -> BlipType:
        self.__ensure_code_type(code, "expression")

        value = code["value"]

        return self.__interpret_expression_value(value)

    def __interpret_expression_value(self, code: dict) -> BlipType:
        match code:
            case {"type": "string_literal"}:
                return self.__interpret_literal(code)

            case {"type": "identifier"}:
                return self.__interpret_identifier(code)

            case {"type": "concatenation"}:
                return self.__interpret_concatenation(code)

            case _:
                raise InterpreterError(f"Unexpected codetype in expression value: {code}")

    def __interpret_concatenation(self, code: dict) -> str:
        self.__ensure_code_type(code, "concatenation")

        string = ""

        for operand_code in code["operands"]:
            operand_value = self.__interpret_expression_value(operand_code)

            if isinstance(operand_value, str):
                string += operand_value
            else:
                raise InterpreterError(f"Unexpected type in string concatenation: {type(operand_value)}")

        return string

    def __interpret_literal(self, code: dict) -> str:
        self.__ensure_code_type(code, "string_literal")

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
