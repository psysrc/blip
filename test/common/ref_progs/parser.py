import json

from markdown_it import MarkdownIt
from markdown_it.token import Token

from test.common.ref_progs.classes import ReferenceProgram, ReferenceProgramExecution


class TokenStream:
    def __init__(self, tokens: list[Token]) -> None:
        self.__tokens = tokens
        self.__current_token: Token | None = self.__tokens[0]

    def goto_token(self, **attrs) -> Token:
        """
        Move the current token to the next token in the stream that has the provided attributes.
        Return the current token if it exists, or raise an exception of the end of the token stream has been reached.
        """

        while True:
            match self.__current_token:
                case Token() if all(getattr(self.__current_token, k) == v for k, v in attrs.items()):
                    return self.__current_token

                case None:
                    raise RuntimeError("ReferenceParser.goto_token() reached the end of the token stream")

            self.consume_token()

    def consume_token(self) -> Token | None:
        """
        Consume and return the next token in the stream, or `None` if all tokens have been exhausted.
        """

        if self.__current_token is None:
            return None

        current_token = self.__current_token

        self.__tokens = self.__tokens[1:]
        self.__current_token = self.__tokens[0] if len(self.__tokens) > 0 else None

        return current_token

    def current_token(self) -> Token | None:
        return self.__current_token


class ReferenceParser:
    def __init__(self, markdown_text: str) -> None:
        self.__tokens = MarkdownIt().parse(markdown_text)

    def get_reference_programs(self) -> list[ReferenceProgram]:
        return [self.__parse_reference_program(tokens) for tokens in self.__program_token_chunks()]

    def __program_token_chunks(self) -> list[list[Token]]:
        """
        Split the token stream into one chunk per program, each starting at its `##` heading.

        Sections are optional - a program that cannot compile has no `#### Blip IR` and no `#### Execution` - so looking one up
        has to be able to come back empty rather than running off the end of the stream. Chunking first is what allows that.
        """

        chunks: list[list[Token]] = []

        for token in self.__tokens:
            if token.type == "heading_open" and token.tag == "h2":
                chunks.append([token])
            elif chunks:
                chunks[-1].append(token)

        return chunks

    @staticmethod
    def __section_index(tokens: list[Token], section: str) -> int | None:
        """The index of a `####` section heading's inline token, or `None` if the program has no such section."""

        return next((i for i, token in enumerate(tokens) if token.type == "inline" and token.content == section), None)

    @staticmethod
    def __fence_after(tokens: list[Token], start: int, info: str) -> str:
        """The contents of the first fenced block of the given kind at or after `start`."""

        for token in tokens[start:]:
            if token.type == "fence" and token.info == info:
                return token.content

        raise RuntimeError(f"Failed to find a '{info}' fenced block in a reference program")

    def __parse_reference_program(self, tokens: list[Token]) -> ReferenceProgram:
        name = next(token.content for token in tokens if token.type == "inline")

        code_index = self.__section_index(tokens, "Blip code")
        if code_index is None:
            raise RuntimeError(f"Reference program '{name}' has no '#### Blip code' section")

        blip_code = self.__fence_after(tokens, code_index, "blip")

        compilation_index = self.__section_index(tokens, "Compilation")
        if compilation_index is not None:
            # The program is expected to fail to compile, so it has no BlipIR and nothing to execute
            return ReferenceProgram(
                name=name,
                blip_code=blip_code,
                compile_error=self.__fence_after(tokens, compilation_index, "text").strip(),
            )

        ir_index = self.__section_index(tokens, "Blip IR")
        if ir_index is None:
            raise RuntimeError(f"Reference program '{name}' has neither a '#### Blip IR' nor a '#### Compilation' section")

        blip_ir = json.loads(self.__fence_after(tokens, ir_index, "json"))

        return ReferenceProgram(
            name=name,
            blip_code=blip_code,
            blip_ir=blip_ir,
            executions=self.__parse_executions(tokens, name),
        )

    def __parse_executions(self, tokens: list[Token], name: str) -> list[ReferenceProgramExecution]:
        execution_index = self.__section_index(tokens, "Execution")
        if execution_index is None:
            raise RuntimeError(f"Reference program '{name}' has no '#### Execution' section")

        table_stream = TokenStream(tokens=tokens[execution_index + 1 :])
        table_tokens = table_stream.goto_token(type="inline").children

        if table_tokens is None:
            raise RuntimeError("Failed to get Execution data: Table tokens are empty")

        row_stream = TokenStream(tokens=table_tokens)
        execution_data: list[tuple[str, str]] = []

        while True:
            input = row_stream.goto_token(type="code_inline", tag="code").content
            row_stream.consume_token()
            output = row_stream.goto_token(type="code_inline", tag="code").content

            execution_data.append((input, output))

            row_stream.consume_token()
            row_stream.consume_token()

            match row_stream.current_token():
                case None:
                    break
                case Token(type="softbreak"):
                    continue
                case _:
                    raise RuntimeError(f"Unexpected token while parsing execution table: {row_stream.current_token()}")

        return [self.__make_execution(exec_data) for exec_data in execution_data]

    @staticmethod
    def __make_execution(exec_data: tuple[str, str]) -> ReferenceProgramExecution:
        i, o = exec_data

        in_strings: list[str] = json.loads(i)

        if o == "Error":
            success = False
            out_strings: list[str] = []
        else:
            success = True
            out_strings = json.loads(o)

        return ReferenceProgramExecution(input_strings=in_strings, output_strings=out_strings, expect_success=success)
