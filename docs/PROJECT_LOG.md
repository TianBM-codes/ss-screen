# PROJECT_LOG.md — Cross-session project log for `ss-screen`

> **Purpose:** Keep this long-running project on track across many sessions.
> Append a dated entry at the end of every work session (newest first).
> This file + `PROJECT_PLAN.md` + `AGENTS.md` are the single source of truth
> for *where we are* — do not rely on conversation history surviving.

**Read first at the start of every session:** `AGENTS.md` → this file → `PROJECT_PLAN.md`.

## 2026-07-16 — Review remediation for staged CLI

**Goal of this session:** Address multi-agent review findings against the staged CLI implementation.

**Done:**
- Fixed `condense_paths()` in `src/ssscreen/data/condense.py` so unreadable input files are recorded as failed manifest/index rows instead of being silently dropped.
- Fixed `gap-export` in `src/ssscreen/pair/gap_export.py` so atom-count gating and exported structure JSON use the same primitive/calculation structure.
- Updated gap-result validation and feedback in `src/ssscreen/pair/gap_export.py` and `src/ssscreen/pair/gap_feedback.py` to accept CSV/JSON records, tolerate blank failed rows, and report gap shifts/directness changes in method comparisons.
- Added `src/ssscreen/data/wbm.py` and `ss-screen dataset wbm` for WBM extxyz normalization.
- Hardened `src/ssscreen/stability/sqs.py` and CLI validation so SQS target fractions must be in `[0, 1]`.
- Updated `README.md`, `docs/PROJECT_PLAN.md`, and the CLI roadmap to reflect the current extras, WBM loader, JSON gap files, and review remediations.

**Decisions / changes to plan:**
- Core dependencies remain small; WBM loading, condensation, MP live API, and SQS each live behind targeted extras.
- Historical `mp-offline` notes remain below, but this ss-screen entry is the current project handoff point.

**Next up:** Run full verification, then continue with Stage 7 MLP relaxation adapters or Stage 12 Chinese user guide work.

**Blockers / upstream issues:** No read-only reference files were modified.

## 2026-07-14 — mp-offline thermo review Task 2 corrections

**Goal of this session:** Correct thermo resume compatibility, row-count metadata, and fallback identity behavior in the shared `mp-offline` development checkout.

**Done:**
- Updated `mp-offline/mp-offline-develop/src/mp_offline/dump.py` to reject resumes when the saved JSON-canonical normalized summary query differs, seed compatible thermo resumes from the existing `thermo_entry` count, and use stable material-plus-canonical-scheme fallback thermo identities.
- Retained and documented the public one-shot `ThermoRester.search()` download behavior; no private pagination or streaming redesign was added.
- Added regression coverage in `mp-offline/mp-offline-develop/tests/test_dump_resume.py` and `tests/test_thermo_entries.py`.
- Recorded TDD and verification evidence in `/tmp/mp-offline-20260714-task2.md`; focused and full test suites completed with exit code zero.

**Decisions / changes to plan:**
- Same-material, same-canonical-scheme rows with no API thermo ID deduplicate even when mutable payload fields change; distinct schemes remain separate identities.

**Next up:** Continue only with explicitly requested thermo-cache plan tasks.

**Blockers / upstream issues:** No live Materials Project request, staging, or commit was performed.

## 2026-07-14 — mp-offline thermo review Task 1 corrections

**Goal of this session:** Implement Task 1 from the thermo review corrections plan in the shared `mp-offline` development checkout.

**Done:**
- Updated `mp-offline/mp-offline-develop/src/mp_offline/dump.py` so `--run-type` semantics use only scalar `energy_type`, persisted thermo schemes are canonicalized, and every downloaded row is checked against the selected cache scheme before it can be written.
- Updated `mp-offline/mp-offline-develop/src/mp_offline/client.py` and `src/mp_offline/cli.py` to reject scheme requests that conflict with the cache profile and reject orphaned `--run-type` options.
- Added focused regression coverage in `mp-offline/mp-offline-develop/tests/test_thermo_entries.py`, `tests/test_client.py`, and `tests/test_cli.py`.
- Recorded TDD and verification evidence in `/tmp/mp-offline-20260714-task1.md`; focused tests passed (`35 passed`).

**Decisions / changes to plan:**
- A returned thermo row outside the selected scheme raises before any batch persistence rather than being silently ignored.

**Next up:** Continue only with explicitly requested thermo-cache plan tasks.

**Blockers / upstream issues:** `uv run` cannot resolve the declared Python support range with `mp-api==0.46.4`, and `ruff` is absent from the existing virtualenv. No live Materials Project request, staging, or commit was performed.

## 2026-07-13 — mp-offline thermo implementation review

**Goal of this session:** Run independent reviews of thermo download compatibility, theory separation, and the local query/CLI surface.

**Done:**
- Launched three read-only reviewers against `mp-offline/mp-offline-develop`.
- Identified P1 gaps in returned-scheme validation, authoritative run-type semantics, summary resume compatibility, and thermo resume/identity behavior.
- Identified P2 usability/provenance gaps around wrong-scheme local queries and native `r2SCAN` normalization.

**Decisions / changes to plan:**
- No implementation changes were made during this review pass; the findings require a focused correction plan before further claims of theory-safe caching.

**Next up:**
- Decide the authoritative meaning of `--run-type`, then implement the P1 correction set with tests.

**Blockers / upstream issues:** No live Materials Project request or archive/database modification.

## 2026-07-13 — mp-offline Task 4 theory-aware local thermo queries

**Goal of this session:** Expose an explicit-scheme local thermo query and CLI command in the shared `mp-offline` development checkout.

**Done:**
- Added `MPOffline.query_thermo()` in `mp-offline/mp-offline-develop/src/mp_offline/client.py`, constrained to `MaterialThermoEntry` and using Task 1/3 canonical scheme and exact run-type matching helpers.
- Added `mp-offline list-thermo --thermo-type ...` with repeated material/run filters and a validated `thermo_entry` projection in `mp-offline/mp-offline-develop/src/mp_offline/cli.py`.
- Added focused regression tests in `mp-offline/mp-offline-develop/tests/test_client.py` and `mp-offline/mp-offline-develop/tests/test_cli.py`.
- Recorded TDD evidence in `/tmp/mp-offline-task-4-report.md`: RED `5 failed, 10 passed`; GREEN focused `15 passed`; full suite `61 passed`.

**Decisions / changes to plan:**
- Kept the implementation table-specific; no generic table abstraction was introduced.

**Next up:** Continue only with explicitly requested thermo-cache tasks.

**Blockers / upstream issues:** No live Materials Project request or cache/archive modification. No files were staged or committed.

## 2026-07-13 — mp-offline Task 3 thermo identity and exact filtering

**Goal of this session:** Preserve distinct current Materials Project thermo documents and make thermo run-type selection/resume metadata exact and canonical in the shared development checkout.

**Done:**
- Updated `mp-offline/mp-offline-develop/src/mp_offline/dump.py` to derive `payload-sha256:` fallback thermo IDs from canonical raw JSON, map before deduplication, use exact normalized run-type labels, and sort/deduplicate run types in `thermo_profile`.
- Added Task 3 regression coverage in `mp-offline/mp-offline-develop/tests/test_thermo_entries.py` for pure versus mixed GGA labels, exact mixed scheme selection, distinct no-ID payload persistence, and reordered/duplicated profile selections.
- Recorded TDD evidence in `/tmp/mp-offline-task-3-report.md`: RED `3 failed, 8 passed`; GREEN `11 passed`; full suite `56 passed`.

**Decisions / changes to plan:**
- Existing `thermo_entry.thermo_id` schema accepts the deterministic textual hash key, so Task 3 required no schema or migration change.

**Next up:** Continue only with explicitly requested thermo-cache tasks.

**Blockers / upstream issues:** `ruff` is unavailable in the existing test virtual environment; no dependencies were installed. No files were staged or committed.

## 2026-07-13 — mp-offline Task 2 thermo resume safety

**Goal of this session:** Repair Task 2 thermo downloading/profile-safe resume behavior in the shared `mp-offline` development checkout.

**Done:**
- Updated `mp-offline/mp-offline-develop/src/mp_offline/dump.py` to use only public thermo chunking arguments, enforce public thermo selection invariants, persist profiles/failures, and reject mismatched resumes before summary writes.
- Updated `mp-offline/mp-offline-develop/src/mp_offline/migration.py` metadata defaults and added focused regression coverage in `mp-offline/mp-offline-develop/tests/`.
- Recorded RED/GREEN evidence in `/tmp/mp-offline-task-2-report.md`; focused result: `12 passed`.

**Decisions / changes to plan:**
- A supplied `thermo_types` value enables thermo inclusion at the public `create_offline_db` boundary; `GGA_GGA+U_R2SCAN` remains one valid scheme.

**Next up:** Continue only with explicitly requested thermo theory-separation tasks.

**Blockers / upstream issues:** `uv run` cannot resolve the declared Python support range with `mp-api==0.46.4`; focused tests used the existing checkout virtual environment. No files were staged or committed.

## 2026-07-13 — mp-offline Task 1 thermo profile validation

**Goal of this session:** Implement the first thermo theory-separation task in the shared `mp-offline` development checkout.

**Done:**
- Added enum-backed `normalize_thermo_types` and `thermo_profile` in `mp-offline/mp-offline-develop/src/mp_offline/dump.py`.
- Updated `mp-offline/mp-offline-develop/src/mp_offline/cli.py` so `--thermo-type` implies thermo download and `--include-thermo` requires a scheme.
- Added focused validator and CLI tests in `mp-offline/mp-offline-develop/tests/`.
- Recorded RED/GREEN evidence in `/tmp/mp-offline-task-1-report.md`.

**Decisions / changes to plan:**
- Normalize against installed `ThermoType` values and exclude `UNKNOWN`; defer pagination, resume comparison, and exact run-type filtering to later tasks.

**Next up:** Implement Task 2 downloader contract and profile-safe resume behavior.

**Blockers / upstream issues:** No live Materials Project request or archive/database modification. No files were staged or committed.

---

## 2026-07-13 — Stage 6 stability SQS input artifacts

**Goal of this session:** Start the optional stability workflow by generating reusable alloy/SQS input artifacts from final pair results.

**Done:**
- Added `src/ssscreen/stability/sqs.py` with deterministic random-substitution alloy structure generation and JSONL manifest writing.
- Installed `icet==3.2` into `.venv` and added an `icet` SQS backend using `generate_sqs_from_supercells`.
- Added `ss-screen stability sqs-generate` in `src/ssscreen/cli/app.py`.
- Added tests in `tests/test_stability_sqs.py` and CLI coverage in `tests/test_cli.py`.
- Updated `README.md` and `plans/2026-07-12-cli-long-term-screening-roadmap-v1.md` with the Stage 6 command and artifact boundary.

**Decisions / changes to plan:**
- `stability sqs-generate` now supports `--backend random` for dependency-light fixtures and `--backend icet` for optimized SQS generation.
- The JSONL manifest is the reusable task queue for future MLP relaxation and stability-analysis backends.

**Next up:** Implement Stage 7 MLP relaxation manifest/result adapters, keeping actual GPU-heavy relaxation outside default CI.

**Blockers / upstream issues:** No read-only reference files were modified.

## 2026-07-13 — thermo theory-separation review

**Goal of this session:** Audit whether the `mp-offline` thermo cache can safely select, record, and expose one Materials Project thermodynamic theory scheme.

**Done:**
- Ran three independent read-only reviews of downloader/CLI behavior, schema/provenance, and local consumer APIs.
- Found that the current installed `mp-api==0.46.4` thermo search does not accept the downloader's private `_page` argument, so the implemented thermo download path is not compatible with that API contract.
- Found that resume can append entries from a different scheme while replacing global metadata, run-type matching is fuzzy, and public client/CLI query paths expose only summary records.

**Decisions / changes to plan:**
- Proposed a strict single-thermo-scheme cache policy: one explicitly selected `thermo_type` per database, where MP's `GGA_GGA+U_R2SCAN` is a valid scheme in its own right.
- Require exact normalized matching, immutable per-download provenance, and public `query_thermo` access before considering thermo data theory-safe.

**Next up:**
- Obtain user approval for the strict scheme-separation policy, then implement with TDD.

**Blockers / upstream issues:** No live Materials Project request was run. No archive/database files were modified.

## 2026-07-13 — Stage 5 external gap feedback and comparison

**Goal of this session:** Continue the staged CLI by feeding externally calculated band gaps back into final pair generation and comparing multiple theory levels.

**Done:**
- Added `src/ssscreen/pair/gap_feedback.py` for validated external gap-result ingestion, method selection, coverage reporting, and final pair CSV generation.
- Extended `ss-screen pair` in `src/ssscreen/cli/app.py` with `--gap-results`, `--method`, and `--summary` while preserving the legacy `--gaps` path.
- Added `ss-screen gap-compare` for method-specific pair CSVs and JSON comparison reports across external gap methods.
- Added Stage 5 tests in `tests/test_gap_feedback.py` and `tests/test_cli.py`.
- Updated `README.md` and `plans/2026-07-12-cli-long-term-screening-roadmap-v1.md` with the new Stage 5 command flow.

**Decisions / changes to plan:**
- External gap results are used as a transient high-level gap map during pair enumeration; the original PBE/database `StructureGroup.band_gaps` are not overwritten.
- Multiple methods in gap-result files require explicit method selection for single-method final pair generation; `gap-compare` owns cross-method comparison.

**Next up:** Start the optional Stage 6 SQS/stability artifact generator.

**Blockers / upstream issues:** No read-only reference files were modified.

## 2026-07-13 — mp-api offline cache surface audit

**Goal of this session:** Identify Materials Project API routes beyond summaries and thermo entries that can be represented in an offline cache.

**Done:**
- Inspected the installed `mp-api==0.46.4` route registry and document primary keys without making a live API request.
- Classified material, task, relationship, molecule, and large-artifact routes for future offline-cache support.
- Identified a generic versioned document cache plus a content-addressed artifact store as the forward-compatible extension path; retain dedicated tables only for high-value query models such as summaries and thermo entries.

**Decisions / changes to plan:**
- Keep `thermo_entry` separate because it models stable one-to-many material thermodynamic entries.
- Do not treat `MPRester.local_dataset_cache` as an application offline database; it is client-side caching for the package's dataset/delta-table mechanisms.

**Next up:**
- Select the first property caches needed by downstream screening, likely robocrys, electronic-structure metadata, and elasticity/dielectric/magnetism.

**Blockers / upstream issues:** Browser access to the official documentation was unavailable in this environment; the audit is based on the locally installed `mp-api==0.46.4` source. No live authenticated query was run, and archive/database files were not modified.

## 2026-07-13 — mp-offline thermo entries cache

**Goal of this session:** Expand `mp-offline` to cache Materials Project thermo entries separately from summary documents and support thermo/run-type selection.

**Done:**
- Added `mp-offline/mp-offline-develop/src/mp_offline/model.py` support for a `thermo_entry` table storing thermo docs, entries, energy type, entry types, and raw JSON payloads.
- Extended `mp-offline/mp-offline-develop/src/mp_offline/dump.py` with thermo search normalization, chunked thermo downloads, thermo row writes, local run-type filtering, and thermo metadata.
- Extended `mp-offline/mp-offline-develop/src/mp_offline/cli.py` with `--include-thermo`, repeated `--thermo-type`, and repeated `--run-type`.
- Added tests in `mp-offline/mp-offline-develop/tests/test_thermo_entries.py` and extended API contract/download/CLI tests.
- Updated `mp-offline/mp-offline-develop/README.md` with summary-vs-thermo behavior and examples.
- Verified with `MPLCONFIGDIR=/tmp/mpl-cache /tmp/mp-offline-thermo-venv/bin/python -m pytest -q` (`40 passed`).

**Decisions / changes to plan:**
- Do not pass `thermo_types` into `summary.search`; current `mp-api==0.46.4` exposes `thermo_types` on `ThermoRester.search`, not `SummaryRester.search`.
- Store thermo documents as separate cache records because one material summary can be associated with multiple phase-diagram entries/schemes.
- Treat `run_type` as a local filter over `energy_type`, `entry_types`, and `entries` keys.

**Next up:**
- Consider adding client/CLI query helpers for the `thermo_entry` table if downstream screening needs direct thermo-cache queries.

**Blockers / upstream issues:** No live Materials Project API query was run. Existing archive/database files were not modified.

## 2026-07-13 — Stage 3 structure matching command

**Goal of this session:** Add the explicit Stage 3 structure-matching command that consumes Stage 1 composition candidates and Stage 2 condensed JSON archives.

**Done:**
- Added `src/ssscreen/pair/structure_match.py` with `match_structure_candidates()`.
- Added `ss-screen structure-match --candidates ... --condensed-dir ... --output ... [--summary ...]`.
- Added tests in `tests/test_structure_match.py` covering environment grouping, X-element diversity, band-gap attachment, and missing condensed descriptions.
- Added CLI regression coverage in `tests/test_cli.py`.
- Updated `README.md` and `plans/2026-07-12-cli-long-term-screening-roadmap-v1.md`.

**Decisions / changes to plan:**
- `ss-screen structure-match` is the new staged path for Stage 3.
- The older `ss-screen group` command remains available as a legacy all-in-one path for now.
- Stage 3 summaries report candidate/template counts, missing descriptions, raw groups, final groups, grouped members, and the X-element diversity threshold.

**Next up:**
- Implement Stage 3a: export the union of matched group member structures/metadata for external high-level band-gap calculations.

**Blockers / upstream issues:** No read-only reference files were modified.

## 2026-07-12 — mp-offline MP API compatibility updates implemented

**Goal of this session:** Implement the `mp-offline` downloader/provenance updates needed for current `mp-api` compatibility.

**Done:**
- Updated `mp-offline/mp-offline-develop/src/mp_offline/dump.py` with normalized Materials Project summary kwargs, required field merging, chunked page iteration, incremental SQLite writes, idempotent material-id skipping, resume support, and richer download metadata.
- Updated `mp-offline/mp-offline-develop/src/mp_offline/migration.py` with expanded provenance metadata defaults for old and new caches.
- Updated `mp-offline/mp-offline-develop/src/mp_offline/cli.py` with `dump` options for fields, filters, GNoMe inclusion, chunking, resume, endpoint, database version, and `MP_API_KEY`.
- Added tests for download option normalization, resumable dumps, CLI dump options, and the installed `mp-api` contract.
- Updated `mp-offline/mp-offline-develop/README.md`, `pyproject.toml`, and the compatibility plan checklist.
- Verified with `MPLCONFIGDIR=/tmp/mpl-cache /tmp/mp-offline-develop-venv/bin/python -m pytest -q` (`33 passed`).

**Decisions / changes to plan:**
- Did not promote additional fields such as `density`, `volume`, `efermi`, or `has_props` because current workflow searches found no offline query requirement; they remain available in `json_data`.
- Set `mp_api>=0.46.4` and added contract tests instead of adding an upper bound.

**Next up:**
- Optional final code review/commit if the user wants this branch prepared for integration.

**Blockers / upstream issues:** No live Materials Project API query was run. The old archive and both `data/default.db` files were not modified; timestamps remained `2024-06-04 21:05:39.178801411 +0800`.

## 2026-07-12 — mp-offline MP API compatibility update plan

**Goal of this session:** Generate an implementation plan for `mp-offline` updates needed after the latest `mp-api` / Materials Project API audit.

**Done:**
- Added `mp-offline/mp-offline-develop/docs/superpowers/plans/2026-07-12-mp-offline-mp-api-compatibility-updates.md`.
- Covered downloader option normalization, chunked/resumable writes, provenance metadata, CLI controls, dependency contract tests, candidate promoted columns, and documentation/verification.
- Ran a placeholder scan on the new plan.

**Decisions / changes to plan:**
- Prioritize downloader/provenance compatibility before promoting additional schema columns.
- Keep implementation tests mocked/offline unless the user explicitly authorizes live Materials Project queries.

**Next up:**
- Execute the compatibility update plan, preferably with subagent-driven development.

**Blockers / upstream issues:** The `create-plan` validation script referenced by the planning skill is not present in this repository, so validation was manual.

## 2026-07-12 — mp-api 0.46.4 compatibility follow-up

**Goal of this session:** Inspect latest `mp-api` / Materials Project API behavior and identify updates needed for `mp-offline`.

**Done:**
- Verified the dedicated development environment is using `mp-api==0.46.4`, `emmet-core==0.87.1`, and `pymatgen==2026.5.4`.
- Reviewed current `MPRester` and `SummaryRester.search` signatures, including `db_version`, `local_dataset_cache`, `include_gnome`, `fields`, `all_fields`, `chunk_size`, and `num_chunks`.
- Ran read-only sub-agent audits of `mp-offline/mp-offline-develop` and the installed `mp-api` package surface.
- Identified follow-up updates needed around downloader chunking/resume behavior, credential documentation, required field handling, richer provenance metadata, and dependency compatibility bounds.

**Decisions / changes to plan:**
- Treat the existing schema migration work as compatible with current `mp-api`, but prioritize downloader/provenance improvements before adding more promoted columns.
- Keep old archive and database files untouched.

**Next up:**
- Implement a resumable/downloader-focused compatibility pass for `mp-offline/mp-offline-develop`.

**Blockers / upstream issues:** No live authenticated Materials Project query was run.

## 2026-07-12 — mp-offline migration system implemented

**Goal of this session:** Execute the `mp-offline` schema migration plan using subagent-driven development.

**Done:**
- Created branch `codex/mp-offline-schema-migration` in `mp-offline/mp-offline-develop`.
- Added `mp-offline/mp-offline-develop/src/mp_offline/migration.py` with `inspect_db()`, `migrate_db()`, schema versioning, metadata finalization, and v0-to-v1 `band_gap` backfill.
- Promoted `MaterialSummary.band_gap` and added `CacheMetadata` in `mp-offline/mp-offline-develop/src/mp_offline/model.py`.
- Updated `mp-offline/mp-offline-develop/src/mp_offline/dump.py` so promoted fields remain in raw `json_data` and fresh dumps are finalized through migration metadata.
- Updated `mp-offline/mp-offline-develop/src/mp_offline/client.py` with database inspection and a simple query wrapper.
- Updated `mp-offline/mp-offline-develop/src/mp_offline/cli.py` with `inspect`, `migrate`, safe repeated `--where` filters, and no `eval`.
- Added pytest coverage under `mp-offline/mp-offline-develop/tests/` for model mapping, migration idempotency, missing-path safety, client queries, CLI filters, and dump metadata.
- Updated `mp-offline/mp-offline-develop/README.md`, `pyproject.toml`, and the local design/plan docs under `mp-offline/mp-offline-develop/docs/superpowers/`.

**Decisions / changes to plan:**
- Kept `json_data` as the raw forward-compatible payload; explicit columns are indexed projections.
- Fixed final-review gaps by adding the full metadata contract and preventing `inspect_db()` / `migrate_db()` from creating empty SQLite files for missing paths.
- Did not commit changes, following the project rule that commits happen only when explicitly requested.

**Next up:**
- Optionally implement resumable Materials Project downloads using the new metadata table.
- Decide whether to stage/commit the `mp-offline` development branch changes.

**Blockers / upstream issues:** No live Materials Project API query was run. The old archive and both `data/default.db` files were not modified; final verification kept their timestamp at `2024-06-04 21:05:39.178801411 +0800`.

## 2026-07-12 — Stage 2 condensed JSON archive generation

**Goal of this session:** Implement Stage 2 archive generation and metadata management while preserving the per-material JSON storage layout used by `../mp-condense`.

**Done:**
- Added `docs/superpowers/plans/2026-07-12-stage-2-condense-archive.md`.
- Extended `src/ssscreen/data/condense.py` with DataFrame-driven condensation, atomic per-material JSON writes, JSONL manifest output, CSV index output, archive indexing, and archive validation.
- Extended `ss-screen condense` with `--df`, `--structure-column`, `--material-id-column`, `--limit`, `--manifest`, `--index`, and `--stop-on-error`.
- Added `ss-screen condense-index --condensed-dir ... --output ...`.
- Added `ss-screen condense-validate --condensed-dir ... --output ...`.
- Added `tests/test_condense_archive.py` and CLI regression tests for the new command surface.
- Installed the condense runtime into `.venv` and ran a real one-structure NaCl condensation smoke test at `/tmp/ss-screen-real-condense`, producing `condensed/smoke-nacl.json`, `manifest.jsonl`, `index.csv`, and a valid validation report.
- Updated the `condense` optional dependency constraints in `pyproject.toml` so modern installs use `matminer>=0.10.1` and `setuptools<81`, avoiding the robocrys/matminer runtime import failures seen with the default resolver choices.
- Updated `README.md` and `plans/2026-07-12-cli-long-term-screening-roadmap-v1.md`.

**Decisions / changes to plan:**
- Keep `condensed/{material_id}.json` as the primary artifact because concurrent workers can independently read, skip, and write files.
- Use JSONL manifest and CSV index sidecars for searchability/auditability instead of replacing the archive with one monolithic file.
- Marked Stage 2 and Stage 2a complete for the first reusable archive-management slice; optional merge/summarize/Parquet index can come later.

**Next up:**
- Refactor `ss-screen group` into the explicit Stage 3 structure-matching command, preferably consuming the Stage 1 composition-candidate CSV and Stage 2 condensed archive.
- Add attrition/missing-description reporting for Stage 3.

**Blockers / upstream issues:** The reference archive `../mp-condense/condensed` was read only for shape/scale checks (`145164` JSON files, about `1.4G`) and was not modified. The conda `work` environment still has an incompatible sklearn/numpy ABI for robocrys; use the project `.venv` for condense runtime checks.

## 2026-07-12 — mp-offline migration design and plan

**Goal of this session:** Review `mp-offline` development checkout and prepare a migration-system implementation plan.

**Done:**
- Used `/home/bonan/work/HC/ss-screen/mp-offline/mp-offline-develop` as the development base.
- Ran three parallel read-only sub-agent reviews covering usability, Materials Project downloading, and database API/schema migration.
- Added `mp-offline/mp-offline-develop/docs/superpowers/specs/2026-07-12-mp-offline-schema-migration-design.md`.
- Added `mp-offline/mp-offline-develop/docs/superpowers/plans/2026-07-12-mp-offline-schema-migration.md`.

**Decisions / changes to plan:**
- Treat explicit schema columns as indexed projections while preserving `json_data` as the raw forward-compatible payload.
- Implement migration and `band_gap` promotion before attempting resumable downloader changes.

**Next up:**
- Execute the migration implementation plan, preferably using subagent-driven task execution with TDD.

**Blockers / upstream issues:** No live Materials Project API query was run. The old archive and old database were not modified.

## 2026-07-12 — mp-offline compatibility audit

**Goal of this session:** Explore `mp-offline` and check compatibility with the latest installed Materials Project API without modifying the old archive.

**Done:**
- Located the private package at `mp-offline/mp-offline/` and inspected its metadata, README, SQLAlchemy model, dump path, client path, and CLI.
- Created a dedicated throwaway environment at `/tmp/mp-offline-latest-api-venv` and installed editable `mp_offline` against `mp-api==0.46.4`.
- Verified the bundled archive `mp-offline/mp-offline/data/default.db` is readable and contains 155,361 rows.
- Confirmed current `mp_api.client.routes.materials.summary.SummaryRester.search` still supports `energy_above_hull`, `band_gap`, `fields`, and `use_document_model=False` workflows needed by `mp_offline`.

**Decisions / changes to plan:**
- No source or archive changes were made to `mp-offline`; the compatibility result is an audit only.
- `mp_offline` remains usable for the historical screening workflow, but fields not mapped as SQL columns, notably `band_gap`, are stored in `json_data` and cannot be queried as `MaterialSummary.band_gap`.

**Next up:**
- If `mp_offline` is maintained further, update its README examples and consider mapping `band_gap` into `MaterialSummary` for SQL filtering.
- Prefer `ss-screen`'s direct `mp-api` loader for new data acquisition unless offline cache behavior is explicitly needed.

**Blockers / upstream issues:** No `MP_API_KEY` was present in the shell, so no live authenticated Materials Project query was run.

## 2026-07-12 — Stage 1 offline MP loader and composition screen start

**Goal of this session:** Start Stage 1 implementation with network-isolated MP data loading and separate composition screening from structure matching.

**Done:**
- Added `src/ssscreen/data/mp.py` with MP summary normalization, an offline `mp_offline` loader, and an explicit live API loader.
- Added `ss-screen dataset mp --output mp.df`, defaulting to `mp_offline` for network-isolated use.
- Added `ss-screen dataset mp --backend api --output mp.df`, using `MPRester()` without passing an explicit API key so `~/.pmgrc.yaml` / standard mp-api config can provide credentials when live access is desired.
- Added `screen_composition_candidates()` in `src/ssscreen/pair/grouping.py`.
- Added `ss-screen composition-screen --df ... --output ... [--summary ...]` to produce a machine-readable composition-candidate CSV and optional JSON summary before robocrys/envmatch structure matching.
- Added tests for MP normalization, offline loader injection, no-explicit-key API loader injection, `dataset mp`, and `composition-screen`.
- Updated `README.md` and `plans/2026-07-12-cli-long-term-screening-roadmap-v1.md` with the new command surface and current Stage 1 status.

**Decisions / changes to plan:**
- `mp_offline` is the default MP backend. The official Materials Project API remains an explicit `--backend api` path.
- `mp-api` is now an optional `mp` extra for the live API backend, keeping default CI free of live MP/network requirements.
- Stage 1 is partially complete: MP loading and composition screening are implemented; WBM loading remains.
- Stage 1a is marked complete for the first reusable CLI artifact because composition candidates can now be generated without condensed structure JSON.

**Next up:**
- Implement `src/ssscreen/data/wbm.py` and `ss-screen dataset wbm`.
- Refactor `ss-screen group` to optionally consume the composition-candidate CSV from `composition-screen`, so Stage 3 no longer repeats Stage 1a internally.

**Blockers / upstream issues:** Live Materials Project querying was not run in CI-style verification because it requires network access and user credentials; tests mock the `MPRester` boundary. The offline path was tested through a fake `mp_offline` client boundary rather than the full local SQLite database. Local untracked `mp-offline/` was added to `.gitignore` so lint does not scan a private/reference package accidentally.

## 2026-07-12 — Baseline commit and Stage 0 CLI CI cleanup

**Goal of this session:** Commit the current repository as a baseline, then start implementing the long-term CLI roadmap.

**Done:**
- Created baseline commit `d71aa25` (`Establish ss-screen baseline`) before making new implementation changes.
- Marked Stage 0 complete in `plans/2026-07-12-cli-long-term-screening-roadmap-v1.md`.
- Added a core GitHub Actions workflow in `.github/workflows/ci.yml` that installs the dev group and runs `ruff`, `black --check`, and `pytest` without optional DFT extras.
- Moved developer tools from the package `dev` extra into the `uv` `[dependency-groups].dev` section in `pyproject.toml`.
- Added `tests/test_project_config.py` so the dependency layout and CI workflow stay aligned with the core-only test path.
- Ran ruff cleanup and formatting on touched Python files.

**Decisions / changes to plan:**
- Stage 0 should keep default CI focused on the core CLI and tests; optional `condense`, `dft`, MLP, MP, and phonon dependencies stay outside the default CI path.
- The next implementation slice should move to Stage 1 / Stage 1a: normalized dataset inputs and composition-only screening artifacts before structure matching.

**Next up:**
- Implement the Stage 1 composition-screening/dataframe builder command surface with small fixtures and schema tests.
- Keep the Chinese user guide synchronized with the staged CLI artifact names once the Stage 1 outputs are stable.

**Blockers / upstream issues:** Local `uv` resolution still depends on network/cache availability in this environment; verification used the existing conda `work` Python plus `ruff`. Local `black` is not installed there, but CI installs it through the `uv` dev group.

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
