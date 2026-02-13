"""
Implements the Interpreter class.
"""

from typing import Optional


class InterpreterError(RuntimeError):
    pass


type BlipType = str | list[str] | int | list[int] | bool | list[bool]


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
        directives: dict = self.__code.get("directives", {})

        # Validate and assign input variables according to directives
        input_directive = directives.get("input")
        if input_directive is not None:
            self.__validate_input(input_strings, input_directive)
            if input_directive.get("names"):
                for idx, name in enumerate(input_directive["names"]):
                    self.__variables[name] = input_strings[idx]

        self.__variables["input"] = input_strings

        match self.__code:
            case {"type": "program", "statements": [*statements]}:
                for statement in statements:
                    result = self.__interpret_statement(statement)
                    if result is not None:
                        # Validate outputs according to directives before returning
                        output_dir = directives.get("output")
                        if output_dir is not None:
                            self.__validate_output(result, output_dir)

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

            case {"type": "decomposition"}:
                return self.__interpret_decomposition(statement)

            case _:
                raise InterpreterError(f"Unexpected statement '{statement}'")

    def __interpret_decomposition(self, code: dict) -> None:
        self.__ensure_code_type(code, "decomposition")

        identifier_name = code["identifier"]["name"]
        original_string = self.__variables[identifier_name]
        string = original_string

        if not isinstance(string, str):
            raise InterpreterError(f"Decomposition failure: Only strings can be decomposed (variable is of type '{type(string)}')")

        pattern: list[dict] = code["pattern"]
        current_operand_idx = 0

        while current_operand_idx < len(pattern):
            current_operand = pattern[current_operand_idx]

            match current_operand:
                case {"type": "string_literal"}:
                    op_value = current_operand["value"]
                    idx = string.find(op_value)
                    if idx == -1:
                        raise InterpreterError(
                            f"Decomposition failed: Operand '{op_value}' not found in '{identifier_name}' (which has value '{original_string}')"
                        )

                    string = string[idx + len(op_value) :]  # Skip ahead in the string to get past the first operand
                    current_operand_idx += 1

                case {"type": "identifier"}:
                    if current_operand_idx + 1 < len(pattern):
                        next_operand = pattern[current_operand_idx + 1]

                        if next_operand["type"] != "string_literal":
                            raise InterpreterError(
                                f"Decomposition semantic error: Variable was followed by something other than a string literal ({next_operand['type']})"
                            )

                        next_op_value = next_operand["value"]
                        idx = string.find(next_op_value)
                        if idx == -1:
                            raise InterpreterError(
                                f"Decomposition failed: Operand '{next_op_value}' not found in '{identifier_name}' (which has value '{original_string}')"
                            )

                        self.__variables[current_operand["name"]] = string[:idx]
                        string = string[idx + len(next_op_value) :]
                        current_operand_idx += 2

                    else:
                        self.__variables[current_operand["name"]] = string
                        current_operand_idx += 1

                case {"type": "decomposition_wildcard"}:
                    if current_operand_idx + 1 < len(pattern):
                        next_operand = pattern[current_operand_idx + 1]

                        if next_operand["type"] != "string_literal":
                            raise InterpreterError(
                                f"Decomposition semantic error: Wildcard was followed by something other than a string literal ({next_operand['type']})"
                            )

                        next_op_value = next_operand["value"]
                        idx = string.find(next_op_value)
                        if idx == -1:
                            raise InterpreterError(
                                f"Decomposition failed: Operand '{next_op_value}' not found in '{identifier_name}' (which has value '{original_string}')"
                            )

                        string = string[idx + len(next_op_value) :]
                        current_operand_idx += 2

                    else:
                        current_operand_idx += 1

                case _:
                    raise InterpreterError(f"Unexpected operand in decomposition: '{current_operand}'")

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
                return items  # type: ignore (Pylance thinks this could be a list[int], but the guard clause prevents that)
            case _:
                raise InterpreterError(f"Unexpected expression type in return statement: '{type(value)}'")

    def __interpret_expression(self, code: dict) -> BlipType:
        self.__ensure_code_type(code, "expression")

        value = code["value"]

        return self.__interpret_expression_value(value)

    def __interpret_expression_value(self, code: dict) -> BlipType:
        match code:
            case {"type": "string_literal"}:
                return self.__interpret_string_literal(code)

            case {"type": "integer_literal"}:
                return self.__interpret_integer_literal(code)

            case {"type": "boolean_literal"}:
                return self.__interpret_boolean_literal(code)

            case {"type": "identifier"}:
                return self.__interpret_identifier(code)

            case {"type": "concatenation"}:
                return self.__interpret_concatenation(code)

            case {"type": "index"}:
                return self.__interpret_indexed_expression(code)

            case {"type": "list"}:
                return self.__interpret_list(code)

            case _:
                raise InterpreterError(f"Unexpected codetype in expression value: {code}")

    def __interpret_list(self, code: dict) -> BlipType:
        self.__ensure_code_type(code, "list")

        the_list = []
        for elem in code["elements"]:
            the_list.append(self.__interpret_expression(elem))

        return the_list

    def __interpret_indexed_expression(self, code: dict) -> BlipType:
        self.__ensure_code_type(code, "index")

        variable = self.__interpret_identifier(code["identifier"])

        match idx := code["index"]:
            case {"type": "integer_literal"}:
                index = self.__interpret_integer_literal(idx)
            case {"type": "identifier"}:
                raise InterpreterError("Indexing with an identifier is not yet supported")
            case _:
                raise InterpreterError(f"Unexpected codetype in indexed expression value: {idx}")

        if not isinstance(variable, list):
            raise InterpreterError(f"Cannot index into non-list type ({type(variable)})")

        if index >= len(variable):
            raise InterpreterError(f"Index out of bounds (list has {len(variable)} elements, index is {index})")

        element = variable[index]
        return element

    def __interpret_integer_literal(self, code: dict) -> int:
        self.__ensure_code_type(code, "integer_literal")

        value = code["value"]

        if not isinstance(value, int):
            raise InterpreterError(f"Expected integer literal but value type is '{type(value)}'")

        return value

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

    def __interpret_string_literal(self, code: dict) -> str:
        self.__ensure_code_type(code, "string_literal")

        value = code["value"]

        if not isinstance(value, str):
            raise InterpreterError(f"Expected string literal but value type is '{type(value)}'")

        return value

    def __interpret_boolean_literal(self, code: dict) -> bool:
        self.__ensure_code_type(code, "boolean_literal")

        value = code["value"]

        if not isinstance(value, bool):
            raise InterpreterError(f"Expected boolean literal but value type is '{type(value)}'")

        return value

    def __validate_input(self, inputs: list[str], directive: dict) -> None:
        dtype = directive.get("type")

        if dtype == "fixed":
            expected = directive.get("value")
            if len(inputs) != expected:
                raise InterpreterError(f"Input directive expects {expected} inputs, got {len(inputs)}")

        elif dtype == "range":
            mn = directive.get("min")
            mx = directive.get("max")
            if mn is not None and len(inputs) < mn:
                raise InterpreterError(f"Input directive expects at least {mn} inputs, got {len(inputs)}")
            if mx is not None and len(inputs) > mx:
                raise InterpreterError(f"Input directive expects at most {mx} inputs, got {len(inputs)}")

        else:
            raise InterpreterError(f"Unknown input directive type: {dtype}")

    def __validate_output(self, outputs: list[str], directive: dict) -> None:
        dtype = directive.get("type")

        if dtype == "fixed":
            expected = directive.get("value")
            if len(outputs) != expected:
                raise InterpreterError(f"Output directive expects {expected} outputs, got {len(outputs)}")

        elif dtype == "range":
            mn = directive.get("min")
            mx = directive.get("max")
            if mn is not None and len(outputs) < mn:
                raise InterpreterError(f"Output directive expects at least {mn} outputs, got {len(outputs)}")
            if mx is not None and len(outputs) > mx:
                raise InterpreterError(f"Output directive expects at most {mx} outputs, got {len(outputs)}")

        else:
            raise InterpreterError(f"Unknown output directive type: {dtype}")

    def __interpret_identifier(self, code: dict) -> BlipType:
        self.__ensure_code_type(code, "identifier")

        name = code["name"]

        if name not in self.__variables:
            raise InterpreterError(f"Identifier '{name}' does not exist")

        return self.__variables[name]
