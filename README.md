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
# To also run the robocrys condensation step:
pip install -e ".[condense]"
```

## CLI

```bash
ss-screen --help

# Stage 1b: pre-filter metallic / mixed-valence structures
ss-screen valence-filter --df-mp mp.df --df-wbm wbm.df --output valid_ids.json

# Stage 1c: build robocrys condensed JSON inputs for grouping
ss-screen condense --input structures/ --output-dir condensed/

# Stage 2: group materials by composition template + environment fingerprint
ss-screen group \
  --df-mp mp.df --df-wbm wbm.df --nelems 2 \
  --condensed-dirs ../mp-condense/condensed \
  --output group_df.json

# Stage 5: enumerate promising alloying pairs from computed gaps
ss-screen pair \
  --groups group_df.json --gaps mbj_gaps.csv \
  --output mbj_result.csv
```

All numerical thresholds (band-gap windows, atom-count caps, excluded elements)
are exposed as CLI options with research-default values; pass `--help` on any
command to see them. The `condense` command requires the optional `condense`
extra because it uses robocrys at runtime.

## Documentation

- `docs/PROJECT_PLAN.md` — full design and milestone roadmap
- `docs/PROJECT_LOG.md` — cross-session progress log
- `AGENTS.md` — operating rules for AI assistants (read-only boundaries)

## Status

Pair-screening core (Milestone 1). Data-acquisition, DFT verification, and
defect-ranking stages are planned — see `docs/PROJECT_PLAN.md`.

## License

MIT
