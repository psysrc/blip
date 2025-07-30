"""
Implements the Interpreter class.
"""

from typing import Optional


class InterpreterError(RuntimeError):
    pass


class Interpreter:
    def __init__(self, blip_ir: dict) -> None:
        self.__code = blip_ir
        self.__variables: dict[str, str | list[str]]

    def run(self, input_strings: list[str]) -> list[str]:
        self.__variables: dict[str, str | list[str]] = {}

        return self.__interpret_program(input_strings)

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
            case {
                "type": "return",
                "expression": {
                    "type": "literal",
                    "value": the_string,
                },
            }:
                return [the_string]

            case {
                "type": "return",
                "expression": {
                    "type": "identifier",
                    "name": "input",
                },
            }:
                data = self.__variables["input"]
                match data:
                    case [*items] if all(isinstance(item, str) for item in items):
                        return data
                    case _:
                        raise InterpreterError(
                            f"Failed to return 'input': Only strings and string lists can be returned ('input' is of type {type(input)})"
                        )

            case _:
                raise InterpreterError("Unexpected code")
