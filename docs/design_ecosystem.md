# Blip Ecosystem Design

Blip code can be used in a few different ways:

1. Directly execute Blip code using an interpreter
2. Transpile Blip code into a target language, like Python or C

## Directly execute Blip code using an interpreter

Using a Blip Interpreter, you can take Blip code and interpret it directly.

For example, this package provides a Blip Interpreter class written in Python.
Using this, you can give it raw Blip code and execute it straight from Python.

```mermaid
flowchart LR
    i(Input Strings)
    o(Output Strings)
    blip(.blip)
    interpreter[Blip Interpreter]

    i --> interpreter
    blip --> interpreter --> o

    style blip fill:#55f,color:#fff,stroke:#333
    style interpreter fill:#555,color:#fff,stroke:#333
    style i fill:#ddd,color:#000,stroke:#333
    style o fill:#ddd,color:#000,stroke:#333
```

## Transpile Blip code into a target language

Using a Blip Transpiler, you can take Blip code and convert it into a target language.
For example, you could transpile into Python code, or C code, or any language the transpiler supports.

```mermaid
flowchart LR
    blip(.blip)
    t(Target Code)
    transpiler[Blip Transpiler]

    blip --> transpiler --> t

    style blip fill:#55f,color:#fff,stroke:#333
    style transpiler fill:#555,color:#fff,stroke:#333
    style t fill:#333,color:#fff,stroke:#333
```

From there, of course, you can take the target code output and do what you need to with it.
If it's an interpreted language like Python, it should run as-is.
If it's a compiled language like C, you'll need to run it through a C compiler to get an executable program.

## Intermediate representation - BlipIR

Blip code is parsed into an intermediate representation (IR) that is more convenient for computers to handle.
This is dubbed BlipIR and takes the file extension `.blipir`.

Using the Blip parser, Blip code (`.blip`) can be parsed into BlipIR (`.blipir`):

```mermaid
flowchart LR
    blip(.blip)
    blipir(.blipir)
    parser[Blip Parser]

    blip --> parser
    parser --> blipir

    style blip fill:#55f,color:#fff,stroke:#333
    style blipir fill:#85f,color:#fff,stroke:#333
    style parser fill:#555,color:#fff,stroke:#333
```

BlipIR (and hence the parser) is used for both transpiling and direct interpretation.
Therefore it is a very important part of the Blip processing lifecycle.

BlipIR code is an Abstract Syntax Tree (AST) encoded in JSON.

For convenience, the rest of this document omits BlipIR and the Blip parser from diagrams and descriptions.
Just remember that it remains a core part of the Blip interpretation and transpiling design.
