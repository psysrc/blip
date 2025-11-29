# To-Do List

There are lots of things that need to be done to make Blip a useful piece of software.

# Design

Before a feature can be implemented, it has to be properly designed.
In no particular order, here are the ideas that still need to be fleshed out.

- Functions
- Static analysis and semantic checks after parsing
- Optimisations
- Improved error messages

## Implementation

Once a feature has been sufficiently designed, it needs to be implemented.

Feature|Parser|Interpreter|Transpiler (Python)|Transpiler (C)|Transpiler (C++)
-------|:----:|:---------:|:-----------------:|:------------:|:--------------:
Return statement|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
Concatenation|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
Decomposition|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
Variables|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
String type|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
List type|:white_check_mark:|:construction:|:x:|:x:|:x:
Integer type|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
List indexing|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
Boolean type|:x:|:x:|:x:|:x:|:x:
Input directives|:x:|:x:|:x:|:x:|:x:
Output directives|:x:|:x:|:x:|:x:|:x:
If-conditionals|:x:|:x:|:x:|:x:|:x:
For-loops|:x:|:x:|:x:|:x:|:x:
While-loops|:x:|:x:|:x:|:x:|:x:

Key:

Icon|Meaning
----|-------
:white_check_mark:|Implemented|
:x: | Not implemented yet
:construction: | In progress
