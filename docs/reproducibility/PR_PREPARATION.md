# PR #9 — original MP ZIP to 318 pairs

Draft PR: https://github.com/TianBM-codes/ss-screen/pull/9, targeting
`TianBM-codes/ss-screen:master` from the existing
`jiazuolong/ss-screen:codex/mp-zip-to-318-20261104` branch. It is not merged. PR #8 was merged during this work; its original
replay-only title/body are preserved. This follow-up includes current master
with its `/run` ignore rule.

## Final implementation

The recipient can now run `ss-screen mp-reproduce --mp-zip ... --mbj-bundle ...
--output-dir ...` to read the original database, regenerate composition candidates,
descriptions, groups and pending tasks, verify existing mBJ results, and pair the
**new groups**. Frozen groups serve only as a separate acceptance reference.
The original 10.76 MiB replay-only package cannot replace the original MP database.

The dated protocol verifies the exact ZIP/database hashes, preserves four explicit
historical exclusions and 30/45-atom cutoffs, and checks material membership,
property-preserving periodic geometry, normalized pair/group evidence and gap values.
Formal calculation identities and new pending identities remain separate.
Spectator environment fingerprints are sorted after variable-element substitution,
porting the audited canonical rule into tested source instead of an external patch.

Robocrys descriptions are fresh by default. An optional descriptor cache is
explicit and bound to the database, material IDs, every input structure and each
file's bytes. Cache use and the number of newly calculated descriptors are reported.
The shared `ssscreen.mbj_replay` module retains the older replay-only script entry.
Manifest verification uses eight bounded I/O threads; every checksum is still checked.
Correspondence constrains original site properties and labels, avoiding generated
supercell labels and species-only permutations that exchange different moments.

Code and observed environment constraints are in Git. The original `mp.zip`,
frozen mBJ bundle, offline reader wheels and optional descriptor cache are delivered
in one external ZIP. Neither data nor virtual environments/model weights are
committed. No VASP, MACE, SQS or phonon calculation is launched by this route.

## Validation

- 108 focused MP/ZIP/cache/geometry/grouping/gap/CLI tests pass.
- New/changed reproduction modules, wrapper and tests pass Ruff/Black.
- A real fresh one-worker descriptor job for mp-1001833 completed successfully;
  its bytes equal the prior descriptor. All 14 previously identified representation
  differences pass the property-preserving periodic correspondence check.
- Full fixed-code MP ZIP validation **passed**: 46675 prefiltered rows, 4948
  candidates, 491/1358 groups, 949/1995 tasks, all 2944 mBJ records strictly
  accepted (1999 success, 620 unconverged, 325 failed), 79+239=318 pairs / 317
  endpoints. Normalized pair/group evidence equals the historical reference,
  with gaps within 1e-12 eV. The 2930 equal primary representations and 14
  property-preserving periodic matches all pass. `DELIVERY.json` records the
  fixed checkout and artifact checksums. The selected mode is an explicit verified descriptor cache:
  the database/candidates/groups/tasks/pairing are regenerated, while 4944 descriptions
  are reused. This is not a claim of recalculating all 4944 descriptions in this run.
- The earlier replay-only entry was independently verified for 2944 states,
  1999 success / 620 unconverged / 325 failed, and 318 pairs / 317 endpoints.

## Existing draft limitations

The repository baseline already includes the structure-import and Stage 13
changes from merged PR #8. Those changes are not new in this follow-up.
Prior Stage 13/configuration
checks had 66 passes and one missing-fixture failure
(`tests/data/stage13_geometry/config.json`). Selected legacy changed files had
60 Ruff findings and seven files needing Black formatting. Those unrelated
limitations are retained, not silently suppressed or described as green CI.
A fresh-machine install and a complete offline scientific wheel set have not
been verified. The optional MACE/phonon workflow remains stopped.

Current recipient instructions: [MP ZIP → 318 pairs](MP_ZIP_TO_318_ZH.md).
The old [replay-only guide](REPLAY_318_ZH.md) remains available for the narrower task.

## External data delivery

`ss-screen-mp-to-318-data-20261104.zip`: 367,962,171 bytes (~351 MiB),
SHA256 `599f40f3678d209c049f23684a783d7ae8a1012901a7342c93d07ec7ee182534`.
All 8980 members pass CRC/path checks; all 8976 asset entries pass SHA/size checks.
Original MP ZIP bytes and frozen mBJ member bytes are preserved. `DELIVERY.json`
pins checkout `84d6299243d22e8d43462f12a73932d59dc954c2`; its scientific sources
are identical to validated `6cf332c`. Later checksum documentation does not
change those sources. The data archive is outside the repository and is not
part of this PR. A `.zip.sha256` sidecar and local verification JSON accompany it.
