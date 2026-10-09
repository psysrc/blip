# To-Do List

There are lots of things that need to be done to make Blip a useful piece of software.

# Design

Before a feature can be implemented, it has to be properly designed.
In no particular order, here are the ideas that still need to be fleshed out.

- Functions
- Definite-return analysis, static directive arity checks
- Optimisations
- Improved error messages
- Arithmetic
- Indexing into strings

## Implementation

Once a feature has been sufficiently designed, it needs to be implemented.

Feature|Parser|Interpreter|Transpiler (Python)|Transpiler (C)|Transpiler (C++)
-------|:----:|:---------:|:-----------------:|:------------:|:--------------:
Return statement|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Concatenation|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Decomposition|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Variables|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
String type|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
List type|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Integer type|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
List indexing|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Boolean type|:white_check_mark:|:white_check_mark:|:white_check_mark:|:x:|:x:
Input directives|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
Output directives|:white_check_mark:|:white_check_mark:|:x:|:x:|:x:
If-conditionals|:x:|:x:|:x:|:x:|:x:
For-loops|:x:|:x:|:x:|:x:|:x:
While-loops|:x:|:x:|:x:|:x:|:x:

Key:

Icon|Meaning
----|-------
:white_check_mark: | Implemented
:x: | Not implemented yet
:construction: | In progress

## Outstanding work to consider

- **Decomposition adjacency check.** A decomposition pattern whose capturing elements are adjacent — `x -> a b`, `x -> * b`, `x -> a *` — analyses
  cleanly and then fails at execution. It belongs here: a capturing element needs a following literal to say where it stops, so a pattern
  without one is unsatisfiable whatever the input. The rule would be that every `identifier` and `decomposition_wildcard` in a pattern is
  either last or followed by a `string_literal`. Adding it means an inference rule, an error-table row, a reference program, and deleting the
  interpreter's check — which is the only reason that check still exists.
- **`Program.variables` and a value walker.** The computed property that replaces the derived variable map is not implemented. It needs a walk
  over every value node, which `blip --check` also wants; one exists as `values_of()` in `test/unit/analysis/test_analyser.py` and belongs in
  `bliplib/ir/` rather than being written a second time. A C backend is the real customer.
- **Error recovery.** The analyser raises on the first `SemanticError`, like the parser and the loader. Reporting several at once needs a fourth
  type-model case — an `Unknown` meaning "this expression is already wrong, do not complain about it again" — plus a diagnostic list in place of
  a raise, and one more case for the resolution pass to reject. Worth having once one error per run gets tedious; until then `Unknown` would be
  a case nothing produces.
- **`.blipir` as CLI input.** `blip` accepts `.blip` source only, and detecting the format is a separate decision. The annotation design is what
  makes the feature worth having, and `load()` is the code it will need.


The following constructs are described in the [Language Reference](language_reference.md) but are not yet implemented by the parser. Their
binding rules are settled here so that the analyser does not have to be redesigned when they land:

- **`if` / `else` branches.** A variable bound in only one branch is **not** bound after the `if`. A variable bound in all branches must have
  the same type in each.
- **Conditional decomposition** (`if email -> name "@" domain { ... }`). Bindings are visible **inside the block only**, since they do not
  exist when the decomposition fails.
- **Decomposition alternatives** (`a | b`). All alternatives must bind the same names at the same types. This rules out a nasty class of bug
  where the set of bound variables depends on which alternative matched.
- **Loops.** The body is analysed once. A variable assigned in the body must keep the type it had before the loop.
- **Loop variables.** `for item in items` binds `item` to the element type of `items`; `for num in 3` binds `num` to `INTEGER`. The loop
  variable is scoped to the body.

- **User-defined functions.** `docs/todo.md` lists functions as a feature still to be designed. Functions will likely be explicitly typed, but
  if Blip gets functions and they are meant to be generic, this is where unification's missing half — generalisation at the definition and
  instantiation at each use, the other half of Hindley–Milner — becomes necessary. That decision belongs with the functions design; the
  unification described above is the part that would not change.
- **Source locations.** BlipIR carries none, so a semantic error can describe a conflict structurally but cannot point at a line. This bites
  hardest when two distant constraint sites disagree. Tracked under the `docs/todo.md` "Improved error messages" item.
- **Comparison operators and arithmetic.** `if` and `while` conditions must be `BOOLEAN`, but no operator produces one yet, and arithmetic is
  still to be designed. Rules will be added when the operators are.
- **Generalised decomposition targets.** The rule above is that the target must be `STRING`; the IR permits only an identifier, which is why
  `Decomposition.target` and `Index.target` are typed as `Identifier` in the object model. The alternative assignment syntax `"John" -> name` in
  the Language Reference implies a target that is an arbitrary `STRING`-typed expression, which is a parser change first.

- **A program with no `ret`.** Input-independent, but a reachability question rather than a type-and-binding one, and it gets harder the moment
  `if` and `while` land. The "Empty Program" reference program documents this as a valid program that fails at execution. Definite-return
  analysis is a separate feature for another day.
- **Directive arity against a literal return.** `!out 2` with `ret "OK"` is provably wrong without running the program, but proving it needs
  *length* tracking, which is not in the type model. It would also be inconsistent: provable for a literal, unknowable for `ret input`.
