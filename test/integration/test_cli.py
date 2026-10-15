"""
Integration tests for the `blip` CLI.
"""

import json

import pytest

from test.integration.conftest import run_blip

LEXICAL_ERROR = "first = 1\nsecond = \u00a35\nret first\n"
SYNTAX_ERROR = 'a = "x"\nb = = "y"\n'
SEMANTIC_ERROR = 'x = "a"\nx = 1\nret x\n'
GOOD = 'ret "ok"\n'


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
