# BLiP

BLiP code is a Domain Specific Language (DSL) for parsing and manipulating string data.

Using the BLiP parser program, BLiP code can be parsed into a BLiP AST (Abstract Syntax Tree):

```mermaid
flowchart LR
    blip(.blip)
    blipast(.blipast)
    parser[BLiP Parser]

    blip --> parser
    parser --> blipast
```

BLiP AST code can then either be directly run using a BLiP interpreter...

```mermaid
flowchart LR
    i(Input Strings)
    o(Output Strings)
    blipast(.blipast)
    interpreter[BLiP Interpreter]

    i --> interpreter
    blipast --> interpreter --> o
```

...or be transpiled into a target language of choice (such as Python)...

```mermaid
flowchart LR
    blipast(.blipast)
    t[Target Code]
    transpiler[BLiP Transpiler]

    i(Input Strings)
    o(Output Strings)

    blipast --> transpiler --> t

    i --> t --> o
```

## Name history

The DSL is syntactically inspired by BNF (Backus-Naur Form) but is functionally different.
This is where BLiP originally derived its name: BNF Lite Parser.
Because the BLiP DSL grammar is functionally different from BNF, however, this acronym is a misnomer.
Therefore, officially, BLiP is a standalone name and is not an acronym.
