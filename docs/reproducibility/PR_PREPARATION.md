# PR #8 — original MP ZIP to 318 pairs

Draft PR: https://github.com/TianBM-codes/ss-screen/pull/8, targeting
`TianBM-codes/ss-screen:master` from the existing
`jiazuolong/ss-screen:codex/mp-318-replay-20261104` branch. It is not merged.

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
- Full fixed-code MP ZIP validation status is recorded in the final delivery's
  `DELIVERY.json`. Its selected mode is an explicit verified descriptor cache:
  the database/candidates/groups/tasks/pairing are regenerated, while 4944 descriptions
  are reused. This is not a claim of recalculating all 4944 descriptions in this run.
- The earlier replay-only entry was independently verified for 2944 states,
  1999 success / 620 unconverged / 325 failed, and 318 pairs / 317 endpoints.

## Existing draft limitations

The PR also includes two previously unmerged local source commits (`a7f0bb2`,
`7444d3d`) with structure-import and Stage 13 changes. Prior Stage 13/configuration
checks had 66 passes and one missing-fixture failure
(`tests/data/stage13_geometry/config.json`). Selected legacy changed files had
60 Ruff findings and seven files needing Black formatting. Those unrelated
limitations are retained, not silently suppressed or described as green CI.
A fresh-machine install and a complete offline scientific wheel set have not
been verified. The optional MACE/phonon workflow remains stopped.

Current recipient instructions: [MP ZIP → 318 pairs](MP_ZIP_TO_318_ZH.md).
The old [replay-only guide](REPLAY_318_ZH.md) remains available for the narrower task.
