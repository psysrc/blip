import json
from typing import Optional
from markdown_it import MarkdownIt
from markdown_it.token import Token
from test.common.ref_progs.classes import ReferenceProgram, ReferenceProgramExecution


class TokenStream:
    def __init__(self, tokens: list[Token]) -> None:
        self.__tokens = tokens
        self.__current_token: Optional[Token] = self.__tokens[0]

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

    def consume_token(self) -> Optional[Token]:
        """
        Consume and return the next token in the stream, or `None` if all tokens have been exhausted.
        """

        if self.__current_token is None:
            return None

        current_token = self.__current_token

        self.__tokens = self.__tokens[1:]
        self.__current_token = self.__tokens[0] if len(self.__tokens) > 0 else None

        return current_token

    def current_token(self) -> Optional[Token]:
        return self.__current_token


class ReferenceParser:
    def __init__(self, markdown_text: str) -> None:
        self.__token_stream = TokenStream(tokens=MarkdownIt().parse(markdown_text))

    def get_reference_programs(self) -> list[ReferenceProgram]:
        reference_programs: list[ReferenceProgram] = []

        finished = False
        while not finished:
            match self.__token_stream.current_token():
                case Token(type="heading_open", tag="h2"):
                    reference_programs.append(self.__parse_reference_program())

                case None:
                    return reference_programs

            self.__token_stream.consume_token()

        raise RuntimeError("ReferenceParser.get_reference_programs() halted without returning anything")

    def __parse_reference_program(self) -> ReferenceProgram:
        self.__token_stream.goto_token(type="heading_open", tag="h2")
        reference_name = self.__token_stream.goto_token(type="inline").content

        self.__token_stream.goto_token(type="inline", content="Blip code")
        blip_code = self.__token_stream.goto_token(type="fence", info="blip").content

        self.__token_stream.goto_token(type="inline", content="Blip IR")
        blip_ir = self.__token_stream.goto_token(type="fence", info="json").content

        self.__token_stream.goto_token(type="inline", content="Execution")
        self.__token_stream.consume_token()
        table_tokens = self.__token_stream.goto_token(type="inline").children

        if table_tokens is None:
            raise RuntimeError("Failed to get Execution data: Table tokens are empty")

        table_stream = TokenStream(tokens=table_tokens)

        execution_data: list[tuple[str, str]] = []

        while True:
            input = table_stream.goto_token(type="code_inline", tag="code").content
            table_stream.consume_token()
            output = table_stream.goto_token(type="code_inline", tag="code").content

            execution_data.append((input, output))

            table_stream.consume_token()
            table_stream.consume_token()

            match table_stream.current_token():
                case None:
                    break
                case Token(type="softbreak"):
                    continue
                case _:
                    raise RuntimeError(f"Unexpected token while parsing execution table: {table_stream.current_token()}")

        def make_execution(exec_data: tuple[str, str]) -> ReferenceProgramExecution:
            i = exec_data[0]
            o = exec_data[1]

            in_strings: list[str] = json.loads(i)

            if o == "Error":
                success = False
                out_strings: list[str] = []
            else:
                success = True
                out_strings: list[str] = json.loads(o)

            return ReferenceProgramExecution(input_strings=in_strings, output_strings=out_strings, expect_success=success)

        return ReferenceProgram(
            name=reference_name,
            blip_code=blip_code,
            blip_ir=json.loads(blip_ir),
            executions=[make_execution(exec_data) for exec_data in execution_data],
        )
