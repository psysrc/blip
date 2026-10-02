# For Developers

## Getting Started

Poetry is used to manage this repo.

You can *optionally* create a specific virtual env to install poetry.
This isn't necessary if you already have `poetry` available on the system.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install poetry
```

Then install all project dependencies:

```bash
poetry install
```

It is also recommended to set up your `pre-commit` hooks:

```bash
pip install pre-commit
pre-commit install
```

## Running Blip

To run the Blip tool:

```bash
poetry run python3 blip.py
```

## Unit tests

Pytest is used for unit testing. To run the test suite:

```bash
poetry run pytest
```

If desired, you can also get the code coverage output (the CI/CD pipeline does this):

```bash
poetry run pytest --cov=bliplib --cov-report=term-missing
```

## Linting and Formatting

Ruff is used as the linter and formatter.

To lint:

```bash
poetry run ruff check --fix
```

To format:

```bash
poetry run ruff format
```

## Type Checking

Pyright is used as the static type checker.

```bash
poetry run pyright
```
