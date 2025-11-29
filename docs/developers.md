# For Developers

## Getting Started

Poetry is used to manage this repo.
To get started, do the following:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install poetry
poetry install
```

This will set up a new Python virtual environment with all dependencies.

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
