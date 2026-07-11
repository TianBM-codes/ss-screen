"""Composition-template grouping.

First stage of pair screening: bucket materials whose reduced compositions
share a common "fixed" part, leaving one element as the variable ``X`` site.
For a binary ``AxBy`` the templates are ``AxX`` and ``ByX`` (i.e. each element
in turn plays the role of X); for a ternary ``AxByCz`` there are three
templates.

Merges the divergent logic of ``screening-binary.ipynb`` cell 15 and
``screening-tenary.ipynb`` cell 5 into a single function parameterised by the
number of elements.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from pymatgen.core import Composition

from ..config import composition_permutations
from .envmatch import StructureGroup


def composition_template(comp: Composition) -> str:
    """Render the *fixed* part of a reduced composition as ``"A{...}B{...}"``.

    Used for display / debugging. The variable-element slot is appended by
    :func:`group_by_composition_template`.
    """
    return comp.reduced_formula


def _template_key(comp: Composition, permutation: list[int]) -> str:
    """Build the ``AxByX{n}`` template key for one permutation.

    ``permutation[-1]`` is the variable element; the leading indices are the
    spectator (fixed) elements. Reproduces cell 15 (binary) and cell 5
    (ternary) exactly.
    """
    elems = list(comp.keys())
    fixed = {elems[k]: comp[elems[k]] for k in permutation[:-1]}
    # Reduced formula of the fixed part (handles integer amounts), e.g.
    # {Ca:3} -> "Ca3", {} -> "" (only happens for elemental, out of scope).
    fixed_str = Composition(fixed).reduced_formula if fixed else ""
    x_amount = int(comp[elems[permutation[-1]]])
    return f"{fixed_str}X{x_amount}"


def group_by_composition_template(
    df: pd.DataFrame,
    nelems: int | None = None,
    *,
    index_col: str = "material_id",
    comp_col: str = "reduced_composition",
    bandgap_col: str = "band_gap",
    min_group_size: int = 2,
) -> dict[str, list[list]]:
    """Group rows of ``df`` by composition template (``AxByX`` etc.).

    Parameters
    ----------
    df
        Dataset with one row per material. Must contain ``comp_col``
        (pymatgen ``Composition``), ``bandgap_col`` (float, eV), and be indexed
        by ``index_col``.
    nelems
        Number of elements in the reduced composition (2 or 3). If ``None``,
        inferred per-row from ``len(comp_col)`` — but a fixed value is strongly
        recommended so the permutation set is consistent.
    min_group_size
        Drop templates with fewer than this many members (default 2: a template
        must have at least two structures to be a candidate for pairing).

    Returns
    -------
    dict mapping template key (``"CaX3"``) to a list of
    ``[material_id, x_element_symbol, band_gap]`` triples, sorted by nothing in
    particular (insertion order).

    Mirrors ``screening-binary.ipynb:15`` and ``screening-tenary.ipynb:5``.
    """
    if nelems is not None:
        permutations = composition_permutations(nelems)

    all_fixed_parts: dict[str, list[list]] = {}
    for index, row in df.iterrows():
        rd = row[comp_col]
        if nelems is None:
            perms = composition_permutations(len(rd))
        else:
            perms = permutations
        elems = list(rd.keys())
        for perm in perms:
            key = _template_key(rd, perm)
            x_elem = str(elems[perm[-1]])
            entry = [str(index), x_elem, float(row[bandgap_col])]
            all_fixed_parts.setdefault(key, []).append(entry)

    if min_group_size > 1:
        all_fixed_parts = {k: v for k, v in all_fixed_parts.items() if len(v) >= min_group_size}
    return all_fixed_parts


def attach_band_gaps(
    groups: Iterable[StructureGroup],
    template_entries: list[list],
) -> None:
    """Fill in each group's ``band_gaps`` from the template's ``[id, x, gap]`` rows.

    ``group.entry_idx`` indexes into ``template_entries``. Mutates the groups
    in place, matching upstream ``get_groups`` in
    ``screening-binary.ipynb:26``.
    """
    for group in groups:
        group.band_gaps = [template_entries[i][2] for i in group.entry_idx]
