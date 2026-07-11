"""CLI tests for the ``ss-screen`` command surface."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from click.testing import CliRunner
from ssscreen.cli.app import cli

CLI_FIXTURES = Path(__file__).parent / "data" / "cli"


def test_cli_help_lists_current_commands():
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "valence-filter" in result.output
    assert "group" in result.output
    assert "pair" in result.output


def test_pair_command_compresses_missing_gap_members_in_lockstep(tmp_path):
    runner = CliRunner()
    output = tmp_path / "pairs.csv"

    result = runner.invoke(
        cli,
        [
            "pair",
            "--groups",
            str(CLI_FIXTURES / "pair_groups.json"),
            "--gaps",
            str(CLI_FIXTURES / "pair_gaps.csv"),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    df = pd.read_csv(output, index_col=0)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["comp_a"] == "CaS"
    assert row["comp_b"] == "CaSe"
    assert row["mp_id_a"] == "mp-low"
    assert row["mp_id_b"] == "mp-mid"
    assert str(row["gap_direct_a"]) == "False"
    assert str(row["gap_direct_b"]) == "True"


def test_condense_help_is_available():
    runner = CliRunner()

    result = runner.invoke(cli, ["condense", "--help"])

    assert result.exit_code == 0
    assert "--input" in result.output
    assert "--output-dir" in result.output


def test_condense_command_invokes_data_layer(monkeypatch, tmp_path):
    from ssscreen.data.condense import CondenseSummary

    runner = CliRunner()
    input_path = tmp_path / "mp-1.json"
    input_path.write_text("{}")
    output_dir = tmp_path / "condensed"
    calls = []

    def fake_condense_paths(inputs, output_dir_arg, overwrite=False):
        calls.append((inputs, output_dir_arg, overwrite))
        return CondenseSummary(written=1, skipped=0, failed=0)

    monkeypatch.setattr("ssscreen.data.condense.condense_paths", fake_condense_paths)

    result = runner.invoke(
        cli,
        [
            "condense",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [([input_path], output_dir, False)]
    assert "written=1" in result.output
    assert "skipped=0" in result.output
    assert "failed=0" in result.output
