# To-Do List

There are lots of things that need to be done to make Blip a useful piece of software.

In no particular order, here are the things currently on the roadmap:

- Basic language syntax/behaviour defined
- Basic parser to convert to BlipIR
- Basic interpreter written in Python to execute Blip programs
- Basic transpiler to convert Blip to native Python code
- Basic transpiler to convert Blip to native C code
- Basic transpiler to convert Blip to native C++ code
- Improved tokenizer/parser/interpreter/transpiler error reporting

## Implementation Table

Once a particular design aspect is finalised, it's time to implement it in the `blip` tool.
This table shows each feature and which parts of the `blip` tool support it.

:white_check_mark: means it is implemented.
:x: means it's still to do.

|Feature|Parser|Interpreter|Transpile (Python)|Transpile (C)|Transpile (C++)|
|-------|------|-----------|------------------|-------------|---------------|
|Input directives|:x:|:x:|:x:|:x:|:x:|
|Output directives|:x:|:x:|:x:|:x:|:x:|
|Return statement|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:|
