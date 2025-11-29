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

Pytest is used for unit testing.

To run the unit tests, run `poetry run pytest`.
