# AGENTS.md — Operating rules for AI assistants working on `ss-screen`

This file gives any AI agent (across sessions) a stable, authoritative set of
rules for working in this repository. Read it before doing anything else.

## 1. Repository scope — READ-ONLY boundary (HARD RULE)

**You may ONLY create, modify, or delete files inside `/home/bonan/work/HC/ss-screen/`.**

Every other path under `/home/bonan/work/HC/` is **READ-ONLY reference material**:

Paths below are relative to this file's location (`ss-screen/`), i.e. the
read-only siblings are at `../`.

| Path | Status | What it is |
|---|---|---|
| `./` (this dir, `ss-screen/`) | ✅ **READ-WRITE** (this package) | the formal package being built |
| `../pair-screening/` | 🔒 READ-ONLY | source of the envmatch/grouping algorithms |
| `../mp-condense/` | 🔒 READ-ONLY | source of the robocrys condense worker |
| `../wbm-dataset/` | 🔒 READ-ONLY | source of WBM data-prep logic |
| `../screen-mbj/`, `../screen-promising/`, `../screen-antiperovskite/` | 🔒 READ-ONLY | DFT-launcher reference logic |
| `../rocksalt/`, `../zincblend/`, `../Chalcopyrite /` | 🔒 READ-ONLY | prototype-study reference notebooks |
| `../simple-defects/` | 🔒 READ-ONLY | defect-ranking reference logic |
| `../old-screen-202411/` | 🔒 READ-ONLY | historical baseline snapshot |
| `../*.aiida`, `../*.tar.gz`, large data | 🔒 READ-ONLY | never touch |

**How to treat read-only dirs:** Read and study them, but **never write, edit,
rename, move, or delete anything outside `ss-screen/`.** Curated copies of
historical notebooks and source-code files may be added inside `ss-screen/`
(prefer `references/`) so the research provenance can be tracked with the
package. Preserve the original content where practical and record the source
path, snapshot date, and revision or checksum. Before copying, remove secrets
and generated/large data embedded in or adjacent to the source, and confirm
that its license permits redistribution. Full datasets, `.aiida` dumps,
archives, calculation outputs, and other large data remain external and must
not be copied or committed. Archived copies are historical references; the
tested code under `src/` remains canonical. If a fix logically belongs in a
read-only dir, instead fix it inside `ss-screen/` and note the upstream issue
in `docs/PROJECT_LOG.md` under "Upstream issues".

## 2. Mission (what we are building)

A formal, tested, documented Python package + CLI — **`ss-screen`** — for
**screening materials pairs that form solid-solutions (alloys) with tunable
band gaps**. Migrating the research workspace (notebooks + helper modules)
under `HC/` into a versioned package.

Full design lives in `docs/PROJECT_PLAN.md`. Always re-read it before planning
work — it is the source of truth for scope and milestones.

## 3. Cross-session continuity (MANDATORY)

Because this is a long-running project spanning many sessions:

- **At the start of any work session**, read (in this order):
  1. `AGENTS.md` (this file)
  2. `docs/PROJECT_LOG.md` (what has been done, what is next, any blockers)
  3. `docs/PROJECT_PLAN.md` (the blueprint & milestone status)
- **At the end of any work session** (or before handing off), append a dated
  entry to `docs/PROJECT_LOG.md` using the template in §5.

The project log is the single source of truth for *where we are*. Do not rely
on memory or on conversation history surviving between sessions.

## 4. Working conventions

- **Python ≥ 3.10**, `src/` layout, type hints, `ruff` + `black`.
- **No hardcoded paths.** All file locations come from CLI args or a config file.
- **No secrets in code.** MP API key via `MP_API_KEY` env var, never committed.
- **No magic numbers.** Numerical thresholds are named parameters (see `config.py`).
- **Cite sources.** When porting an algorithm from a read-only notebook, add a
  comment like `# ported from pair-screening/screening-binary.ipynb cell 15`.
- **Curate historical sources.** Store approved notebook/source snapshots under
  `references/` with provenance metadata; do not import secrets, generated
  outputs, dependency environments, archives, or full datasets.
- **Test everything ported** into `pair/`, `data/` (core). DFT/defect modules
  (`workflow/`, `defects/`) get smoke tests where feasible.
- **Commit hygiene.** Git commits only when the user asks. Keep the working
  tree clean of large data. Curated notebooks/source snapshots may be tracked
  under `references/`; datasets stay external and only tiny test fixtures are
  committed under `tests/data/`.
- **Don't commit** the multi-GB `.aiida` dumps, `*.tar.gz`, or full datasets.

## 5. PROJECT_LOG.md entry template

Append entries newest-first. Keep entries factual and concise.

```markdown
## YYYY-MM-DD — <short title>

**Goal of this session:** <one line>

**Done:**
- <bullet of concrete completed work, with file paths>

**Decisions / changes to plan:**
- <any deviation from PROJECT_PLAN.md, with rationale>

**Next up:** <the immediate next step(s)>

**Blockers / upstream issues:** <read-only-dir problems noticed but not fixed>
```

## 6. What NOT to do

- Do not run notebooks, DFT jobs, or AiiDA daemons unless explicitly asked.
- Do not `pip install` into the system environment without asking; prefer
  editable installs (`pip install -e .`) in the user environment.
- Do not delete or overwrite a file in `ss-screen/` you haven't Read first.
- Do not guess package names, skill names, or APIs — verify in the read-only
  source before porting.
- Do not treat prior session summaries as authoritative over `PROJECT_LOG.md`
  and `PROJECT_PLAN.md`; if they conflict, trust the docs and note the conflict.
