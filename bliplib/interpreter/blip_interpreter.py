"""
Implements the Interpreter class.
"""

import re
from collections.abc import Sequence

from bliplib.decomposition import FLAGS, describe_pattern, pattern_regex
from bliplib.errors import InterpreterError
from bliplib.ir import (
    Assignment,
    BooleanLiteral,
    Concatenation,
    Condition,
    Decomposition,
    DecompPattern,
    DecompTest,
    Directive,
    FixedDirective,
    Identifier,
    If,
    Index,
    IntegerLiteral,
    ListLiteral,
    Program,
    RangeDirective,
    Return,
    Statement,
    StringLiteral,
    Value,
)
from bliplib.ir.types import List, Scalar

# A value a Blip program can hold while it runs. Recursive, because a list's elements are themselves values - which is what the
# analyser's type model says too. Not to be confused with `bliplib.ir.types.BlipType`: that is a Blip *type*, this is a value.
type BlipValue = str | int | bool | list[BlipValue]

# The built-in holding the program's input strings
INPUT = "input"


def _as_string(value: BlipValue) -> str:
    """
    Narrow a value the analyser has already typed as a string.

    Analysis has run by the time a program is interpreted, so this cannot fail on a program that got here legitimately. It is
    an assertion rather than a raise for exactly that reason: there is no error for a caller to handle, only a broken promise.
    """

    if not isinstance(value, str):
        raise InterpreterError(f"Expected a string, but got {type(value).__name__}")

    return value


class Interpreter:
    """Executes a Blip program."""

    def __init__(self, program: Program) -> None:
        self.__program = program
        self.__variables: dict[str, BlipValue] = {}

    def run(self, input_strings: list[str]) -> list[str]:
        self.__variables = {}

        return self.__interpret_program(input_strings)

    def __interpret_program(self, input_strings: list[str]) -> list[str]:
        directives = self.__program.directives

        if directives is not None and directives.input is not None:
            self.__validate_program_input(input_strings, directives.input)
            self.__bind_input_names(input_strings, directives.input)

        inputs: list[BlipValue] = [*input_strings]
        self.__variables[INPUT] = inputs

        result = self.__interpret_block(self.__program.statements)

        if result is None:
            raise InterpreterError("Program halted without returning a value")

        if directives is not None and directives.output is not None:
            self.__validate_program_output(result, directives.output)

        return result

    def __interpret_block(self, statements: Sequence[Statement]) -> list[str] | None:
        """
        Run statements until one of them returns, and hand that result straight back.

        `None` means the block ran to its end without returning. A `ret` inside a block ends the whole program rather than
        just the block, so the result has to travel all the way out - which is what every caller passing it upwards does.
        """

        for statement in statements:
            result = self.__interpret_statement(statement)

            if result is not None:
                return result

        return None

    def __validate_program_input(self, inputs: list[str], directive: Directive) -> None:
        try:
            self.__validate_strings_against_directive(inputs, directive)
        except InterpreterError as err:
            raise InterpreterError(f"Program input validation failed: {err}") from err

    def __validate_program_output(self, outputs: list[str], directive: Directive) -> None:
        try:
            self.__validate_strings_against_directive(outputs, directive)
        except InterpreterError as err:
            raise InterpreterError(f"Program output validation failed: {err}") from err

    def __bind_input_names(self, input_strings: list[str], directive: Directive) -> None:
        """A named input directive gives each input string a name. A counted or ranged one names nothing."""

        match directive:
            case FixedDirective(names=[*names]):
                for index, name in enumerate(names):
                    self.__variables[name] = input_strings[index]

            case _:
                return

    def __interpret_statement(self, statement: Statement) -> list[str] | None:
        """
        Interpret a Blip statement.

        This function returns `None` for most statements.
        If the statement is a Blip return statement, this function returns the list of Blip program output strings.
        """

        match statement:
            case Return():
                return self.__interpret_return(statement)

            case Assignment():
                self.__interpret_assignment(statement)
                return None

            case Decomposition():
                self.__interpret_decomposition(statement)
                return None

            case If():
                return self.__interpret_if(statement)

    def __interpret_assignment(self, statement: Assignment) -> None:
        self.__variables[statement.target.name] = self.__interpret_expression(statement.expression)

    def __interpret_return(self, statement: Return) -> list[str]:
        """A program returns a string or a list of strings, and always hands back a list of them."""

        returned = self.__interpret_expression(statement.expression)

        match statement.expression.blip_type:
            case Scalar.STRING:
                return [_as_string(returned)]
            case List(element=Scalar.STRING):
                if not isinstance(returned, list):
                    raise InterpreterError(f"Expected a list, but got {type(returned).__name__}")
                return [_as_string(i) for i in returned]
            case unreturnable:
                raise InterpreterError(f"Blip programs cannot return '{type(unreturnable).__name__}'")

    def __interpret_if(self, statement: If) -> list[str] | None:
        """Run whichever branch the condition selects, and pass on whatever that branch returns."""

        if self.__condition_holds(statement.condition):
            return self.__interpret_block(statement.body)

        return self.__interpret_block(statement.otherwise or [])

    def __condition_holds(self, condition: Condition) -> bool:
        """Whether an `if` takes its first branch."""

        match condition:
            case DecompTest():
                return self.__decomposition_matches(_as_string(self.__interpret_identifier(condition.target)), condition.pattern)

            case _:
                evaluated = self.__interpret_expression(condition)

                if not isinstance(evaluated, bool):
                    raise InterpreterError(f"Expected a boolean condition, but got {type(evaluated).__name__}")

                return evaluated

    def __interpret_decomposition(self, statement: Decomposition) -> None:
        """Decompose a string according to a pattern, binding any variables that the pattern captures."""

        original = _as_string(self.__interpret_identifier(statement.target))
        pattern = statement.pattern

        if not self.__decomposition_matches(original, pattern):
            raise InterpreterError(f"Decomposition failed: '{original}' does not match the pattern '{describe_pattern(pattern)}'")

    def __decomposition_matches(self, original: str, pattern: DecompPattern) -> bool:
        """
        Try a pattern against a string, binding every capture if it fits, and report whether it did.

        This is the whole of what a decomposition statement and an `if` condition share. The difference between them is only
        what they do with a `False`: the statement halts the program, the condition takes its other branch.
        """

        matched = re.fullmatch(pattern_regex(pattern), original, flags=FLAGS)

        if matched is None:
            return False

        self.__variables.update(matched.groupdict())

        return True

    def __interpret_expression(self, value: Value) -> BlipValue:
        """Evaluate a Blip value."""

        match value:
            case StringLiteral() | IntegerLiteral() | BooleanLiteral():
                return value.value

            case Identifier():
                return self.__interpret_identifier(value)

            case Concatenation():
                return "".join(_as_string(self.__interpret_expression(operand)) for operand in value.operands)

            case Index():
                return self.__interpret_index(value)

            case ListLiteral():
                elements: list[BlipValue] = [self.__interpret_expression(element) for element in value.elements]
                return elements

    def __interpret_index(self, value: Index) -> BlipValue:
        """Index into a list."""

        indexed = self.__interpret_identifier(value.target)
        if not isinstance(indexed, list):
            raise InterpreterError(f"Expected a list here, but got {type(indexed).__name__}")

        position = self.__interpret_expression(value.index)
        if not isinstance(position, int) and not isinstance(position, bool):
            raise InterpreterError(f"Expected an int here, but got {type(position).__name__}")

        if position >= len(indexed):
            raise InterpreterError(f"Index out of bounds (list has {len(indexed)} elements, index is {position})")

        return indexed[position]

    def __interpret_identifier(self, identifier: Identifier) -> BlipValue:
        """Read a variable."""

        if identifier.name not in self.__variables:
            raise InterpreterError(f"Identifier '{identifier.name}' does not exist")

        return self.__variables[identifier.name]

    def __validate_strings_against_directive(self, operands: list[str], directive: Directive) -> None:
        """Runtime check comparing directive arity against a number of input or output strings."""

        match directive:
            case FixedDirective(count=expected):
                if len(operands) != expected:
                    raise InterpreterError(f"Directive expected {expected} operands, got {len(operands)}")

            case RangeDirective(min=minimum, max=maximum):
                if minimum is not None and len(operands) < minimum:
                    raise InterpreterError(f"Directive expected at least {minimum} operands, got {len(operands)}")

                if maximum is not None and len(operands) > maximum:
                    raise InterpreterError(f"Directive expected at most {maximum} operands, got {len(operands)}")
