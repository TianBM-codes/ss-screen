# SS-Screen GUI Integration Notes

## Goal

The desktop GUI should preserve the workflow thinking from the standalone review
build while keeping the existing CLI as the authoritative scientific runtime.
The two public entry points should coexist:

```text
ss-screen      # real Click CLI and scientific pipeline
ss-screen-gui  # optional PySide6 desktop workbench
```

## Design Kept From The Review Build

- A project-oriented workbench with a left project tree, central parameter pages,
  right-side properties, and a bottom log/file/message area.
- The workflow is organized by the same staged material-screening flow as the
  CLI: data sources, composition screening, structure condensation, structure
  matching, gap handoff, pairing, SQS, relaxation, thermodynamics, phonons,
  phase diagram, and recommendation.
- GUI pages collect user-facing inputs and convert them back into CLI arguments.
- Long-running work is executed through `python -m ssscreen.cli.app ...` so the
  CLI and GUI share validation, defaults, output schemas, and exit codes.
- API keys, when entered in the GUI, should be injected only into the child
  process environment and not written to commands, project files, or logs.

## Integration Boundary

The GUI must not replace or simplify `src/ssscreen/cli/app.py`. Any preview-only
or mock command surface should remain outside the production package. The CLI is
the contract used by tests, documentation, automation, and future Web workers.

The formal package exposes the GUI as an optional extra:

```text
pip install -e ".[gui]"
ss-screen-gui
```

For a fuller Ubuntu development environment, use the repository
`requirements.txt`.

## Near-Term Follow-Up

- Add a small import/launcher smoke test once a GUI-capable CI environment is
  available, or keep it guarded so headless Linux does not need a display server.
- Review each specialized GUI page against the restored real Click command
  options and remove any parameter that is only valid in the standalone demo.
- Decide whether Windows should run the GUI natively while dispatching heavy
  scientific work to WSL/Ubuntu, or whether both GUI and CLI should run inside
  Linux with X11/Wayland forwarding.
