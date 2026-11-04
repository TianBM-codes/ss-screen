# Observed environments for the 2026-11-04 local MP workflow

These files record installed package versions, without credentials, editable
paths, machine usernames, or private package URLs. They are **version constraints
and observations**, not hash-locked wheel sets or proof of a clean-machine install.
They describe the local November run, not the September historical environment.

| Environment | Python | Constraints | Purpose |
|---|---|---|---|
| WSL/Linux x86_64 screening | 3.11.18 | `screen-wsl-py311.constraints.txt` | MP database, descriptions, groups, tasks, mBJ replay |
| WSL/Linux x86_64 CPU MLP | 3.11.18 | `mlp-cpu-wsl-py311.constraints.txt` | MACE, mixing, Phonopy, hull collection |
| Windows GUI | 3.11.9 | `gui-windows-py311.constraints.txt` | Optional PySide6 desktop; CLI runs in WSL |

Matching JSON files contain complete installed-distribution inventories, including
`ss-screen==1.0`. Use the reviewed Git commit to identify project code: the version
string alone cannot distinguish two worktrees. `ss-screen` is excluded from all
constraints because it is installed from the checkout. `mp_offline` is excluded
from screening constraints because its original wheel must be delivered separately.

## Screening and mBJ replay

For **MP ZIP → regenerated groups → 318 pairs**, follow the
[full database quickstart](../../docs/reproducibility/MP_ZIP_TO_318_ZH.md).
Install `.[condense]` with the screening constraints, plus the separately supplied
`mp_offline` wheel. This route does not need the live `mp` extra, GUI or MLP.
It uses the original database and the external mBJ results together; the
replay-only instructions immediately below have a narrower scope.

For **only the 318-pair replay**, the core package is sufficient. In a Python 3.11
environment, use `python -m pip install -c requirements/reproduction-20261104/screen-wsl-py311.constraints.txt -e .`.
The optional `condense`, `mp`, GUI and MLP extras are not required for this route.
Run `python scripts/replay_mbj_results.py --bundle /path/to/extracted-bundle --output /path/to/new-output`.
The output must be a new directory outside the data bundle. See the
[318-pair quickstart](../../docs/reproducibility/REPLAY_318_ZH.md).

Run from a reviewed repository checkout on Linux/WSL with Python 3.11:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install 'pip==26.2.2'
python -m pip install -c requirements/reproduction-20261104/screen-wsl-py311.constraints.txt \
  -e '.[condense,mp]' --group dev
# Only for the offline MP database route; set DEPENDENCY_PACK to the delivered pack:
python -m pip install -c requirements/reproduction-20261104/screen-wsl-py311.constraints.txt \
  "$DEPENDENCY_PACK/wheels/mp_offline-0.1.0-py2.py3-none-any.whl"
python -m pip check
ss-screen --help
```

The mBJ replay package does not require `mp_offline` or the MP database. The
screening environment uses NumPy 2.4.6. Do not install the MLP extra into it.

## Optional CPU MACE / Phonopy

Use a separate environment; the validated MACE runtime uses NumPy 1.26.4:

```bash
deactivate
python3.11 -m venv .venv-mlp
source .venv-mlp/bin/activate
python -m pip install 'pip==26.3'
python -m pip install 'torch==2.5.1+cpu' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -c requirements/reproduction-20261104/mlp-cpu-wsl-py311.constraints.txt \
  -e '.[mlp,phonon,mp]'
python -m pip check
ss-screen stability relax --help
```

These are CPU constraints. A CUDA environment needs its own compatible Torch
build and a separate recorded inventory; do not relabel the CPU snapshot as GPU
validation. The MLP environment does not contain `mp_offline`: export offline
competing structures in the screening environment, then relax/collect in MLP.
Pass JSON/CSV artifacts between environments, not NumPy-2 pickle objects to MLP.

## Optional Windows GUI

From PowerShell in the checkout, select the desired Python 3.11 installation:

```powershell
py -3.11 -m venv .venv-gui
.\.venv-gui\Scripts\python.exe -m pip install -c requirements/reproduction-20261104/gui-windows-py311.constraints.txt -e ".[gui]"
.\.venv-gui\Scripts\python.exe -m pip check
.\.venv-gui\Scripts\ss-screen-gui.exe
```

Set the GUI's WSL project path to the recipient's checkout and select the proper
environment per stage. Do not copy another person's absolute paths. The local
MP demonstration's extra result-viewer/monitor scripts are external run adapters,
not part of the general GUI implementation or required for CLI reproduction.

## Verification and offline installation boundary

All three source environments passed `pip check` when captured. The screening
and CPU MLP environments actually ran the workflows recorded in the handoff
guide. No new MACE/DFT/phonon calculations are started by this documentation.

To recreate *every* observed distribution, use the constraints file as a
requirements file (`-r`) after handling the platform-specific Torch wheel and
separate project/MP-reader installations. This is broader than the minimal
workflow extras above. For a fully disconnected recipient, download the complete
transitive wheel set for their Python/OS/architecture, plus build prerequisites
where binary wheels are unavailable, and verify installation in a fresh offline
environment. The four-wheel MP-reader supplement alone is not such a wheel set.
