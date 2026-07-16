"""Tests for external band-gap candidate export and result schema."""

from __future__ import annotations

import pandas as pd
import pytest
from monty.serialization import loadfn
from pymatgen.core import Lattice, Structure

from ssscreen.data.io import dump_group_df
from ssscreen.pair.envmatch import StructureGroup
from ssscreen.pair.gap_export import export_gap_candidates, validate_gap_results


def _structure() -> Structure:
    return Structure(Lattice.cubic(5.4), ["Ca", "S"], [[0, 0, 0], [0.5, 0.5, 0.5]])


def _supercell_structure() -> Structure:
    structure = _structure().copy()
    structure.make_supercell((2, 1, 1))
    return structure


def _dataset() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "material_id": "mp-1",
                "formula": "CaS",
                "composition": "CaS",
                "band_gap": 0.0,
                "e_hull": 0.0,
                "structure": _structure(),
                "source": "fixture",
            },
            {
                "material_id": "mp-2",
                "formula": "CaSe",
                "composition": "CaSe",
                "band_gap": 0.3,
                "e_hull": 0.0,
                "structure": _structure(),
                "source": "fixture",
            },
        ]
    ).set_index("material_id")


def test_export_gap_candidates_writes_unique_metadata_and_structures(tmp_path):
    groups = [
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
    ]
    groups_path = tmp_path / "groups.json"
    dataset_path = tmp_path / "dataset.df"
    output = tmp_path / "gap_candidates.csv"
    structure_dir = tmp_path / "structures"
    dump_group_df(groups, groups_path)
    _dataset().to_pickle(dataset_path)

    exported = export_gap_candidates(
        groups_path,
        dataset_path,
        output,
        structure_dir=structure_dir,
        method="hse06",
    )

    assert list(exported["material_id"]) == ["mp-1", "mp-2"]
    assert set(exported.columns) >= {
        "method",
        "source_group_index",
        "material_id",
        "formula",
        "composition",
        "initial_band_gap",
        "e_hull",
        "natoms",
        "structure_path",
    }
    assert set(exported["method"]) == {"hse06"}
    assert (structure_dir / "mp-1.json").exists()
    assert (structure_dir / "mp-2.json").exists()


def test_export_gap_candidates_applies_atom_count_gate(tmp_path):
    groups = [
        StructureGroup(
            entry_idx=[0, 1],
            A_elements=[["Ca"], ["Ca"]],
            compositions=["CaS", "CaSe"],
            group_size=2,
            X_element=["S", "Se"],
            mp_ids=["mp-1", "mp-2"],
            group_repr="descriptor",
        )
    ]
    groups_path = tmp_path / "groups.json"
    dataset_path = tmp_path / "dataset.df"
    dump_group_df(groups, groups_path)
    _dataset().to_pickle(dataset_path)

    exported = export_gap_candidates(
        groups_path,
        dataset_path,
        tmp_path / "gap_candidates.csv",
        max_natoms=1,
    )

    assert exported.empty


def test_export_gap_candidates_writes_the_structure_used_for_atom_count_gate(tmp_path):
    groups = [
        StructureGroup(
            entry_idx=[0],
            A_elements=[["Ca"]],
            compositions=["CaS"],
            group_size=1,
            X_element=["S"],
            mp_ids=["mp-1"],
            group_repr="descriptor",
        )
    ]
    groups_path = tmp_path / "groups.json"
    dataset_path = tmp_path / "dataset.df"
    structure_dir = tmp_path / "structures"
    df = _dataset()
    df["primitive_structure"] = None
    df.at["mp-1", "structure"] = _supercell_structure()
    df.at["mp-1", "primitive_structure"] = _structure()
    dump_group_df(groups, groups_path)
    df.to_pickle(dataset_path)

    exported = export_gap_candidates(
        groups_path,
        dataset_path,
        tmp_path / "gap_candidates.csv",
        structure_dir=structure_dir,
        max_natoms=2,
    )

    exported_structure = loadfn(exported.loc[0, "structure_path"])
    assert exported.loc[0, "natoms"] == 2
    assert len(exported_structure) == 2


def test_validate_gap_results_accepts_stable_schema(tmp_path):
    path = tmp_path / "gap_results.csv"
    pd.DataFrame(
        [
            {
                "material_id": "mp-1",
                "formula": "CaS",
                "method": "hse06",
                "band_gap": 0.2,
                "is_direct": True,
                "transition": "G-G",
                "status": "success",
            }
        ]
    ).to_csv(path, index=False)

    results = validate_gap_results(path)

    assert list(results["material_id"]) == ["mp-1"]
    assert results.loc[0, "method"] == "hse06"
    assert results.loc[0, "band_gap"] == 0.2


def test_validate_gap_results_accepts_json_records(tmp_path):
    path = tmp_path / "gap_results.json"
    pd.DataFrame(
        [
            {
                "material_id": "mp-1",
                "formula": "CaS",
                "method": "hse06",
                "band_gap": 0.2,
                "is_direct": True,
                "transition": "G-G",
                "status": "success",
            }
        ]
    ).to_json(path, orient="records")

    results = validate_gap_results(path)

    assert list(results["material_id"]) == ["mp-1"]


def test_validate_gap_results_rejects_missing_required_columns(tmp_path):
    path = tmp_path / "bad_gap_results.csv"
    pd.DataFrame([{"material_id": "mp-1", "band_gap": 0.2}]).to_csv(path, index=False)

    with pytest.raises(ValueError, match="missing required gap-result columns"):
        validate_gap_results(path)


def test_validate_gap_results_allows_blank_band_gap_for_failed_rows(tmp_path):
    path = tmp_path / "gap_results.csv"
    pd.DataFrame(
        [
            {
                "material_id": "mp-1",
                "formula": "CaS",
                "method": "hse06",
                "band_gap": "",
                "is_direct": "",
                "transition": "",
                "status": "failed",
            }
        ]
    ).to_csv(path, index=False)

    results = validate_gap_results(path)

    assert pd.isna(results.loc[0, "band_gap"])
