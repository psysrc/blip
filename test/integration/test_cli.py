"""
Integration tests for the `blip` CLI.
"""

import json
from pathlib import Path

import pytest

from test.integration.conftest import run_blip, run_blip_on_file

LEXICAL_ERROR = "first = 1\nsecond = \u00a35\nret first"
SYNTAX_ERROR = 'a = "x"\nb = = "y"\n'
SEMANTIC_ERROR = 'x = "a"\nx = 1\nret x'
GOOD = 'ret "ok"'


def test_check_emits_nothing_and_succeeds_for_a_good_program():
    result = run_blip(["--check"], GOOD)

    assert result.returncode == 0
    assert result.stdout == ""


def test_check_fails_for_a_program_with_a_static_error():
    result = run_blip(["--check"], SEMANTIC_ERROR)

    assert result.returncode != 0
    assert "semantic error" in result.stderr


@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(["--check"], id="check"),
        pytest.param(["--ir"], id="ir"),
        pytest.param(["--interpret"], id="interpret"),
        pytest.param(["--transpile", "python", "--prog"], id="transpile"),
    ],
)
def test_a_static_error_is_refused_in_every_mode(mode: list[str]):
    """The whole point of running analysis everywhere: one wrong program, one error, whatever you asked for."""

    result = run_blip(mode, SEMANTIC_ERROR)

    assert result.returncode != 0
    assert "semantic error" in result.stderr


def test_ir_output_is_annotated():
    result = run_blip(["--ir"], GOOD)

    assert result.returncode == 0
    assert json.loads(result.stdout)["statements"][0]["expression"]["blip_type"] == "string"


def test_no_analysis_dumps_unannotated_ir():
    result = run_blip(["--ir", "--no-analysis"], GOOD)

    assert result.returncode == 0
    assert "blip_type" not in result.stdout


def test_no_analysis_is_rejected_outside_ir_mode():
    """It exists to debug the analyser, not to run a program the analyser rejects."""

    for mode in (["--interpret"], ["--check"], ["--transpile", "python"]):
        result = run_blip([*mode, "--no-analysis"], GOOD)

        assert result.returncode != 0, f"--no-analysis flag was accepted with {mode}"


def test_a_diagnostic_names_the_file_line_and_column():
    result = run_blip(["--check"], SYNTAX_ERROR)

    assert result.returncode != 0
    assert result.stderr.startswith("<stdin>:2:5: parser error: ")


def test_a_diagnostic_draws_a_caret_under_the_source():
    result = run_blip(["--check"], SYNTAX_ERROR)

    assert result.returncode != 0
    assert '\n2 | b = = "y"\n' in result.stderr
    assert "\n  |     ^\n" in result.stderr


def test_a_lexical_error_reports_what_failed_and_where():
    result = run_blip(["--check"], LEXICAL_ERROR)

    assert result.returncode != 0
    assert result.stderr.startswith("<stdin>:2:10: parser error: ")
    assert "Unknown syntax near characters" in result.stderr


def test_a_type_conflict_is_reported_at_both_sites():
    result = run_blip(["--check"], SEMANTIC_ERROR)

    assert result.returncode != 0
    assert result.stderr.startswith("<stdin>:2:5: semantic error: ")
    assert "<stdin>:1:1: note: 'x' was bound as 'string' here" in result.stderr

    assert '\n1 | x = "a"\n' in result.stderr
    assert "\n2 | x = 1\n" in result.stderr


def test_an_unknown_transpiler_is_reported_as_a_diagnostic():
    result = run_blip(["--transpile", "matlab"], GOOD)

    assert result.returncode != 0
    assert "transpiler error" in result.stderr
    assert "matlab" in result.stderr
    assert "Traceback" not in result.stderr


def test_a_program_is_read_from_a_file_on_disk(tmp_path: Path):
    source = tmp_path / "prog.blip"
    source.write_text(GOOD)

    result = run_blip_on_file(["--interpret"], str(source))

    assert result.returncode == 0
    assert json.loads(result.stdout) == ["ok"]


def test_a_diagnostic_names_the_file_it_was_read_from(tmp_path: Path):
    """Piped input is named `<stdin>`; a program read from a path has to be named by that path."""

    source = tmp_path / "bad.blip"
    source.write_text(SEMANTIC_ERROR)

    result = run_blip_on_file(["--check"], str(source))

    assert result.returncode != 0
    assert result.stderr.startswith(str(source))


def test_a_missing_file_is_reported_rather_than_raised(tmp_path: Path):
    """There is no source text to render a diagnostic against yet, but it still must not be a traceback."""

    missing = tmp_path / "nope.blip"

    result = run_blip_on_file(["--check"], str(missing))

    assert result.returncode != 0
    assert "nope.blip" in result.stderr
    assert "No such file or directory" in result.stderr
    assert "Traceback" not in result.stderr


def test_a_directory_given_in_place_of_a_file_is_reported(tmp_path: Path):
    """Reading this fails with a different `OSError`, so the handler cannot be keyed on the missing-file case alone."""

    result = run_blip_on_file(["--check"], str(tmp_path))

    assert result.returncode != 0
    assert "Traceback" not in result.stderr
