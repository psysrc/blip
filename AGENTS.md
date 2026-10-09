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
| `blip.py` | CLI entry point (`--interpret`, `--transpile LANG`, `--ir`, `--prog`) |
| `bliplib/parser/` | Tokenizer and parser; produces BlipIR as a `dict` |
| `bliplib/ir/` | BlipIR object model: a class per node kind, `load()` and `to_dict()` |
| `bliplib/analysis/` | The Blip Analyser: gives every value a type, rejects programs that cannot have one. Not yet wired into the CLI |
| `bliplib/interpreter/` | Executes BlipIR directly |
| `bliplib/transpiler/` | `interface.py` (ABC), `factory.py` (name -> transpiler), one module per target |
| `bliplib/errors/` | All exceptions subclass `BlipError` |
| `docs/refs/` | Reference programs — **also the test suite**, see below |

## Reference programs are the test suite

The markdown files in `docs/refs/` are parsed at test time by `test/common/ref_progs/getter.py`, which globs `docs/refs/*.md` (skipping `README.md`) and extracts every program's Blip code, its expected BlipIR, and a table of input/output executions.

Those parsed programs are then run against the parser, the interpreter, and each transpiler.

**So: adding or changing a language feature means editing the documentation.** A new reference program in `docs/refs/` is immediately picked up by the parser, interpreter and transpiler test suites. A reference program that compiles needs `#### Blip code`, `#### Blip IR` and an `#### Execution` table; follow `docs/refs/basic_programs.md`. One that is *meant* to be rejected has a `#### Compilation` section naming the error instead of those last two; follow `docs/refs/static_errors.md`.

Write unit tests in `test/unit/` only for things reference programs can't express — internal helpers, error paths, malformed IR.

## Feature-completeness bookkeeping

Two places track which backend supports what, and both go stale silently:

- **`test/integration/program_references/test_python_transpiler.py`** holds an `xfail_progs` list naming reference programs the Python backend can't handle yet. The marks are `strict=True`, so a program that starts passing will **fail** the suite until you remove it from the list. That's intentional — it's the signal that you've finished a feature.
- **`docs/todo.md`** has a per-feature, per-backend status matrix (:white_check_mark: / :construction: / :x:). Update the relevant cell when a feature lands.

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

CI (`.github/workflows/build.yml`) runs unit tests with coverage, integration tests, `ruff check` and `ruff format --check` — all four must pass.

## Code conventions

- Ruff, line length **140** (configured in `pyproject.toml`; there is no other lint config).
- Private attributes use the double-underscore name-mangled form (`self.__expression`), consistently throughout.
- Transpilers must implement both `transpile_function` and `transpile_program` from `bliplib/transpiler/interface.py`, and register in `factory.py`.

## Transpiler back ends

Each transpiler should ideally build a tree of small node classes and serialise into source code at the end.
For example, the Python back end (`bliplib/transpiler/python.py`) uses the stdlib `ast` module: nodes expose `node()` returning an `ast` node, and `ast.unparse` handles escaping, quoting, operator precedence and indentation. Static scaffolding (function signature, imports, `main()`) is written as ordinary Python source and run through `ast.parse` since none of it derives from BlipIR; hand-built `ast` nodes are reserved for what does.
