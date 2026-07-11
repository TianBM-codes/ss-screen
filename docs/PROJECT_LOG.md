# PROJECT_LOG.md — Cross-session project log for `ss-screen`

> **Purpose:** Keep this long-running project on track across many sessions.
> Append a dated entry at the end of every work session (newest first).
> This file + `PROJECT_PLAN.md` + `AGENTS.md` are the single source of truth
> for *where we are* — do not rely on conversation history surviving.

**Read first at the start of every session:** `AGENTS.md` → this file → `PROJECT_PLAN.md`.

---

## 2026-07-12 — Long-term CLI screening roadmap

**Goal of this session:** Generate a comprehensive long-term CLI plan for reproducing notebook-like screening results through staged command-line artifacts.

**Done:**
- Added `plans/2026-07-12-cli-long-term-screening-roadmap-v1.md`.
- Structured the CLI roadmap into stages: CLI platform, dataset/composition screening, structure-description JSON archives, structure matching, external band-gap candidate export, external gap-result ingestion, final pair generation, multi-theory comparison, SQS generation, MLP relaxation, mixing enthalpy, phonon screening, MP phase-diagram/competing-phase checks, and final recommendation reports.
- Made explicit that high-level band-gap calculations remain outside the core CLI; the CLI exports candidates and later ingests externally calculated gap tables so different theory levels can be compared.

**Decisions / changes to plan:**
- The CLI should separate composition screening from structure matching rather than treating `group` as one opaque operation.
- Condensed robocrys JSON descriptions should become reusable archives with manifests, validation, merging, and summary commands.
- Preliminary MLP stability evaluation belongs after final pair generation and should be optional, backend-pluggable, and clearly labeled as screening rather than final thermodynamic proof.

**Next up:**
- Convert the long-term roadmap into the next executable short plan, likely starting with Stage 0 CI/dependency cleanup and Stage 1 composition-screening/dataframe builder commands.
- Keep the Chinese user guide aligned with these staged CLI artifacts once command names and schemas settle.

**Blockers / upstream issues:** The `create-plan` validation script expected at `./.forge/skills/create-plan/validate-plan.sh` is still absent, so the roadmap was manually checked for required structure and placeholder markers.

---

## 2026-07-11 — CLI-first implementation: condense command and CLI tests

**Goal of this session:** Shift implementation priority to the reusable CLI, update the plan, and continue with the next CLI slice.

**Done:**
- Added `plans/2026-07-11-cli-first-implementation-v1.md` and marked the completed CLI-first tasks.
- Added CLI regression fixtures in `tests/data/cli/` and `tests/test_cli.py`, covering `ss-screen --help`, the `pair` command's gap-compression behavior, and the new `condense` command surface.
- Added `src/ssscreen/data/condense.py` with optional-runtime robocrys condensation helpers and `CondenseSummary`.
- Added `ss-screen condense --input ... --output-dir ... [--overwrite]` to `src/ssscreen/cli/app.py`.
- Updated `README.md` and `docs/PROJECT_PLAN.md` so the canonical command names are `valence-filter`, `group`, `pair`, and `condense`.

**Decisions / changes to plan:**
- CLI command names are now frozen to the shorter current names (`group`, `pair`) rather than the older `group-screen` / `pair-screen` planning names.
- `robocrys` remains optional: default tests mock the data-layer entry point and do not import robocrys unless the real `condense` runtime path is used.

**Next up:**
- Add a CI baseline that runs core CLI/tests without `[dft]`.
- Continue M2 with MP/WBM DataFrame builders once the CLI test harness is stable.
- Draft the Chinese user guide around the now-stabilized CLI command names.

**Blockers / upstream issues:** `uv run pytest` currently tries to resolve optional `[dft]` dependencies or fetch packages in this environment; tests were run with `/home/bonan/miniconda3/envs/work/bin/python`, matching the existing project environment noted earlier.

---

## 2026-07-11 — Scope split into Chinese docs and reusable CLI/package

**Goal of this session:** Clarify the next work plan after recognizing `ss-screen` is two related projects, not only a package migration.

**Done:**
- Confirmed two workstreams: a Chinese technical documentation project for the screening process, and an English CLI/package project for CI-ready reuse.
- Confirmed language boundaries: technical report and user guide should be Chinese-first; CLI commands, parameters, Python APIs, docstrings, tests, and CI should remain English-first.
- Added `plans/2026-07-11-next-task-breakdown-v1.md` with the next task breakdown, covering project-scope cleanup, Chinese technical report, Chinese user guide, `ss-screen pair` CLI regression coverage, M2 `condense`, MP/WBM loaders, CI baseline, README cleanup, and logging.

**Decisions / changes to plan:**
- Treat `docs/algorithm_structure_grouping.md` and `docs/algorithm_gap_backfill_pairing.md` as Chinese algorithm appendices / evidence sources, not the final top-level technical report.
- Add a Chinese `docs/technical_report.md` and Chinese `docs/user_guide.md` as explicit documentation deliverables before expanding far into M2/M3.
- Keep README short and English-first, linking to the Chinese technical report and user guide.

**Next up:**
- Update `docs/PROJECT_PLAN.md` to encode the two-workstream roadmap and language rules.
- Draft `docs/technical_report.md` and `docs/user_guide.md` skeletons.
- Add the small `ss-screen pair` CLI regression test before implementing M2 `condense`.

**Blockers / upstream issues:** The `create-plan` validation script expected at `./.forge/skills/create-plan/validate-plan.sh` is not present in this repository, so the new plan was manually checked for required structure instead.

---

## Current status (snapshot)

- **Phase:** M0 + M1 complete. Pair-screening core shipped as installable CLI; `ss-screen pair` reproduces the notebook's 52 binary pairs exactly (52/52 identical rows).
- **Next milestone:** M2 — data layer (`data/mp.py`, `data/wbm.py`, `data/condense.py` CLI); the only thing M1 cannot do yet is *build* the input `.df` files (it consumes pre-built ones).

### Milestone tracker
- [x] **M0** — Scaffolding: `pyproject.toml`, `src/ssscreen/` skeleton, `.gitignore`, ruff/black, README, `git init`. DONE.
- [x] **M1** — Pair-screening core. DONE: `config.py`, `pair/{envmatch,grouping,filters,pairing}.py`, `data/io.py`, `cli/app.py` (3 commands), 41 tests passing, CLI reproduces research output. DONE.
- [ ] **M2** — Data layer: `data/mp.py`, `data/wbm.py`, `data/condense.py` (the `ss-screen condense` command); externalize MP key.
- [ ] **M3** — DFT workflow factories `[dft]`: `make_bandstructure_updater`, `init_aiida`, MACE relax, hull stability.
- [ ] **M4** — Defect ranking `[dft]`: elemental refs, vacancy driver, cation/anion ranking.
- [ ] **M5** — Docs & technical reviews: `docs/algorithm_structure_grouping.md` (Part 1) and `docs/algorithm_gap_backfill_pairing.md` (Part 2) already exist and are high-quality source-indexed; remaining: a top-level package user guide + cross-references.

---

## 2026-07-06 — Both specs peer-reviewed & revised (4 agents, all P0/P1/P2 fixed)

**Goal of this session:** Have independent agents audit the two algorithm specs; fix every issue found.

**Done:**
- Ran 4 parallel review agents: (1) Doc1 scientific accuracy, (2) Doc2 scientific accuracy,
  (3) Doc-vs-code consistency audit, (4) structure/readability for implementers. Personally
  re-verified every P0/P1 claim against source code with bash/python.
- **P0 fixes (hard errors that would mislead migration):**
  - **Ternary uses real mBJ, not HSE06** — `mbj-screen-ternery.ipynb` Cell 11 uses `metagga='mbj'`
    (verified). Rewrote Doc2 §3.2/§4.3/§7/§8 to reflect FOUR independent DFT lines (binary PBE,
    binary VASP-HSE06, binary ABACUS-HSE06, ternary mBJ), and that "mbj" in filenames means
    different methods for binary vs ternary.
  - **Calc-submission sizes wrong** — wrote "286/927 submitted"; actual submission is 665/1588
    (verified). 286/927 are the *gap-success* subset. Fixed Doc1 §6, Doc2 §1/§4.3.
  - **direct-not-filtered consequence disclosed** — measured: 54% of binary pairs & 71% of ternary
    pairs are both-indirect (verified). Added table + migration guidance to Doc2 §5.4.
  - **Interface contract contradiction** — Doc1 said band_gaps gets overwritten by mBJ; Doc2 actually
    creates a new `gaps_mbj` field AND rebuilds the group (dropping members). Aligned both docs:
    Doc1 §4 now documents band_gaps as dynamic PBE field + points to Doc2 §4.2 for the rebuild contract.
- **P1 fixes (scientific argument / self-consistency):**
  - "充分条件 → 逐级必要筛": Doc1 §2.2/§2.3 no longer calls envmatch a sufficient condition; both
    layers are now framed as successive necessary filters (envmatch only captures
    `(poly_formula, geometry.type)`, not space group/lattice/bowing → ≈same-prototype, not ≈alloyable).
  - Robustness rationale assumptions: Doc2 §1 now explicitly states the two assumptions (Vegard-like
    gap-vs-composition + consistent per-endmember DFT error) and when they break.
  - Physical-window vs engineering-threshold split: Doc2 §5.1 separates the *physical target window*
    (0~0.5 / 0~0.15 eV) from the *engineering thresholds* (0.15/1.5 group-level, 0.2/0.3/0.8 pair-level),
    notes group-vs-pair use different values by design, and flags the LOW_HI/MID_LO overlap +
    `any()` logic that can let through "neither-end-near-zero" pairs (with min/max fix suggestion).
- **P2 fixes (precision/structure):**
  - Added pipeline data-flow diagram (Doc1 §1) spanning both parts.
  - Fixed cell refs: abacus-hse-analysis is Cell 5 (was "Cell 8"); mbj-analysis is Cell 8.
  - Documented `material_id` extraction differs (`split()[1]` vs `split()[0]`) between analysis notebooks.
  - Doc1 §3.5 added boundary/exception handling (robocrys fail, X-disambiguation, missing condensed).
  - Doc1 §5 added "group-level gap-diversity gate" row (binary/ternary inconsistent) + natoms
    reclassified as post-grouping; §7 added template-construction inconsistency.
  - Doc1 §3.3 fixed swap_elem_by_X asymmetry note + CoO/NiO example; §3.2 fixed list-vs-tuple + §-ref.
  - Doc2 §5.3 flagged self-pairing (i,i) bug; §8 flagged direct-is-string-type gotcha.

**Decisions / changes to plan:**
- The "mBJ naming misnomer" is more severe than first thought: ternary genuinely IS mBJ (not just
  binary ABACUS-HSE06 mislabeled). Migration MUST let binary/ternary use different methods.
- direct-as-info-column is now flagged as a decision point needing re-evaluation (not settled),
  given 54–71% both-indirect pairs in current output.
- Note: M0+M1 code was shipped by a parallel session *during* this review (see next entry). The spec
  fixes above apply to `docs/`; the M1 code may need a follow-up pass to align with the corrected
  mBJ/ternary understanding (e.g. gap-source config should be per-system, not assume one global method).

**Next up:** Specs are now review-hardened. Check whether M1 code already reflects these corrections
(esp. the mBJ-vs-HSE06-per-system point and the direct-column consequence); if not, schedule a fix.

**Blockers / upstream issues:** none new — all issues were in our docs, not upstream code.

---

## 2026-07-06 — M0 + M1 shipped: installable CLI, 41 tests, reproduces notebook output

**Goal of this session:** Build the formal CLI package per the approved plan (full pipeline, AiiDA as optional extra, refactor envmatch first).

**Done:**
- **M0 scaffolding:** `pyproject.toml` (hatchling, `ss-screen` console script, `[condense]`/`[dft]`/`[dev]` extras), `.gitignore` (excludes `*.df`, `*.aiida`, `*.tar.gz`), `LICENSE` (MIT), `README.md`, `git init`.
- **M1 config** (`src/ssscreen/config.py`): `Thresholds` / `SelectionThresholds` / `GroupThresholds` / `PairThresholds` dataclasses + `DEFAULT_EXCLUDED_ELEMENTS` + `composition_permutations(nelems)`. All notebook magic numbers centralised.
- **M1 envmatch** (`pair/envmatch.py`): faithful port of `pair-screening/envmatch.py`; **fixed the `__getitem___`→`__getitem__` typo**; added `band_gaps` field, type hints, docstrings, `to_dict()`.
- **M1 grouping** (`pair/grouping.py`): merged binary (cell 15) + ternary (cell 5) into one `group_by_composition_template(df, nelems)`; plus `attach_band_gaps`.
- **M1 filters** (`pair/filters.py`): `is_valence_assignable`, `valence_filter` (valence-filter.ipynb cell 11), `apply_element_exclusion`, `has_gap_diversity`, `apply_size_gate`.
- **M1 pairing** (`pair/pairing.py`): `gaps_valid` + `enumerate_pairs` + `attach_gaps_and_compress` (the cell-4 lockstep compression) + `pairs_to_dataframe`.
- **M1 data/io** (`data/io.py`): `CondenseLoader`, `dump_group_df`, `load_group_df` (handles BOTH records-array AND pandas column-oriented JSON — the real `binary-group-df.json` is column-oriented), `read_mbj_gaps`, `write_pairs_csv`.
- **M1 CLI** (`cli/app.py`): three commands — `ss-screen valence-filter`, `ss-screen group`, `ss-screen pair` — all thresholds exposed as `--options` with research defaults.
- **M1 tests**: 41 tests across `test_{envmatch,grouping,pairing,filters}.py` using 4 real robocrys fixtures copied from `../mp-condense/condensed/` (CeSe2 polymorphs mp-1080296/0351 with identical env, mp-1080265/1080248 as different-env controls). **41/41 passing.**
- **End-to-end verification:** `ss-screen pair` on the real research data (`binary-group-df.json` + `mbj_gaps_binary_2025_0425_pmg_info.csv`) produces **52 pairs identical to `mbj_result_binary_20250426.csv`** (52/52 rows match as sets; no row only-in-ours or only-in-notebook).
- Package installed editable in conda env `work`: `pip install -e .` succeeded; `ss-screen --help` works.
- Re-found two pre-existing high-quality docs: `docs/algorithm_structure_grouping.md` (Part 1) + `docs/algorithm_gap_backfill_pairing.md` (Part 2) — these cover the M5 technical-review content already; integrated into the milestone tracker.

**Decisions / changes to plan:**
- The `pair` command needed `attach_gaps_and_compress` (new helper) because the notebook's cell-4 compresses the group's `compositions`/`mp_ids` in lockstep with gap availability — without it, `gaps[k]` misaligns with `compositions[k]`. Caught by the end-to-end smoke test, not unit tests (a gap in test coverage to note).
- `load_group_df` supports both JSON layouts because the real `binary-group-df.json` is pandas column-oriented (`{col: {row_idx: val}}`), not a records array — only discovered during the smoke test.
- Env `work` lacks `robocrys`; this does NOT block M1 (envmatch consumes pre-condensed JSON). Only the future `ss-screen condense` command (M2) will need robocrys → declared in the `[condense]` extra.
- `mp_offline` is a private package; M1's `group`/`pair` commands take pre-built `.df` pickles as input and do NOT require `mp_offline` at runtime. Data acquisition (M2) is what will use it.

**Next up:**
- **M2 — data layer**: `data/mp.py` (`load_mp_dataset`, ported from `datacollect.py`), `data/wbm.py` (`load_wbm_data`), `data/condense.py` (the `ss-screen condense` single-file + batch worker, ported from `mp-condense/condense.py` + `condense_one.py`). This removes the last "consume a pre-built df" limitation.
- Add a CLI integration test that runs `ss-screen pair` on a tiny committed fixture group_df + gaps CSV, so the lockstep-compression regression is covered going forward.

**Blockers / upstream issues (read-only dirs — do NOT fix there):**
- All previously-listed upstream issues remain (envmatch dunder FIXED in our copy; live MP API key still in `../screen-antiperovskite/satbility-mp.ipynb`; checkpoint `if name==` bug; launcher duplication). None block further work.
- `robocrys` absent from env `work` — only blocks M2's `condense` command at runtime, not development.

---

## 2026-07-06 — Part 2 spec refined: tunable-range rationale + pair-criteria restatement

**Goal of this session:** Incorporate the user's two key clarifications into `docs/algorithm_gap_backfill_pairing.md`.

**Done:**
- Added a new subsection in §1 — **"为什么对带隙做范围筛选是合理的（方法论的根基）"**. This captures the
  foundational rationale the user articulated: a solid-solution is a *continuous compositional range*, so DFT's
  systematic gap error gets absorbed into a *compositional shift* — we can still tune the alloy to hit the target
  gap window. This is why range-based gap screening is sound despite DFT error. Rewires §1 to show how Part 1
  (isostructural group → physical precondition for tunability) and Part 2 (gap-spanning pair → target window)
  together yield "alloyable AND tunable-to-target" candidates.
- Restated §5 pair criteria in clean physical terms per user: **one endmember near-zero gap, the other small-gap
  (e.g. 0–0.5 eV)**, so the alloy's gap can be continuously tuned across a small window (e.g. 0–0.15 eV).
  Restructured §5 into: §5.1 (the physical form we seek, the source of the criteria) → §5.2 (group-level) →
  §5.3 (pair-level, mapping the three thresholds to the §5.1 concepts) → §5.4 (direct) → §5.5 (output schema).
- Aligned §6 parameter table to the new terminology ("小带隙端" instead of "中等端"), with cross-refs to §5.1.
- Renumbered downstream subsections consistently.

**Decisions / changes to plan:**
- The "tunable range absorbs DFT error" rationale is now documented as the **methodological foundation** of the
  whole pipeline, not just a side note. Both spec docs should be read with this in mind.
- Pair criteria are now expressed as physical concepts (near-zero end / small-gap end / tunable-range cap) with
  the numeric thresholds (0.15/1.5/0.2/0.3/0.8) demoted to "numerical instances of these concepts" — consistent
  with the user's stance that exact thresholds are tunable sieves, not algorithm core.

**Next up:** both Part 1 & Part 2 specs are now content-complete. Proceed to Milestone 0 (scaffolding) + M1 (port envmatch).

**Blockers / upstream issues:** none new.

---

## 2026-07-06 — Part 2 algorithm spec written (gap backfill + pairing)

**Goal of this session:** Write the formal spec for Part 2 of the pipeline (high-precision gap computation → backfill into groups → pair enumeration), with code-backed evidence.

**Done:**
- Read all of `screen-mbj/`: `pbe-screen-binary.ipynb`, `hse-screen-binary.ipynb`, `mbj-screen-binary.ipynb`
  (ABACUS HSE06, incl. PBE cell-relax), `mbj-analysis.ipynb`, `abacus-hse-analysis.ipynb`. Cross-checked the three
  DFT lines (PBE / VASP-HSE06 / ABACUS-HSE06) and re-read both `pairing_mbj_gaps_*.ipynb`.
- Confirmed WBM dataset **does** carry PBE band gaps (`datacollect.py:69` `df_all['band_gap']=df_all.gap`,
  257489 rows, ~85% zero/metallic) — so Part 1's PBE gaps come from the DB itself for both MP and WBM.
- Measured **gap-source coverage** (key finding): binary group has 680 unique members, VASP-HSE06 (2025-0425)
  covers only 286 (42%), ABACUS-HSE06 (2025-0528) covers 504 (74%); ternary 1646 members, VASP-HSE06 covers 909 (55%).
  → The current pairing notebooks hardcode `*_2025_0425` (older, less-covered VASP-HSE06) and silently drop
  members without a high-precision gap via `.get()`→`None`→`is_valid` filter. This is the main reason the final
  pair counts are low (binary 52, ternary 299).
- Wrote `docs/algorithm_gap_backfill_pairing.md` — formal spec of Part 2 with full source-code index (§8).
  Key framing per user: (1) the high-precision functional (mBJ / VASP-HSE06 / ABACUS-HSE06) is a **configurable
  sieve parameter, not algorithm core**; (2) the gap-size criteria are tunable thresholds; (3) `direct` is an
  **info column, not a hard filter** (user-confirmed).

**Decisions / changes to plan:**
- Part 2's high-precision method is abstracted to a configurable input (not bound to any one functional) —
  matches the user's view that it's "a sieve parameter". Migration target: `config.py` + CLI arg, no hardcoded CSV name.
- Documented the "mBJ" naming misnomer: `mbj-screen-*.ipynb` actually runs ABACUS HSE06, and `mbj_gaps_*.csv`
  comes from VASP HSE06 — historical naming to clarify during migration.
- Coverage-rate monitoring + optional PBE fallback flagged as a migration must-do (avoid silent member drops).

**Next up:**
- With both Part 1 & Part 2 specs locked, proceed to Milestone 0 (scaffolding) + Milestone 1 (port envmatch core).
- Milestone scope clarification: `pair/pairing.py` (`gaps_valid` + `enumerate_pairs`) is now scoped to the
  Part-2 milestone (gap backfill + pairing), not M1 (which is grouping only).

**Blockers / upstream issues:** none new beyond those recorded in
`algorithm_gap_backfill_pairing.md` §8 (pairing hardcodes old CSV; silent member drop; `has_direct` misnomer).

---

## 2026-07-06 — Part 1 algorithm spec written (structure grouping)

**Goal of this session:** Extract the structure-grouping algorithm from the research notebooks with code-backed evidence; write a formal spec for Part 1 of the pipeline.

**Done:**
- Read all of `pair-screening/`: `envmatch.py`, `datacollect.py`, `screening-binary.ipynb` (42 cells),
  `screening-tenary.ipynb` (32 cells), `pairing_mbj_gaps_binary.ipynb`, `pairing_mbj_gaps_ternary.ipynb`,
  `valence-filter.ipynb`. Cross-checked against result CSVs/JSONs (`binary-group-df.json`, `ternary-group-df.json`,
  `mbj_gaps_*`, `mbj_result_*`).
- Diffed `envmatch.py` (module) vs the inlined copy in `screening-tenary.ipynb` Cell 17:
  only **one** behaviour-affecting difference (`find_unique_envs` regex sanitization of `site['element']` is
  present in the module, missing in the inline copy). All other diffs are cosmetic (dataclass vs dict,
  `compositions` vs `Compositions`, function name, `.tolist()`).
- Clarified the pipeline's **two-part split** with the user (driven by mBJ cost):
  - Part 1 = structure grouping via two-layer match (cheap, the scope of this doc);
  - Part 2 = mBJ gap computation + gap backfill into groups + pair enumeration (separate doc).
- Wrote `docs/algorithm_structure_grouping.md` — formal spec of Part 1 with full source-code index (§7).
  Key framing confirmed by user: the two-layer match (composition match → envmatch) is the **only** load-bearing,
  order-dependent skeleton; every other filter (e_hull, PBE-gap, valence, element exclusion, natoms) is a
  **movable/tunable gate** that only shrinks the candidate set.

**Decisions / changes to plan:**
- Part 1 deliverable is now scoped to **grouping only** (not pairing). Pair enumeration is Part 2 work.
  Milestone 1 in PROJECT_PLAN.md should be read as "port envmatch + grouping + filters"; the `pair/pairing.py`
  module (gaps_valid + enumerate_pairs) belongs to a Part-2 milestone (TBD).
- Confirmed the module version (`envmatch.py`) is the migration baseline; the ternary inline copy is a stale
  duplicate to discard.

**Next up:**
- Discuss & write Part 2 spec: mBJ gap source → backfill into groups → pair enumeration + gap criteria
  (incl. settling whether `direct` is a hard filter or an info column).
- After both specs are locked, proceed to Milestone 0 (scaffolding) + Milestone 1 (port envmatch core).

**Blockers / upstream issues:** none new (see entry below for the standing list).

---

## 2026-07-06 — Exploration complete & plan written

**Goal of this session:** Map the whole `HC/` workdir, understand the project, draft a packaging plan.

**Done:**
- Ran 4 parallel Explore subagents over all of `/home/bonan/work/HC/`:
  pair-screening core; structure-type dirs (rocksalt/zincblend/Chalcopyrite/antiperovskite);
  data-prep dirs (mp-condense, wbm-dataset); downstream dirs (screen-mbj, screen-promising, simple-defects, old-screen-202411).
- Identified the project as a 4-stage pipeline: **data → pair-screening → band-gap verification → defect ranking**.
  Core algorithm = `envmatch` (robocrystallographer local-environment fingerprinting with the variable element relabeled to `X`).
- Catalogued reusable code, duplication, and defects (see `PROJECT_PLAN.md` §2).
- Wrote full blueprint: `docs/PROJECT_PLAN.md` (target layout, dependency strategy, 5 milestones, conventions).
- Wrote `AGENTS.md` (operating rules; **READ-ONLY boundary** = only `ss-screen/` is writable).
- Wrote this log.

**Decisions / changes to plan:**
- User decisions recorded: **full pipeline** scope; AiiDA as optional `[dft]` extra;
  package location = `/home/bonan/work/HC/ss-screen`; **refactor envmatch first**.
- Package working name: `ss-screen` (import name `ssscreen`).

**Next up:**
- Milestone 0: `git init` in `ss-screen/`, `pyproject.toml`, `src/ssscreen/` skeleton, `.gitignore` (exclude GB-scale data & `.aiida`), ruff/black config, README stub.
- Milestone 1: port `pair-screening/envmatch.py` → `src/ssscreen/pair/envmatch.py`
  (fix `__getitem___` → `__getitem__`, add type hints + docstrings);
  extract `group_by_composition_template`, `gaps_valid`, `enumerate_pairs`, filters into their modules;
  centralize thresholds/element-lists in `config.py`;
  write unit tests with tiny real robocrys fixtures sampled from `mp-condense/condensed/`;
  wire `ss-screen pair-screen` CLI.

**Blockers / upstream issues (read-only dirs — do NOT fix there, note for migration):**
- `pair-screening/envmatch.py:132` — `__getitem___` misspelled (3 trailing `_`); indexing silently broken.
- `pair-screening/screening-tenary.ipynb` — stale inlined envmatch copy, diverges from module.
- Hardcoded relative paths throughout (`wbm-dataset/condense/condensed`, `../mp-condense/condensed`).
- **Live MP API key committed** in `screen-antiperovskite/satbility-mp.ipynb` and used in `simple-defects/` — must be externalized to `MP_API_KEY` env var in the package.
- `mp-condense/.ipynb_checkpoints/condense-checkpoint.py:31` — `if name ==` missing `__main__`.
- DFT launcher functions (`launch_hse06`/`launch_mbj`/`get_upd*`) duplicated verbatim across 6+ notebooks; `rocksalt.ipynb` ≡ `zincblend.ipynb` cells 9–11.

---

<!-- Append new entries above this line, newest first. Use the template from AGENTS.md §5. -->
