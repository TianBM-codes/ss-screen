"""Central configuration: numerical thresholds and element-exclusion lists.

All magic numbers that were scattered as inline literals across the source
notebooks live here as named, documented attributes of :class:`Thresholds`.
This is the single place to audit or tune the screening criteria.

Default values reproduce the research workspace defaults
(``pair-screening/screening-binary.ipynb`` and ``pairing_mbj_gaps_binary.ipynb``).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Sequence


# ---------------------------------------------------------------------------
# Element exclusion
# ---------------------------------------------------------------------------
# Default excluded elements: radioactive/toxic, common transition metals that
# rarely form the target narrow-gap semiconductors, and the lanthanide +
# actinide series (f-electron complexity, magnetism).
# Source: pair-screening/screening-binary.ipynb cell 29.
_DEFAULT_EXCLUDED = [
    # radioactive / toxic
    "U", "Th", "Po", "Tl", "Hg",
    "Np", "Pu", "Pa", "Pr",
    # transition metals (excluded in the binary screen)
    "Ti", "Fe", "Co", "Ni", "Mn", "Cr", "V",
    # non-metals that distort the chemistry
    "H",
    # lanthanides
    "La", "Ce", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm",
    "Yb", "Lu",
]

#: Frozen set used by :func:`ssscreen.pair.filters.apply_element_exclusion`.
DEFAULT_EXCLUDED_ELEMENTS: frozenset[str] = frozenset(_DEFAULT_EXCLUDED)


# ---------------------------------------------------------------------------
# Permutation indices for composition-template grouping
# ---------------------------------------------------------------------------
# For a reduced composition with ``nelems`` elements, the orderings in which
# each element is treated as the variable `X` site. Mirrors
# screening-binary.ipynb cell 15 ([[0,1],[1,0]]) and
# screening-tenary.ipynb cell 5 ([[0,1,2],[0,2,1],[1,2,0]]).
_PERMUTATIONS: dict[int, list[list[int]]] = {
    2: [[0, 1], [1, 0]],
    3: [[0, 1, 2], [0, 2, 1], [1, 2, 0]],
}


def composition_permutations(nelems: int) -> list[list[int]]:
    """Return the per-element-as-X permutations for a reduced composition.

    The last index in each permutation is the variable element; the leading
    indices are the fixed (spectator) elements.
    """
    if nelems not in _PERMUTATIONS:
        raise ValueError(
            f"Composition-template grouping only supports nelems in {sorted(_PERMUTATIONS)}; "
            f"got nelems={nelems}."
        )
    return [list(p) for p in _PERMUTATIONS[nelems]]


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SelectionThresholds:
    """Thresholds for the initial data selection (stage 1).

    Attributes mirror the filters in ``screening-binary.ipynb`` cells 9-12.
    """

    #: Number of elements in the reduced composition (2=binary, 3=ternary).
    nelems: int = 2
    #: Maximum PBE band gap (eV) to keep a material. Default 1.0 (cell 12).
    max_bandgap: float = 1.0
    #: Maximum energy above hull (eV/atom). Use a small negative value to keep
    #: only on-hull structures (``e_hull <= 0``), matching cell 12's ``<= 0.0``;
    #: use ``0.01`` to mirror ``MPOffline``'s query predicate.
    max_e_hull: float = 0.0


@dataclass(frozen=True)
class GroupThresholds:
    """Thresholds applied to environment groups (stages 3-4).

    Mirrors ``screening-binary.ipynb`` cells 26-29.
    """

    #: Minimum number of distinct X elements required in a group after
    #: environment matching (cell 26: ``len(np.unique(group.X_element)) > 1``).
    min_x_diversity: int = 2
    #: Require at least one zero-gap member (cell 29: ``any(x == 0 ...)``).
    require_zero_gap_member: bool = True


@dataclass(frozen=True)
class PairThresholds:
    """Thresholds for the pair-enumeration stage (stage 5).

    Mirrors ``pairing_mbj_gaps_binary.ipynb`` cells 6 and 8. Two distinct sets:
    the *group validity* rule (``gaps_valid``) and the *pair* rule.
    """

    # --- gaps_valid (cell 6): group must contain both kinds of member ---
    #: A "low" member has gap below this (eV). Default 0.15.
    low_gap: float = 0.15
    #: A "direct small-gap" member has gap in (direct_min, direct_max) eV.
    direct_min: float = 0.15
    direct_max: float = 1.5

    # --- pair enumeration (cell 8) ---
    #: A pair is kept if some member is below this (eV). Default 0.3.
    pair_any_below: float = 0.3
    #: ...and some member is above this (eV). Default 0.2.
    pair_any_above: float = 0.2
    #: ...and neither member exceeds this (eV). Default 0.8.
    pair_both_below: float = 0.8


@dataclass(frozen=True)
class Thresholds:
    """Aggregate of all screening thresholds.

    Build with :meth:`default` for the research defaults, or :meth:`with_nelems`
    to switch binary <-> ternary while keeping the rest.
    """

    selection: SelectionThresholds = field(default_factory=SelectionThresholds)
    group: GroupThresholds = field(default_factory=GroupThresholds)
    pair: PairThresholds = field(default_factory=PairThresholds)
    #: Maximum number of atoms in the primitive cell kept for DFT (cell 36/41:
    #: binary uses 30, ternary uses 45).
    max_natoms: int = 30
    #: Elements to exclude from A-positions and the X-position.
    excluded_elements: frozenset[str] = DEFAULT_EXCLUDED_ELEMENTS

    @staticmethod
    def default(nelems: int = 2) -> "Thresholds":
        """Research defaults for the given element count."""
        max_natoms = 30 if nelems == 2 else 45
        return Thresholds(
            selection=SelectionThresholds(nelems=nelems),
            max_natoms=max_natoms,
        )

    def with_nelems(self, nelems: int) -> "Thresholds":
        """Return a copy with ``nelems`` (and the matching natoms cap) set."""
        return replace(
            self,
            selection=replace(self.selection, nelems=nelems),
            max_natoms=30 if nelems == 2 else 45,
        )

    @property
    def excluded(self) -> set[str]:
        """The excluded-element set as a plain ``set`` (for easy membership tests)."""
        return set(self.excluded_elements)


def coerce_excluded(extra: Sequence[str] | None) -> frozenset[str]:
    """Helper for the CLI: merge user-supplied extras into the default set."""
    base = set(DEFAULT_EXCLUDED_ELEMENTS)
    if extra:
        base.update(extra)
    return frozenset(base)
