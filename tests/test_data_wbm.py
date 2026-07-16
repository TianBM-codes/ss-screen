"""Tests for WBM dataset normalization."""

from __future__ import annotations

from ase import Atoms
from ase.io import write

from ssscreen.data.wbm import load_wbm_dataset


def test_load_wbm_dataset_normalizes_extxyz(tmp_path):
    xyz = tmp_path / "wbm.xyz"
    atoms = Atoms(
        "CaS",
        cell=[5.4, 5.4, 5.4],
        scaled_positions=[[0, 0, 0], [0.5, 0.5, 0.5]],
        pbc=True,
    )
    atoms.info.update(
        {
            "WBM_idx": 7,
            "WBM_gap": 0.25,
            "WBM_e_hull": 0.01,
            "WBM_step": 3,
        }
    )
    write(xyz, [atoms], format="extxyz")

    df = load_wbm_dataset(xyz_path=xyz, output=tmp_path / "wbm.df")

    assert list(df.index) == ["wbm-7"]
    row = df.loc["wbm-7"]
    assert row.formula == "CaS"
    assert row.reduced_composition.reduced_formula == "CaS"
    assert row.nelems == 2
    assert row.band_gap == 0.25
    assert row.e_hull == 0.01
    assert row.source == "wbm"
    assert row.source_metadata["step"] == 3
    assert len(row.structure) == 2
    assert (tmp_path / "wbm.df").exists()
