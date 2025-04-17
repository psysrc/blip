# Design documentation

Using the Blip parser, Blip code can be parsed into a Blip AST (Abstract Syntax Tree):

```mermaid
flowchart LR
    blip(.blip)
    blipast(.blipast)
    parser[Blip Parser]

    blip --> parser
    parser --> blipast
```

Blip AST code can then either be directly run using a Blip interpreter...

```mermaid
flowchart LR
    i(Input Strings)
    o(Output Strings)
    blipast(.blipast)
    interpreter[Blip Interpreter]

    i --> interpreter
    blipast --> interpreter --> o
```

...or be transpiled into a target language of choice (such as Python)...

```mermaid
flowchart LR
    blipast(.blipast)
    t[Target Code]
    transpiler[Blip Transpiler]

    i(Input Strings)
    o(Output Strings)

    blipast --> transpiler --> t

    i --> t --> o
```
