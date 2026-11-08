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

## Test suite

The full test suite consists of unit tests and integration tests. Pytest is used for both.
`pytest-xdist` is used to let the tests run across multiple cores (this significantly speeds up the integration tests).

```bash
poetry run pytest                    # Run the full test suite
poetry run pytest test/unit/         # Run the full test suite
poetry run pytest test/integration/  # Run the full test suite
```

To get a code coverage report from the unit tests:

```bash
poetry run pytest test/unit/ --cov=bliplib --cov-report=term-missing
```

Note the code coverage report does not work with the integration tests.

## Linting and Formatting

`ruff` is used for linting and formatting:

```bash
poetry run ruff check --fix
poetry run ruff format
```

## Type Checking

`ty` is used for static type checking:

```bash
poetry run ty check
```
