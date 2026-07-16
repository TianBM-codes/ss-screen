"""CLI tests for the ``ss-screen`` command surface."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from click.testing import CliRunner
from monty.serialization import loadfn
from pymatgen.core import Composition, Lattice, Structure

from ssscreen.cli.app import cli
from ssscreen.pair.envmatch import StructureGroup

CLI_FIXTURES = Path(__file__).parent / "data" / "cli"


def _screening_df(rows):
    records = []
    for material_id, formula, band_gap, e_hull in rows:
        structure = Structure(
            Lattice.cubic(5.4),
            list(Composition(formula).as_dict().keys()),
            [[0, 0, 0]] * len(Composition(formula)),
        )
        comp = Composition(formula)
        records.append(
            {
                "material_id": material_id,
                "formula": formula,
                "composition": comp,
                "reduced_composition": comp.get_reduced_composition_and_factor()[0],
                "nelems": len(comp),
                "band_gap": band_gap,
                "e_hull": e_hull,
                "structure": structure,
                "source": "fixture",
            }
        )
    return pd.DataFrame.from_records(records).set_index("material_id")


def test_cli_help_lists_current_commands():
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "valence-filter" in result.output
    assert "group" in result.output
    assert "pair" in result.output
    assert "composition-screen" in result.output


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
    assert "--df" in result.output
    assert "--output-dir" in result.output


def test_condense_command_invokes_data_layer(monkeypatch, tmp_path):
    from ssscreen.data.condense import CondenseSummary

    runner = CliRunner()
    input_path = tmp_path / "mp-1.json"
    input_path.write_text("{}")
    output_dir = tmp_path / "condensed"
    calls = []

    def fake_condense_paths(
        inputs,
        output_dir_arg,
        overwrite=False,
        manifest_path=None,
        index_path=None,
        continue_on_error=True,
    ):
        calls.append(
            (inputs, output_dir_arg, overwrite, manifest_path, index_path, continue_on_error)
        )
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
    assert calls == [([input_path], output_dir, False, None, None, True)]
    assert "written=1" in result.output
    assert "skipped=0" in result.output
    assert "failed=0" in result.output


def test_condense_command_invokes_dataframe_archive_mode(monkeypatch, tmp_path):
    from ssscreen.data.condense import CondenseSummary

    runner = CliRunner()
    df_path = tmp_path / "mp.df"
    df_path.write_bytes(b"placeholder")
    output_dir = tmp_path / "condensed"
    manifest = tmp_path / "manifest.jsonl"
    index = tmp_path / "index.csv"
    calls = []

    def fake_condense_dataframe(**kwargs):
        calls.append(kwargs)
        return CondenseSummary(written=2, skipped=1, failed=0)

    monkeypatch.setattr("ssscreen.data.condense.condense_dataframe", fake_condense_dataframe)

    result = runner.invoke(
        cli,
        [
            "condense",
            "--df",
            str(df_path),
            "--structure-column",
            "structure",
            "--limit",
            "3",
            "--output-dir",
            str(output_dir),
            "--manifest",
            str(manifest),
            "--index",
            str(index),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        {
            "df_path": df_path,
            "output_dir": output_dir,
            "structure_col": "structure",
            "material_id_col": None,
            "limit": 3,
            "overwrite": False,
            "manifest_path": manifest,
            "index_path": index,
            "continue_on_error": True,
        }
    ]
    assert "written=2" in result.output
    assert "skipped=1" in result.output


def test_condense_index_command_writes_archive_index(monkeypatch, tmp_path):
    runner = CliRunner()
    condensed_dir = tmp_path / "condensed"
    condensed_dir.mkdir()
    output = tmp_path / "index.csv"
    calls = []

    def fake_build_archive_index(condensed_dir_arg, index_path):
        calls.append((condensed_dir_arg, index_path))
        return pd.DataFrame([{"material_id": "mp-1", "status": "present"}])

    monkeypatch.setattr("ssscreen.data.condense.build_archive_index", fake_build_archive_index)

    result = runner.invoke(
        cli,
        [
            "condense-index",
            "--condensed-dir",
            str(condensed_dir),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(condensed_dir, output)]
    assert "Indexed 1 condensed files" in result.output


def test_condense_validate_command_writes_validation_report(monkeypatch, tmp_path):
    runner = CliRunner()
    condensed_dir = tmp_path / "condensed"
    condensed_dir.mkdir()
    output = tmp_path / "validation.csv"
    calls = []

    def fake_validate_archive(condensed_dir_arg, index_path):
        calls.append((condensed_dir_arg, index_path))
        return pd.DataFrame(
            [
                {"material_id": "mp-1", "status": "valid"},
                {"material_id": "mp-2", "status": "invalid"},
            ]
        )

    monkeypatch.setattr("ssscreen.data.condense.validate_archive", fake_validate_archive)

    result = runner.invoke(
        cli,
        [
            "condense-validate",
            "--condensed-dir",
            str(condensed_dir),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(condensed_dir, output)]
    assert "valid=1" in result.output
    assert "invalid=1" in result.output


def test_composition_screen_writes_candidate_table_and_summary(tmp_path):
    runner = CliRunner()
    df = _screening_df(
        [
            ("mp-1", "CaS", 0.0, 0.0),
            ("mp-2", "CaSe", 0.3, 0.0),
            ("mp-3", "SrS", 0.4, 0.0),
            ("mp-4", "MgO", 0.1, 0.2),
            ("mp-5", "CaTe", 1.2, 0.0),
        ]
    )
    input_path = tmp_path / "dataset.df"
    output = tmp_path / "composition_candidates.csv"
    summary = tmp_path / "composition_summary.json"
    df.to_pickle(input_path)

    result = runner.invoke(
        cli,
        [
            "composition-screen",
            "--df",
            str(input_path),
            "--nelems",
            "2",
            "--max-bandgap",
            "1.0",
            "--max-e-hull",
            "0.01",
            "--output",
            str(output),
            "--summary",
            str(summary),
        ],
    )

    assert result.exit_code == 0, result.output
    candidates = pd.read_csv(output)
    assert set(candidates["template"]) == {"CaX1", "SX1"}
    assert set(candidates["material_id"]) == {"mp-1", "mp-2", "mp-3"}
    assert set(candidates.columns) >= {
        "template",
        "material_id",
        "x_element",
        "formula",
        "band_gap",
        "e_hull",
        "source",
    }

    report = loadfn(summary)
    assert report["input_rows"] == 5
    assert report["selected_rows"] == 3
    assert report["template_count"] == 2
    assert report["candidate_rows"] == 4


def test_dataset_mp_command_defaults_to_offline_loader(monkeypatch, tmp_path):
    runner = CliRunner()
    output = tmp_path / "mp.df"
    calls = []

    def fake_load_mp_dataset(output, max_e_hull, backend, offline_db):
        calls.append((output, max_e_hull, backend, offline_db))
        df = _screening_df([("mp-1", "CaS", 0.0, 0.0)])
        df.to_pickle(output)
        return df

    monkeypatch.setattr("ssscreen.data.mp.load_mp_dataset", fake_load_mp_dataset)

    result = runner.invoke(
        cli,
        [
            "dataset",
            "mp",
            "--output",
            str(output),
            "--max-e-hull",
            "0.02",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(output, 0.02, "offline", None)]
    assert "Wrote 1 MP rows" in result.output


def test_dataset_mp_command_accepts_explicit_api_backend(monkeypatch, tmp_path):
    runner = CliRunner()
    output = tmp_path / "mp.df"
    calls = []

    def fake_load_mp_dataset(output, max_e_hull, backend, offline_db):
        calls.append((output, max_e_hull, backend, offline_db))
        df = _screening_df([("mp-1", "CaS", 0.0, 0.0)])
        df.to_pickle(output)
        return df

    monkeypatch.setattr("ssscreen.data.mp.load_mp_dataset", fake_load_mp_dataset)

    result = runner.invoke(
        cli,
        [
            "dataset",
            "mp",
            "--backend",
            "api",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(output, 0.01, "api", None)]


def test_dataset_wbm_command_invokes_loader(monkeypatch, tmp_path):
    runner = CliRunner()
    xyz = tmp_path / "wbm.xyz"
    xyz.write_text("placeholder")
    output = tmp_path / "wbm.df"
    calls = []

    def fake_load_wbm_dataset(xyz_path, output, summary_path):
        calls.append((xyz_path, output, summary_path))
        df = _screening_df([("wbm-1", "CaS", 0.0, 0.0)])
        df.to_pickle(output)
        return df

    monkeypatch.setattr("ssscreen.data.wbm.load_wbm_dataset", fake_load_wbm_dataset)

    result = runner.invoke(
        cli,
        [
            "dataset",
            "wbm",
            "--xyz",
            str(xyz),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(xyz, output, None)]
    assert "Wrote 1 WBM rows" in result.output


def test_structure_match_command_writes_groups_and_summary(monkeypatch, tmp_path):
    runner = CliRunner()
    candidates = tmp_path / "composition_candidates.csv"
    candidates.write_text(
        "template,material_id,x_element,formula,composition,band_gap,e_hull,source\n"
    )
    condensed_dir = tmp_path / "condensed"
    condensed_dir.mkdir()
    output = tmp_path / "groups.json"
    summary = tmp_path / "summary.json"
    calls = []

    def fake_match_structure_candidates(candidates_arg, condensed_dirs, min_x_elements):
        calls.append((candidates_arg, condensed_dirs, min_x_elements))
        return (
            [
                StructureGroup(
                    entry_idx=[0, 1],
                    A_elements=[["Ca"], ["Ca"]],
                    compositions=["CaS", "CaSe"],
                    group_size=2,
                    X_element=["S", "Se"],
                    mp_ids=["mp-1", "mp-2"],
                    group_repr="descriptor",
                    band_gaps=[0.0, 0.3],
                )
            ],
            {
                "candidate_rows": 2,
                "template_count": 1,
                "missing_descriptions": 0,
                "raw_group_count": 1,
                "group_count": 1,
            },
        )

    monkeypatch.setattr(
        "ssscreen.pair.structure_match.match_structure_candidates",
        fake_match_structure_candidates,
    )

    result = runner.invoke(
        cli,
        [
            "structure-match",
            "--candidates",
            str(candidates),
            "--condensed-dir",
            str(condensed_dir),
            "--output",
            str(output),
            "--summary",
            str(summary),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(candidates, [condensed_dir], 2)]
    groups = loadfn(output)
    assert groups[0]["mp_ids"] == ["mp-1", "mp-2"]
    report = loadfn(summary)
    assert report["group_count"] == 1
    assert "Wrote 1 structure groups" in result.output


def test_gap_export_command_writes_candidate_table(monkeypatch, tmp_path):
    runner = CliRunner()
    groups = tmp_path / "groups.json"
    groups.write_text("[]")
    dataset = tmp_path / "dataset.df"
    dataset.write_bytes(b"placeholder")
    output = tmp_path / "gap_candidates.csv"
    structure_dir = tmp_path / "structures"
    calls = []

    def fake_export_gap_candidates(**kwargs):
        calls.append(kwargs)
        df = pd.DataFrame([{"material_id": "mp-1", "method": "hse06"}])
        df.to_csv(kwargs["output"], index=False)
        return df

    monkeypatch.setattr(
        "ssscreen.pair.gap_export.export_gap_candidates", fake_export_gap_candidates
    )

    result = runner.invoke(
        cli,
        [
            "gap-export",
            "--groups",
            str(groups),
            "--dataset",
            str(dataset),
            "--method",
            "hse06",
            "--structure-dir",
            str(structure_dir),
            "--max-natoms",
            "30",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        {
            "groups_path": groups,
            "dataset_path": dataset,
            "output": output,
            "method": "hse06",
            "structure_dir": structure_dir,
            "structure_col": "structure",
            "max_natoms": 30,
        }
    ]
    assert "Wrote 1 gap candidates" in result.output


def test_gap_validate_command_reports_schema_status(monkeypatch, tmp_path):
    runner = CliRunner()
    gaps = tmp_path / "gap_results.csv"
    gaps.write_text("material_id,formula,method,band_gap,is_direct,transition,status\n")
    calls = []

    def fake_validate_gap_results(path):
        calls.append(path)
        return pd.DataFrame([{"material_id": "mp-1"}])

    monkeypatch.setattr("ssscreen.pair.gap_export.validate_gap_results", fake_validate_gap_results)

    result = runner.invoke(cli, ["gap-validate", "--gaps", str(gaps)])

    assert result.exit_code == 0, result.output
    assert calls == [gaps]
    assert "Validated 1 gap-result rows" in result.output


def test_pair_command_accepts_external_gap_results_schema(monkeypatch, tmp_path):
    runner = CliRunner()
    groups = tmp_path / "groups.json"
    groups.write_text("[]")
    gaps = tmp_path / "gap_results.csv"
    gaps.write_text("material_id,formula,method,band_gap,is_direct,transition,status\n")
    output = tmp_path / "pairs.csv"
    summary = tmp_path / "summary.json"
    calls = []

    def fake_generate_pairs_from_gap_results(**kwargs):
        calls.append(kwargs)
        df = pd.DataFrame([{"mp_id_a": "mp-1", "mp_id_b": "mp-2"}])
        df.to_csv(kwargs["output"])
        return df, {"pair_count": 1, "covered_materials": 2, "materials_in_groups": 2}

    monkeypatch.setattr(
        "ssscreen.pair.gap_feedback.generate_pairs_from_gap_results",
        fake_generate_pairs_from_gap_results,
    )

    result = runner.invoke(
        cli,
        [
            "pair",
            "--groups",
            str(groups),
            "--gap-results",
            str(gaps),
            "--method",
            "hse06",
            "--summary",
            str(summary),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["groups_path"] == groups
    assert calls[0]["gap_paths"] == (gaps,)
    assert calls[0]["output"] == output
    assert calls[0]["summary"] == summary
    assert calls[0]["method"] == "hse06"
    assert "Wrote 1 pairs" in result.output


def test_gap_compare_command_writes_method_comparison(monkeypatch, tmp_path):
    runner = CliRunner()
    groups = tmp_path / "groups.json"
    groups.write_text("[]")
    gaps = tmp_path / "gap_results.csv"
    gaps.write_text("material_id,formula,method,band_gap,is_direct,transition,status\n")
    output_dir = tmp_path / "comparison"
    summary = tmp_path / "comparison.json"
    calls = []

    def fake_compare_gap_methods(**kwargs):
        calls.append(kwargs)
        kwargs["summary"].write_text("{}")
        return {"methods": ["hse06", "mbj"], "pair_counts": {"hse06": 1, "mbj": 0}}

    monkeypatch.setattr("ssscreen.pair.gap_feedback.compare_gap_methods", fake_compare_gap_methods)

    result = runner.invoke(
        cli,
        [
            "gap-compare",
            "--groups",
            str(groups),
            "--gap-results",
            str(gaps),
            "--output-dir",
            str(output_dir),
            "--summary",
            str(summary),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["groups_path"] == groups
    assert calls[0]["gap_paths"] == (gaps,)
    assert calls[0]["output_dir"] == output_dir
    assert calls[0]["summary"] == summary
    assert "Compared 2 methods" in result.output


def test_stability_sqs_generate_command_writes_artifacts(monkeypatch, tmp_path):
    runner = CliRunner()
    pairs = tmp_path / "pairs.csv"
    pairs.write_text("comp_a,comp_b,mp_id_a,mp_id_b\n")
    dataset = tmp_path / "dataset.df"
    dataset.write_bytes(b"placeholder")
    output_dir = tmp_path / "sqs"
    manifest = tmp_path / "manifest.jsonl"
    calls = []

    def fake_generate_sqs_inputs(**kwargs):
        calls.append(kwargs)
        kwargs["manifest_path"].write_text('{"status":"written"}\n')
        return [{"status": "written"}, {"status": "skipped"}]

    monkeypatch.setattr("ssscreen.stability.sqs.generate_sqs_inputs", fake_generate_sqs_inputs)

    result = runner.invoke(
        cli,
        [
            "stability",
            "sqs-generate",
            "--pairs",
            str(pairs),
            "--dataset",
            str(dataset),
            "--target-fraction",
            "0.25",
            "--target-fraction",
            "0.5",
            "--backend",
            "icet",
            "--cutoff",
            "4.0",
            "--sqs-steps",
            "10",
            "--supercell",
            "2,1,1",
            "--seed",
            "11",
            "--output-dir",
            str(output_dir),
            "--manifest",
            str(manifest),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        {
            "pairs_path": pairs,
            "dataset_path": dataset,
            "output_dir": output_dir,
            "manifest_path": manifest,
            "target_fractions": (0.25, 0.5),
            "supercell": (2, 1, 1),
            "seed": 11,
            "backend": "icet",
            "cutoffs": (4.0,),
            "sqs_steps": 10,
        }
    ]
    assert "written=1" in result.output
    assert "skipped=1" in result.output


def test_stability_sqs_generate_rejects_invalid_target_fraction(tmp_path):
    runner = CliRunner()
    pairs = tmp_path / "pairs.csv"
    pairs.write_text("comp_a,comp_b,mp_id_a,mp_id_b\n")
    dataset = tmp_path / "dataset.df"
    dataset.write_bytes(b"placeholder")

    result = runner.invoke(
        cli,
        [
            "stability",
            "sqs-generate",
            "--pairs",
            str(pairs),
            "--dataset",
            str(dataset),
            "--target-fraction",
            "1.1",
            "--output-dir",
            str(tmp_path / "sqs"),
            "--manifest",
            str(tmp_path / "manifest.jsonl"),
        ],
    )

    assert result.exit_code != 0
    assert "0.0<=x<=1.0" in result.output
