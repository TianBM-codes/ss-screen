"""Export external band-gap calculation candidates and validate gap results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from monty.serialization import dumpfn
from pymatgen.core import Composition

from ..data.io import load_group_df

GAP_RESULT_REQUIRED_COLUMNS = {
    "material_id",
    "formula",
    "method",
    "band_gap",
    "is_direct",
    "transition",
    "status",
}


def _formula(value: Any) -> str:
    if isinstance(value, Composition):
        return value.reduced_formula
    return str(value)


def _calculation_structure(row: pd.Series, structure_col: str):
    structure = row[structure_col]
    if (
        "primitive_structure" in row
        and row["primitive_structure"] is not None
        and not pd.isna(row["primitive_structure"])
    ):
        structure = row["primitive_structure"]
    return structure


def _structure_natoms(row: pd.Series, structure_col: str) -> int:
    structure = _calculation_structure(row, structure_col)
    return len(structure)


def export_gap_candidates(
    groups_path: str | Path,
    dataset_path: str | Path,
    output: str | Path,
    *,
    method: str = "external",
    structure_dir: str | Path | None = None,
    structure_col: str = "structure",
    max_natoms: int | None = None,
) -> pd.DataFrame:
    """Export unique group members for external high-level band-gap calculations."""
    groups = load_group_df(groups_path)
    dataset = pd.read_pickle(dataset_path)
    seen: set[str] = set()
    records: list[dict] = []

    if structure_dir is not None:
        Path(structure_dir).mkdir(parents=True, exist_ok=True)

    for group_index, group in enumerate(groups):
        for member_index, material_id in enumerate(group.mp_ids):
            material_id = str(material_id)
            if material_id in seen:
                continue
            seen.add(material_id)
            if material_id not in dataset.index:
                continue
            row = dataset.loc[material_id]
            natoms = _structure_natoms(row, structure_col)
            if max_natoms is not None and natoms > max_natoms:
                continue

            structure_path = ""
            if structure_dir is not None:
                path = Path(structure_dir) / f"{material_id}.json"
                dumpfn(_calculation_structure(row, structure_col), str(path))
                structure_path = str(path)

            composition = row.get("composition", group.compositions[member_index])
            records.append(
                {
                    "method": method,
                    "source_group_index": group_index,
                    "source_member_index": member_index,
                    "material_id": material_id,
                    "formula": row.get("formula", group.compositions[member_index]),
                    "composition": _formula(composition),
                    "initial_band_gap": row.get("band_gap", ""),
                    "e_hull": row.get("e_hull", row.get("energy_above_hull", "")),
                    "natoms": natoms,
                    "structure_path": structure_path,
                }
            )

    df = pd.DataFrame.from_records(
        records,
        columns=[
            "method",
            "source_group_index",
            "source_member_index",
            "material_id",
            "formula",
            "composition",
            "initial_band_gap",
            "e_hull",
            "natoms",
            "structure_path",
        ],
    )
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df


def validate_gap_results(path: str | Path) -> pd.DataFrame:
    """Validate the stable external high-level gap-result schema."""
    path = Path(path)
    if path.suffix.lower() == ".json":
        df = pd.read_json(path)
    else:
        df = pd.read_csv(path)
    missing = sorted(GAP_RESULT_REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"missing required gap-result columns: {', '.join(missing)}")
    df = df.copy()
    df["material_id"] = df["material_id"].astype(str)
    df["formula"] = df["formula"].astype(str)
    df["method"] = df["method"].astype(str)
    df["band_gap"] = pd.to_numeric(df["band_gap"], errors="coerce")
    df["status"] = df["status"].astype(str)
    return df
