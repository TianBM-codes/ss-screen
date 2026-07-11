"""Robocrys condensation helpers for ``ss-screen condense``.

This ports the single-structure / batch condensation pattern from the read-only
reference scripts ``mp-condense/condense_one.py`` and ``mp-condense/condense.py``.
The optional ``robocrys`` dependency is imported only inside the runtime path so
the core package and default tests do not need it installed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from monty.serialization import dumpfn, loadfn
from pymatgen.core import Structure


@dataclass(frozen=True)
class CondenseSummary:
    """Counts from a condensation run."""

    written: int = 0
    skipped: int = 0
    failed: int = 0


def expand_input_paths(inputs: Sequence[str | Path]) -> list[Path]:
    """Expand input files/directories into a deterministic file list."""
    paths: list[Path] = []
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            paths.extend(
                sorted(p for p in path.iterdir() if p.is_file() and not p.name.startswith("."))
            )
        else:
            paths.append(path)
    return paths


def load_structure(path: str | Path) -> Structure:
    """Load a pymatgen Structure from a Monty JSON or pymatgen-readable file."""
    path = Path(path)
    try:
        obj = loadfn(str(path))
        if isinstance(obj, Structure):
            return obj
        if isinstance(obj, dict):
            return Structure.from_dict(obj)
    except Exception:
        pass
    return Structure.from_file(str(path))


def _make_condenser():
    try:
        from robocrys import StructureCondenser
    except ImportError as exc:
        raise ImportError(
            "The optional 'robocrys' dependency is required for `ss-screen condense`. "
            "Install it with `pip install -e '.[condense]'`."
        ) from exc
    return StructureCondenser()


def condense_structure(structure: Structure, condenser=None) -> dict:
    """Condense one structure with robocrys."""
    condenser = condenser or _make_condenser()
    try:
        structure.add_oxidation_state_by_guess()
    except Exception:
        pass
    return condenser.condense_structure(structure)


def condense_paths(
    inputs: Sequence[str | Path],
    output_dir: str | Path,
    *,
    overwrite: bool = False,
) -> CondenseSummary:
    """Condense input structure files into ``{material_id}.json`` outputs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    condenser = _make_condenser()

    written = skipped = failed = 0
    for path in expand_input_paths(inputs):
        outpath = output_dir / f"{path.stem}.json"
        if outpath.exists() and not overwrite:
            skipped += 1
            continue
        try:
            structure = load_structure(path)
            condensed = condense_structure(structure, condenser=condenser)
            dumpfn(condensed, str(outpath))
            written += 1
        except Exception:
            failed += 1
    return CondenseSummary(written=written, skipped=skipped, failed=failed)
