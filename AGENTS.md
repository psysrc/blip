# AGENTS.md

## What Blip is

A DSL for parsing and manipulating string data. Blip source is parsed into **BlipIR** (a JSON-serialisable tree), which is then either interpreted directly or transpiled into another language.

```
Blip code -> Parser -> BlipIR -> Interpreter
                             \-> Python / C / C++ transpiler -> target code
```

BlipIR is the contract between the front end and every back end, and it exists in two forms:

- **the object model** in `bliplib/ir/`, a class per node kind. The parser builds it, the analyser gives every value its type, and every consumer walks it;
- **the `dict`**, which is purely the serialised form: what `--ir` prints and what a `.blipir` file holds. `load()` turns one back into objects, validating it completely.

Analysis runs in every mode, and every consumer reads the analysed tree: `--ir`, the interpreter and the transpilers all take a `Program`. No `dict` exists on the `.blip` path at all, so **a change to the IR shape touches `bliplib/ir/` and nothing else** - the parser, interpreter and transpilers contain no node-kind strings.

| Path | Role |
|------|------|
| `blip.py` | CLI entry point (`--interpret`, `--transpile LANG`, `--ir`, `--check`, `--prog`, `--no-analysis`) |
| `bliplib/parser/` | Tokenizer and parser; builds the BlipIR object model, with every type left unset |
| `bliplib/ir/` | BlipIR object model: a class per node kind, `load()` and `to_dict()` |
| `bliplib/decomposition.py` | What a decomposition pattern means: its capture names, its error text, and its lowering to a regex |
| `bliplib/analysis/` | The Blip Analyser: gives every value a type, rejects programs that cannot have one. Runs in every CLI mode |
| `bliplib/interpreter/` | Executes BlipIR directly |
| `bliplib/transpiler/` | `interface.py` (ABC), `factory.py` (name -> transpiler), one module per target |
| `bliplib/errors/` | All exceptions subclass `BlipError` |
| `docs/refs/` | Reference programs — **also the test suite**, see below |

## Reference programs are the test suite

The markdown files in `docs/refs/` are parsed at test time by `test/common/ref_progs/getter.py`, which globs `docs/refs/*.md` (skipping `README.md`) and extracts every program's Blip code, its expected BlipIR, and a table of input/output executions.

Those parsed programs are then run against the parser, the interpreter, and each transpiler.

**So: adding or changing a language feature means editing the documentation.** A new reference program in `docs/refs/` is immediately picked up by the parser, interpreter and transpiler test suites. A reference program that compiles needs `#### Blip code`, `#### Blip IR` and an `#### Execution` table; follow `docs/refs/basic_programs.md`. One that is *meant* to be rejected has a `#### Error` section instead of those last two, naming the error class and, beneath it, the diagnostic the error renders into - caret, notes and all. That rendering is compared exactly, so **rewording an error message might mean updating the `docs/refs/` area**.

Write unit tests in `test/unit/` only for things reference programs can't express — internal helpers, error paths, malformed IR.

## Feature-completeness bookkeeping

**`docs/todo.md`** has a per-feature, per-backend status matrix (:white_check_mark: / :construction: / :x:) that goes stale silently. Update the relevant cell when a feature lands.

The `xfail` feature of Pytest can be used if appropriate; particularly if new reference programs are added and certain staged (parsing/analysis/interpreting/transpiling) don't support it just yet. This can be useful, for example, when implementing new transpiler backends: the programs it can't handle can be put in an `xfail_progs` list and mark them `strict=True`, so that a program which starts passing **fails** the suite until it is taken off the list. That's the signal a feature is finished. Git history has the Python transpiler's version of this if you need (before commit `66605a1d1`).

## Commands

```bash
poetry install

poetry run pytest test/unit/          # fast
poetry run pytest test/integration/   # slow: builds the binary first
poetry run pytest                     # runs both, so also builds the binary

poetry run ruff check --fix
poetry run ruff format
```

Integration tests are slow-ish: the session-scoped autouse fixture in `test/integration/conftest.py` runs `./build.sh`, which invokes PyInstaller to produce `./build/bin/blip`, and the tests then drive that binary as a subprocess. Prefer `pytest test/unit/` while iterating.

CI (`.github/workflows/build.yml`) runs unit tests with coverage, integration tests, `ty check`, `ruff check` and `ruff format --check` — all five must pass. `.pre-commit-config.yaml` runs the same checks bar the integration tests.

## Code conventions

- Ruff, line length **140** (configured in `pyproject.toml`; there is no other lint config).
- Private attributes use the double-underscore name-mangled form (`self.__expression`), consistently throughout.
- Transpilers must implement both `transpile_function` and `transpile_program` from `bliplib/transpiler/interface.py`, and register in `factory.py`.

## Lowering decomposition into regexes

Decomposition is trivially implementable as a regex "find all" search. The interpreter and Python transpiler both do this using
`decomposition.py`.
However, this file is Python/PCRE specific regex syntax; it is not necessarily usable for other transpiler backends:

| | `(?P<name>…)` | lazy `.*?` | `.` matches newline |
|---|---|---|---|
| Python + `re.DOTALL` | yes | yes | yes |
| C++ `std::regex` (ECMAScript) | **rejected at compile time** | yes | **no** - needs `[\s\S]` |
| C POSIX `<regex.h>` | **rejected at compile time** | **compiles, but matches greedily** | yes |

The **"The First Occurrence Wins"** reference program in `docs/refs/decomposition.md` exists to catch these kinds of disagreements.

So a new back end may need its own lowering of `DecompPattern`. What is shared is the *meaning* - non-greedy captures, the
whole-string rule, a capture named after the variable it binds - and `docs/refs/decomposition.md` is where that meaning is
pinned, for every back end, by execution rather than by regex.

## Transpiler back ends

Each transpiler should ideally build a tree of small node classes and serialise into source code at the end.
For example, the Python back end (`bliplib/transpiler/python.py`) uses the stdlib `ast` module: nodes expose `node()` returning an `ast` node, and `ast.unparse` handles escaping, quoting, operator precedence and indentation. Static scaffolding (function signature, imports, `main()`) is written as ordinary Python source and run through `ast.parse` since none of it derives from BlipIR; hand-built `ast` nodes are reserved for what does.

## Docstrings and Comments

Docstrings and comments should be short, to the point, and only talk about the immediate code local to that docstring/comment.
Docstrings and comments should never explain how the "old code" used to work.

Here is a bad example. The docstring below discusses other functions in the file and is way too verbose.
It also starts talking about what the old code used to do before this function existed - pointless.

```python
# Bad example
def read_source(file: str) -> str:
    """
    Read a Blip source file, or report why it could not be read and exit.

    This cannot go through `fail()`: that renders a span against the source text, and there is no source text yet. An
    unreadable file is also not a `BlipError` - nothing about the program is wrong, the file just is not there - so it is
    reported as the plain message an operating system error deserves.

    The call sites used to do this calculation manually, meaning a change had to be copied everywhere each time.
    """
```

Here is a good example of the same function. Short, simple, local to the code it sits near, and doesn't talk about the "old code".

```python
# Good example
def read_source(file: str) -> str:
    """Read a Blip source file, or report why it could not be read and exit."""
```

## Blip code conventions

When writing Blip code on a single line, prefer semicolons `;` to newline characters `\n` where possible.
For example:

- GOOD: `'name = "sam"; ret name'`
- BAD:  `'name = "sam"\nret name'`

Also, more generally, avoid whitespace unless it is necessary.
For example:

- GOOD: `'flag = true; if flag { if flag { ret "deep" } }'`
- BAD:  `'flag = true\nif flag {\n  if flag {\n    ret "deep"\n  }\n}\n'`

This is to aide human readability.

An obvious exception to this convention is where a unit test is asserting that newlines are handled properly by the `blip` suite.
