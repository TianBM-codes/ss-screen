# ss-screen

Screen **materials pairs that form solid-solutions (alloys) with tunable band gaps**.

`ss-screen` packages the screening pipeline developed in the `HC/` research
workspace into a tested, documented command-line tool. It identifies
isostructural prototype groups in large materials databases (Materials Project,
WBM) where one endmember is near-zero-gap and another is a small direct-gap
semiconductor — candidates for gap tuning via alloying.

## Scientific core

Materials are grouped by a **robocrystallographer local-environment fingerprint**
in which the variable (alloyed) element is relabeled to a placeholder `X`, so
chemically distinct but structurally identical prototypes collapse together.
A group is *promising* when it contains both a near-zero-gap member and a
small direct-gap member.

## Install

```bash
pip install -e .
# To query Materials Project directly with --backend api:
pip install -e ".[mp]"
# To load WBM extxyz files:
pip install -e ".[wbm]"
# To also run the robocrys condensation step:
pip install -e ".[condense]"
# To generate optimized SQS candidates with icet:
pip install -e ".[sqs]"
```

## CLI

```bash
ss-screen --help

# Stage 1: build a normalized Materials Project DataFrame from mp_offline
# This requires the local mp_offline package/database to be available.
ss-screen dataset mp --output mp.df

# Optional live Materials Project query. Credentials may come from ~/.pmgrc.yaml.
ss-screen dataset mp --backend api --output mp.df

# Stage 1: build a normalized WBM DataFrame from extxyz
ss-screen dataset wbm --xyz wbm-dataset.xyz --output wbm.df

# Stage 1a: screen composition-template candidates before structure matching
ss-screen composition-screen \
  --df mp.df --nelems 2 \
  --output composition_candidates.csv \
  --summary composition_summary.json

# Optional: pre-filter metallic / mixed-valence structures
ss-screen valence-filter --df-mp mp.df --df-wbm wbm.df --output valid_ids.json

# Stage 2: build robocrys condensed JSON inputs for grouping
ss-screen condense \
  --df mp.df \
  --output-dir condensed/ \
  --manifest condensed_manifest.jsonl \
  --index condensed_index.csv

# Optional: index or validate an existing condensed JSON archive
ss-screen condense-index --condensed-dir condensed/ --output condensed_index.csv
ss-screen condense-validate --condensed-dir condensed/ --output condensed_validation.csv

# Stage 3: match composition candidates by structure/environment fingerprint
ss-screen structure-match \
  --candidates composition_candidates.csv \
  --condensed-dir condensed/ \
  --output group_df.json \
  --summary structure_match_summary.json

# Stage 3a: export structures/metadata for external high-level band-gap calculations
ss-screen gap-export \
  --groups group_df.json \
  --dataset mp.df \
  --method hse06 \
  --structure-dir gap_structures/ \
  --output gap_candidates.csv

# Stage 4: validate externally calculated gap results before feedback
ss-screen gap-validate --gaps gap_results.csv

# Stage 5: enumerate promising alloying pairs from computed gaps
ss-screen pair \
  --groups group_df.json \
  --gap-results gap_results.csv \
  --method hse06 \
  --summary gap_feedback_summary.json \
  --output final_pairs.csv

# Stage 5a: compare final pair lists from multiple theory levels
ss-screen gap-compare \
  --groups group_df.json \
  --gap-results gap_results.csv \
  --output-dir gap_method_comparison/ \
  --summary gap_method_comparison.json

# Stage 6: generate preliminary alloy/SQS input artifacts for stability screening
ss-screen stability sqs-generate \
  --pairs final_pairs.csv \
  --dataset mp.df \
  --backend icet \
  --target-fraction 0.5 \
  --cutoff 4.0 \
  --sqs-steps 10000 \
  --supercell 2,2,2 \
  --output-dir sqs_structures/ \
  --manifest sqs_manifest.jsonl

# Legacy notebook-style gap CSVs are still accepted:
ss-screen pair --groups group_df.json --gaps mbj_gaps.csv --output mbj_result.csv
```

All numerical thresholds (band-gap windows, atom-count caps, excluded elements)
are exposed as CLI options with research-default values; pass `--help` on any
command to see them. The `condense` command requires the optional `condense`
extra because it uses robocrys at runtime. Condensed structures are stored as
one JSON file per material (`condensed/{material_id}.json`) so multiple workers
can read, skip, and write independent files concurrently; manifest/index CSV
sidecars provide searchable metadata without replacing the per-material files.
The Stage 6 `stability sqs-generate` command supports a dependency-light
`--backend random` mode and an optimized `--backend icet` mode. The manifest
records which generator was used, together with backend limitations and
provenance needed by later MLP relaxation stages.

## Documentation

- `docs/PROJECT_PLAN.md` — full design and milestone roadmap
- `docs/PROJECT_LOG.md` — cross-session progress log
- `AGENTS.md` — operating rules for AI assistants (read-only boundaries)
- `references/README.md` — curated historical notebooks/source with executed results
- `references/manifest.json` — machine-readable provenance, hashes, aliases, redactions, and exclusions

The `references/` archive is historical evidence, not canonical runtime code.
Large datasets, calculation directories, archives, `.aiida` data, generated
scheduler artifacts, and secrets remain external.

## Status

The staged CLI currently covers dataset normalization, composition screening,
condensed-structure archive generation, structure matching, external band-gap
handoff/feedback, method comparison, and preliminary SQS input generation. MLP
relaxation, phonon screening, phase-diagram competition, recommendation reports,
and the Chinese user guide remain planned — see `docs/PROJECT_PLAN.md`.

## License

MIT
