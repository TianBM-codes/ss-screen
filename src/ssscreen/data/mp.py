"""Materials Project dataset loading.

The default loader uses ``mp_offline`` so the CLI can run in network-isolated
environments. The live API loader is still available explicitly and uses
``MPRester()`` without passing an API key, so standard pymatgen/mp-api
configuration files such as ``~/.pmgrc.yaml`` can own credentials.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import pandas as pd
from pymatgen.core import Composition, Structure

MP_SUMMARY_FIELDS = [
    "material_id",
    "composition",
    "band_gap",
    "energy_above_hull",
    "structure",
]


def _get_value(doc: Any, key: str) -> Any:
    if isinstance(doc, dict):
        if key == "band_gap" and key not in doc and "json_data" in doc:
            return doc["json_data"]["band_gap"]
        return doc.get(key)
    if key == "band_gap" and not hasattr(doc, key) and hasattr(doc, "json_data"):
        return doc.json_data["band_gap"]
    return getattr(doc, key)


def _as_composition(value: Any) -> Composition:
    if isinstance(value, Composition):
        return value
    return Composition(value)


def _as_structure(value: Any) -> Structure:
    if isinstance(value, Structure):
        return value
    return Structure.from_dict(value)


def normalize_mp_documents(docs: Iterable[Any], *, source: str = "mp") -> pd.DataFrame:
    """Convert Materials Project summary documents to the screening schema."""
    records = []
    for doc in docs:
        material_id = str(_get_value(doc, "material_id"))
        composition = _as_composition(_get_value(doc, "composition"))
        structure = _as_structure(_get_value(doc, "structure"))
        reduced_composition = composition.get_reduced_composition_and_factor()[0]
        records.append(
            {
                "material_id": material_id,
                "formula": reduced_composition.reduced_formula,
                "composition": composition,
                "reduced_composition": reduced_composition,
                "nelems": len(composition),
                "band_gap": float(_get_value(doc, "band_gap")),
                "e_hull": float(_get_value(doc, "energy_above_hull")),
                "energy_above_hull": float(_get_value(doc, "energy_above_hull")),
                "structure": structure,
                "primitive_structure": structure.get_primitive_structure(),
                "source": source,
            }
        )
    if not records:
        return pd.DataFrame(
            columns=[
                "formula",
                "composition",
                "reduced_composition",
                "nelems",
                "band_gap",
                "e_hull",
                "energy_above_hull",
                "structure",
                "primitive_structure",
                "source",
            ]
        ).rename_axis("material_id")
    return pd.DataFrame.from_records(records).set_index("material_id")


def load_mp_dataset_offline(
    *,
    output: str | Path,
    max_e_hull: float = 0.01,
    offline_db: str | Path | None = None,
    offline_client_factory: Callable[..., Any] | None = None,
    material_summary_cls: Any | None = None,
) -> pd.DataFrame:
    """Load Materials Project summaries from ``mp_offline`` and write a pickle DataFrame."""
    if offline_client_factory is None or material_summary_cls is None:
        try:
            from mp_offline.client import MPOffline
            from mp_offline.model import MaterialSummary
        except ImportError as exc:  # pragma: no cover - depends on local optional package
            raise ImportError(
                "Offline MP loading requires mp_offline. Install the local mp-offline "
                "package or add it to PYTHONPATH."
            ) from exc

        offline_client_factory = offline_client_factory or MPOffline
        material_summary_cls = material_summary_cls or MaterialSummary

    client = (
        offline_client_factory(offline_db) if offline_db is not None else offline_client_factory()
    )
    try:
        criterion = material_summary_cls.energy_above_hull <= max_e_hull
    except TypeError:
        criterion = ("energy_above_hull<=", max_e_hull)
    docs = client.query_all(criterion)

    df = normalize_mp_documents(docs, source="mp-offline")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(output)
    return df


def load_mp_dataset_api(
    *,
    output: str | Path,
    max_e_hull: float = 0.01,
    rester_factory: Callable[[], Any] | None = None,
) -> pd.DataFrame:
    """Fetch live Materials Project summaries and write a normalized pickle DataFrame."""
    if rester_factory is None:
        try:
            from mp_api.client import MPRester
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ImportError(
                "Materials Project loading requires mp-api. Install `ss-screen[mp]`."
            ) from exc

        rester_factory = MPRester

    with rester_factory() as rester:
        docs = rester.materials.summary.search(
            energy_above_hull=(0, max_e_hull),
            fields=MP_SUMMARY_FIELDS,
        )

    df = normalize_mp_documents(docs, source="mp-api")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(output)
    return df


def load_mp_dataset(
    *,
    output: str | Path,
    max_e_hull: float = 0.01,
    backend: str = "offline",
    offline_db: str | Path | None = None,
    offline_client_factory: Callable[..., Any] | None = None,
    material_summary_cls: Any | None = None,
    rester_factory: Callable[[], Any] | None = None,
) -> pd.DataFrame:
    """Load Materials Project data using the selected backend."""
    if backend == "offline":
        return load_mp_dataset_offline(
            output=output,
            max_e_hull=max_e_hull,
            offline_db=offline_db,
            offline_client_factory=offline_client_factory,
            material_summary_cls=material_summary_cls,
        )
    if backend == "api":
        return load_mp_dataset_api(
            output=output,
            max_e_hull=max_e_hull,
            rester_factory=rester_factory,
        )
    raise ValueError(f"Unsupported MP backend: {backend}")


def write_mp_dataset(df: pd.DataFrame, output: str | Path) -> pd.DataFrame:
    """Write an already-normalized MP DataFrame and return it."""
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(output)
    return df
