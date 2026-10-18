# To-Do List

There are lots of things that need to be done to make Blip a useful piece of software.

# Design

Before a feature can be implemented, it has to be properly designed.
In no particular order, here are the ideas that still need to be fleshed out.

- Functions
- Definite-return analysis, static directive arity checks
- Optimisations
- Arithmetic
- Indexing into strings

## Implementation

Once a feature has been sufficiently designed, it needs to be implemented.

Feature|Parser|Analyser|Interpreter|Transpiler (Python)|Transpiler (C)|Transpiler (C++)
-------|:----:|:------:|:---------:|:-----------------:|:------------:|:--------------:
Return statement|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Concatenation|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Decomposition|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Variables|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
String type|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
List type|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Integer type|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
List indexing|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Boolean type|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Input directives|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Output directives|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
If-conditionals|:white_check_mark:|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
For-loops|:x:|:x:|:x:|:x:|:x:|:x:
While-loops|:x:|:x:|:x:|:x:|:x:|:x:

Key:

Icon|Meaning
----|-------
:white_check_mark: | Implemented
:x: | Not implemented yet
:construction: | In progress

## Outstanding work to consider

- **`Program.variables` and a value walker.** The computed property that replaces the derived variable map is not implemented. It needs a walk
  over every value node, which `blip --check` also wants; one exists as `values_of()` in `test/unit/test_analyser.py` and belongs in
  `bliplib/ir/` rather than being written a second time. A C backend is the real customer.
- **Error recovery.** The analyser raises on the first `SemanticError`, like the parser and the loader. Reporting several at once needs a fourth
  type-model case — an `Unknown` meaning "this expression is already wrong, do not complain about it again" — plus a diagnostic list in place of
  a raise, and one more case for the resolution pass to reject. Worth having once one error per run gets tedious; until then `Unknown` would be
  a case nothing produces.
- **`.blipir` as CLI input.** `blip` accepts `.blip` source only, and detecting the format is a separate decision. The annotation design is what
  makes the feature worth having, and `load()` is the code it will need.

- **`else if`.** Not implemented, and not described in the Language Reference yet either. `else if ...` is syntactic sugar for `else { if ... }`. The `else`
  branch becomes a single-element list holding a nested `If`, which is what `else { if ... }` already produces - but it needs
  its own reference program and its own paragraph in the reference before it is a feature rather than an accident.
- **Definite-return analysis and `if`.** The Python backend decides whether to append its "halted without returning a value"
  raise by asking, syntactically, whether the last top-level statement is a `ret`. A program ending in an `if` whose every
  branch returns therefore gets an unreachable raise appended. It is harmless, and removing it is the definite-return
  analysis listed above.

The remaining constructs are described in the [Language Reference](language_reference.md) but are not yet implemented by the parser.
Their binding rules are settled here so that the analyser does not have to be redesigned when they land:

- **Loops.** The body is analysed once. A variable assigned in the body must keep the type it had before the loop.
- **Loop variables.** `for item in items` binds `item` to the element type of `items`; `for num in 3` binds `num` to `INTEGER`. The loop
  variable is scoped to the body.
- **`break`.** Mentioned in the Language Reference's loop sections, with no section of its own. `continue` is not mentioned
  anywhere, so whether Blip has one is still open.

- **User-defined functions.** Functions will likely be explicitly typed, but
  if Blip gets functions and they are meant to be generic, this is where unification's missing half — generalisation at the definition and
  instantiation at each use, the other half of Hindley–Milner — becomes necessary. That decision belongs with the functions design; the
  unification described above is the part that would not change.
- **Error recovery for the tokenizer's recursion.** `Tokenizer` skips trivia by recursing once per character, so roughly a thousand
  consecutive spaces exhausts the stack. `RecursionError` is not a `BlipError`, so it escapes the CLI's handlers as a traceback.
  Converting the skip to a loop fixes it, but the whitespace pattern must stay single-character or match `[^\S\n]+` - `\s+` would
  swallow the newline that `EOL` depends on. Deliberately deferred when source locations landed.
- **Comparison operators and arithmetic.** `if` and `while` conditions must be `BOOLEAN`, but no operator produces one yet, and arithmetic is
  still to be designed. Rules will be added when the operators are. This is now the main thing holding the language back:
  `if` is implemented, but until an operator yields a `BOOLEAN` its condition can only be a boolean variable or a literal,
  which is why conditional decomposition is the only form of it that is much use. `while` cannot land at all without them.
  They slot into `__parse_expression` additively, without disturbing the statement machinery `if` introduced.

- **A program with no `ret`.** Input-independent, but a reachability question rather than a type-and-binding one, and it gets harder the moment
  `if` and `while` land. The "Empty Program" reference program documents this as a valid program that fails at execution. Definite-return
  analysis is a separate feature for another day.
- **Directive arity against a literal return.** `!out 2` with `ret "OK"` is provably wrong without running the program, but proving it needs
  *length* tracking, which is not in the type model. It would also be inconsistent: provable for a literal, unknowable for `ret input`.

- Consider rewriting the Python transpiler so it doesn't rely on the `re` module. This would involve writing the Blip decomposition logic in
  pure Python. Perhaps this could be a togglable feature on the Python transpiler - simpler code if you allow the `re` import, or avoid the
  `re` import with the downside of more verbose/complicated code.
