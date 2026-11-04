# PR preparation — 2026-11-04

Published draft: [TianBM-codes/ss-screen #8](https://github.com/TianBM-codes/ss-screen/pull/8),
targeting `master` from the existing fork. Scientific/replay source revision pinned
in the delivered data package: `8e17080842749cac42ebf4406891282b71f24e79`.
The independent versioned-entrypoint replay completed successfully: 8962 packaged
files verified, six batches / 2944 rows strictly accepted, 1999 success / 620
unconverged / 325 failed, zero missing, 79 + 239 = 318 pairs / 317 endpoints.
The data-only handoff ZIP is 11,286,887 bytes; its checksum is recorded in
[mp_2944_assets.json](mp_2944_assets.json). No scientific source changed after this
validation; later documentation updates do not invalidate the pinned source.

Status: the initial pre-publication report was delivered; the user then authorized
a PR and a separate data ZIP specifically for the 318-pair replay. Publish as a
draft while the checks below remain unresolved; do not call it merge-ready.

Target: `TianBM-codes/ss-screen`, base `master` (`64d7e56` when inspected).
Publication branch: `codex/mp-318-replay-20261104`, based on local HEAD `7444d3d`.
Two existing local commits (`a7f0bb2`, `7444d3d`) are ahead of the target base.
The proposed PR must include their source changes as well as the current
reproducibility documentation; it is not a documentation-only PR.

## Proposed title

Add local workflow updates and reproducible 318-pair mBJ replay

## Proposed body

The local workflow needs a usable structure-import implementation, updated
Stage 13 endpoint/substrate assessment and a documented way for another machine
to process the same MP data. This change supplies those source/GUI updates and
records the three separate screening, CPU MLP and Windows GUI environments.
The versioned `scripts/replay_mbj_results.py` and Chinese quickstart provide a
core-only route to replay 318 pairs from the separately delivered immutable data.

The handoff guide distinguishes screening the exact MP database from replaying
existing mBJ results. It specifies the offline reader, canonical matching protocol,
four historical exclusions, external asset checksums and expected acceptance
counts. The README now installs from existing pyproject extras instead of a
missing root requirements.txt. Data, model weights and virtual environments are
not included. Environment inventories are observed versions, not a tested
fresh-machine lockfile or complete offline distribution.

Validation:

- All three observed environments passed `pip check`.
- MP filtering/grouping/pairing/gap export/feedback/VASP collector tests: 56 passed.
- Structure import, detector, geometry, material assessment and project-config
  tests: 66 passed, 1 failed because `tests/data/stage13_geometry/config.json`
  is absent. The missing historical fixture was not recreated without inspection.
- Selected changed core/test files: Ruff reports 60 issues; Black requires seven
  files to be formatted. These are unresolved checks, not suppressed failures.
- Prior actual local mBJ replay accepted all 2944 records with zero rejected or
  missing rows: 1999 success, 620 unconverged, 325 failed. Historical and local
  grouping both yielded 318 pairs / 317 endpoints with matching normalized
  identities and gaps within 1e-12 eV. This preparation did not rerun computations.

## Publication and readiness

The target repository is public. The app connection has no direct push permission.
The existing local Git login has a writable `jiazuolong/ss-screen` fork of the
target, so use that fork's publication branch to open a PR against
`TianBM-codes/ss-screen:master`. No new credentials are required or stored.
Repository visibility does not distribute
external data automatically, and a PR does not update master until it is merged.

Resolve the missing-fixture test and formatting checks before describing the PR
as ready to merge. A fresh installation on a separate environment has not been
verified. The optional MACE/phonon workflow remains stopped at the user's request.

Recipient assets and commands: [handoff guide](mp_2944_20261104.md),
[asset manifest](mp_2944_assets.json),
[environment guide](../../requirements/reproduction-20261104/README.md).
