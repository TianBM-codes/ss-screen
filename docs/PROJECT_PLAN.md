# ss-screen — Project Plan

A formal Python package + CLI + documentation for **screening materials pairs that
form solid-solutions (alloys) with tunable band gaps**.

This document is the living blueprint for migrating the research workspace in
`/home/bonan/work/HC` (a collection of Jupyter notebooks and helper modules) into
a versioned, tested, documented package located at
`/home/bonan/work/HC/ss-screen`.

---

## 1. Scientific mission

Identify **isostructural prototype groups** in large materials databases (Materials
Project, WBM) such that:

- one endmember is a near-zero-gap semiconductor (`Eg < 0.1 eV`), and
- another endmember is a small *direct*-gap semiconductor (`0.1 < Eg < 0.8 eV`),

so that alloying (element substitution on the "variable" site `X`) tunes the gap
across the useful range. Promising pairs are then verified by high-fidelity DFT
band-structure calculations (HSE06 / mBJ) and ranked by cation vacancy formation
energies.

The central scientific insight encoded in the code: **group materials by a
robocrystallographer local-environment fingerprint in which the variable element
is relabeled to a placeholder `X`**, so that chemically distinct but
structurally identical prototypes collapse together. This is the `envmatch`
algorithm.

## 2. Current state (source workspace audit)

| Source dir | Stage | Reuse value |
|---|---|---|
| `pair-screening/envmatch.py` | Pair-screening core | **HIGH** — already modular; scientific heart |
| `pair-screening/datacollect.py` | Data loading | HIGH — dataset builders |
| `pair-screening/screening-*.ipynb` | Pair drivers | MEDIUM — logic to extract, paths to fix |
| `pair-screening/valence-filter.ipynb` | Pre-filter | MEDIUM — small reusable step |
| `pair-screening/pairing_mbj_*.ipynb` | Pair enumeration | MEDIUM — `gaps_valid` + pair builder |
| `mp-condense/condense.py`, `condense_one.py` | Robocrys condense worker | HIGH — already CLI-shaped, resumable |
| `mp-condense/combined_condensed.py` | Bundle JSONs | LOW — trivial helper |
| `wbm-dataset/convert_to_extxyz.py` | WBM data prep | MEDIUM — entry-to-summary matcher |
| `screen-mbj/*.ipynb` | AiiDA mBJ/HSE/PBE launch | MEDIUM (DFT extra) — launcher logic |
| `rocksalt/`, `zincblend/`, `Chalcopyrite /` | Prototype studies | LOW — keep as reference notebooks |
| `screen-antiperovskite/*.ipynb` | Combinatorial + hull | MEDIUM (DFT extra) |
| `screen-promising/*.ipynb` | HSE06 verification | MEDIUM (DFT extra) |
| `simple-defects/*.ipynb` | Vacancy ranking | MEDIUM (DFT extra) |
| `old-screen-202411/` | Baseline snapshot | LOW — historical reference only |

### Known defects to fix on migration
- `envmatch.StructureGroup.__getitem___` — misspelled dunder (3 trailing `_`); indexing silently broken.
- `screening-tenary.ipynb` ships a stale inlined copy of envmatch functions.
- Hardcoded relative paths everywhere (`wbm-dataset/condense/condensed`, `../mp-condense/condensed`).
- **Live Materials Project API key committed** in `screen-antiperovskite/satbility-mp.ipynb` and `simple-defects/` — must be externalized to env var.
- `condense.py` checkpoint copy has `if name ==` (missing `__main__`).
- Magic thresholds (`0.3/0.2/0.8 eV`, `natoms<30/45`, `e_hull<0.01`) scattered as literals.
- DFT-band-launcher functions (`launch_hse06`/`launch_mbj`/`get_upd*`) duplicated verbatim across 6+ notebooks; `rocksalt.ipynb` ≡ `zincblend.ipynb` cells 9–11.

## 3. Target package layout

```
ss-screen/
├── pyproject.toml              # packaging, deps, console_scripts, extras
├── README.md
├── LICENSE
├── src/ssscreen/
│   ├── __init__.py
│   ├── config.py               # central thresholds, element-exclusion lists, paths
│   ├── data/                   # data-layer (no AiiDA)
│   │   ├── __init__.py
│   │   ├── mp.py               # load_mp_dataset (MPOffline / mp_api)
│   │   ├── wbm.py              # load_wbm_data + entry-to-summary matcher
│   │   ├── condense.py         # robocrys StructureCondenser worker, resumable
│   │   └── io.py               # extxyz<->Structure, bundle_json_dir
│   ├── pair/                   # pair-screening core (no AiiDA)
│   │   ├── __init__.py
│   │   ├── envmatch.py         # find_unique_envs, group_similar_structures, StructureGroup
│   │   ├── grouping.py         # composition-template grouping (binary/ternary)
│   │   ├── filters.py          # valence filter, element exclusion, size/stability gates
│   │   └── pairing.py          # gaps_valid predicate + pair enumeration
│   ├── workflow/               # AiiDA / DFT factories  [extra: dft]
│   │   ├── __init__.py
│   │   ├── aiida.py            # init_aiida, GroupPathX helpers
│   │   ├── relax.py            # MACE relax + store
│   │   ├── bands.py            # make_bandstructure_updater(functional=hse06/mbj/pbe, soc, relax)
│   │   └── stability.py        # MP phase-diagram e_above_hull screening
│   ├── defects/                # vacancy ranking  [extra: dft]
│   │   ├── __init__.py
│   │   ├── elemental.py        # elemental reference builder
│   │   ├── vacancy.py          # SimpleVacancyWorkChain driver
│   │   └── ranking.py          # cation/anion split, formation-energy ranking
│   ├── cli/                    # click entry points
│   │   ├── __init__.py
│   │   ├── app.py              # main `ss-screen` group
│   │   ├── condense_cmd.py     # ss-screen condense
│   │   ├── pair_cmd.py         # ss-screen pair-screen
│   │   ├── bands_cmd.py        # ss-screen launch-bands  [dft]
│   │   └── defects_cmd.py      # ss-screen rank-defects [dft]
│   └── _schema.py              # dataclass schemas for result CSVs
├── tests/
│   ├── test_envmatch.py
│   ├── test_pairing.py
│   ├── test_grouping.py
│   ├── test_condense.py
│   └── data/                   # tiny fixtures (real robocrys JSONs)
├── docs/
│   ├── PROJECT_PLAN.md         # this file
│   ├── review_pair_screening.md   # technical review #1
│   ├── review_dft_workflow.md     # technical review #2
│   └── review_defects.md          # technical review #3
└── examples/
    └── (ported notebooks / scripts)
```

## 4. Dependency strategy

**Core** (pair-screening works standalone):
`pymatgen`, `pandas`, `numpy`, `monty`, `click`, `tqdm`. The core CLI consumes
pre-built data artifacts and pre-condensed structure JSONs without requiring
heavy workflow dependencies.

**Extras**:
- `mp`: official Materials Project live API backend (`mp-api`). The offline MP
  backend uses a separately installed/local `mp_offline` package and database.
- `wbm`: WBM extxyz loading (`ase`).
- `condense`: robocrys condensation (`robocrys`, compatible `matminer` /
  `setuptools` pins).
- `sqs`: optimized SQS generation (`ase`, `icet`).
- `dft`: AiiDA-driven verification + defects (`aiida`, `aiida-vasp`,
  `aiida-grouppathx`, `mace-torch`, `sumo`, `doped`). Add ABACUS and other
  calculator integrations here when their workflow modules land.

Install: `pip install ss-screen` (core) or install targeted extras such as
`pip install "ss-screen[mp,condense,sqs]"`.

## 5. Migration milestones (long-running roadmap)

The work is sequenced so each milestone is independently useful and testable.

### Milestone 0 — Scaffolding (small)
- `pyproject.toml`, package skeleton, `pre-commit`, ruff/black config.
- `git init`, `.gitignore` (exclude the multi-GB datasets & AiiDA `.aiida` files).
- README stub. **No** research data committed (only tiny test fixtures).

### Milestone 1 — Structure grouping core (Part 1, the scientific heart)  ← FIRST DELIVERABLE
- Port `envmatch.py` into `src/ssscreen/pair/envmatch.py`; fix `__getitem__` typo;
  add docstrings & type hints; **keep the `re` sanitization of `site['element']`**
  (the ternary inline copy drops it — see `docs/algorithm_structure_grouping.md` §6).
- Extract `group_by_composition_template(df, nelems)` from the binary/ternary
  notebooks into `pair/grouping.py` (de-duplicates the divergent copies).
- Move valence / element-exclusion / size filters into `pair/filters.py`.
- Centralize all thresholds & element lists in `config.py`.
- Unit tests with tiny real robocrys fixtures (sample a few `mp-condense/condensed/*.json`).
- CLI: `ss-screen group --df-mp ... --condensed-dirs ... --output groups.json`
  (outputs `StructureGroup`s only — **no pair enumeration here**).
- Spec reference: `docs/algorithm_structure_grouping.md`.

### Milestone 1b — Gap backfill + pair enumeration (Part 2, logical layer)
- Extract `gaps_valid(gaps, thresholds)` and `enumerate_pairs(...)` from
  `pairing_mbj_*.ipynb` into `pair/pairing.py` with the magic numbers becoming
  `Thresholds` dataclass params.
- Gap-source **must be a configurable input** (mBJ / VASP-HSE06 / ABACUS-HSE06), no hardcoded CSV name.
- Add coverage-rate monitoring + optional PBE fallback (current code silently drops
  members without a high-precision gap — see `docs/algorithm_gap_backfill_pairing.md` §4.3).
- `direct` stays an info column, not a hard filter (user-confirmed).
- CLI: `ss-screen pair --groups ... --gaps ... --output pairs.csv`.
- Spec reference: `docs/algorithm_gap_backfill_pairing.md`.

### Milestone 2 — Data layer
- Port `datacollect.py` → `data/mp.py`, `data/wbm.py`.
- Port `mp-condense/condense.py` + `condense_one.py` → `data/condense.py`;
  CLI: `ss-screen condense` (single file) and a batch mode.
- Port the entry-to-summary matcher from `convert_to_extxyz.py` into a tested
  `match_entries_to_summary(entries, df, tol)` helper in `data/io.py`.
- Externalize MP API key to `MP_API_KEY` env var.

### Milestone 3 — DFT workflow factories `[dft]` extra
- Single `make_bandstructure_updater(node, functional, soc, relax, ...)`
  replacing the 6+ duplicated `launch_*` functions.
- `init_aiida(family)` + GroupPathX helper, `relax_and_store(atoms, label)`.
- Stability screening (`e_above_hull` via pymatgen PhaseDiagram).
- CLI: `ss-screen launch-bands`.

### Milestone 4 — Defect ranking `[dft]` extra
- Elemental-reference builder; `SimpleVacancyWorkChain` driver;
  cation/anion-aware ranking; CSV schema.
- CLI: `ss-screen rank-defects`.

### Milestone 5 — Documentation & technical reviews
- Three technical review docs (pair-screening / DFT workflow / defects) — see
  `docs/review_*.md` — covering algorithm derivation, parameter choices,
  references to source notebooks, and limitations.
- User-guide docs; example notebook ports.

## 6. Conventions
- Python ≥3.10, `src/` layout.
- Type hints everywhere; `ruff` + `black`; tests via `pytest`.
- All file paths configurable (CLI args / config file), no hardcoded relative paths.
- No secrets in repo; MP key via env var.
- Numerical thresholds are named parameters, never inline literals.
- Original notebooks kept in `/home/bonan/work/HC/<orig>/` as reference; the
  package is the canonical, tested version.
