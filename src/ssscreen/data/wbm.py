"""WBM dataset normalization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pymatgen.io.ase import AseAtomsAdaptor


def _info_value(info: dict[str, Any], key: str, default=None):
    value = info.get(key, default)
    return value.item() if hasattr(value, "item") else value


def _material_id(info: dict[str, Any], index: int) -> str:
    if "material_id" in info:
        return str(info["material_id"])
    if "WBM_idx" in info:
        return f"wbm-{_info_value(info, 'WBM_idx')}"
    return f"wbm-{index}"


def _summary_metadata(summary: pd.DataFrame | None, index: int) -> dict:
    if summary is None or index >= len(summary):
        return {}
    row = summary.iloc[index]
    return {
        str(key): row[key].item() if hasattr(row[key], "item") else row[key] for key in row.index
    }


def load_wbm_dataset(
    *,
    xyz_path: str | Path,
    output: str | Path,
    summary_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load WBM extxyz structures into the normalized screening DataFrame schema."""
    try:
        from ase.io import read
    except ImportError as exc:
        raise ImportError(
            "The optional 'ase' dependency is required for `ss-screen dataset wbm`. "
            "Install it with `pip install -e '.[wbm]'`."
        ) from exc

    atoms_list = read(str(xyz_path), index=":")
    if not isinstance(atoms_list, list):
        atoms_list = [atoms_list]
    summary = (
        pd.read_csv(summary_path, sep=None, engine="python") if summary_path is not None else None
    )
    records = []
    adaptor = AseAtomsAdaptor()
    for index, atoms in enumerate(atoms_list):
        info = dict(atoms.info)
        structure = adaptor.get_structure(atoms)
        composition = structure.composition
        reduced = composition.get_reduced_composition_and_factor()[0]
        metadata = _summary_metadata(summary, index)
        metadata.update(
            {
                "wbm_index": _info_value(info, "WBM_idx", index),
                "step": _info_value(info, "WBM_step", None),
            }
        )
        records.append(
            {
                "material_id": _material_id(info, index),
                "formula": composition.reduced_formula,
                "composition": composition,
                "reduced_composition": reduced,
                "nelems": len(reduced),
                "band_gap": float(_info_value(info, "WBM_gap", metadata.get("gap", 0.0))),
                "e_hull": float(_info_value(info, "WBM_e_hull", metadata.get("e_hull", 0.0))),
                "structure": structure,
                "primitive_structure": structure.get_primitive_structure(),
                "source": "wbm",
                "source_metadata": metadata,
            }
        )
    df = pd.DataFrame.from_records(records).set_index("material_id")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(output)
    return df
