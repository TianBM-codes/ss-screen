from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from ssscreen.gui.project_file import (
    create_project_file,
    extract_project_file,
    read_stage13_wavelength,
)


def test_stage13_wavelength_survives_project_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "source"
    stage = root / "13_geometry"
    stage.mkdir(parents=True)
    (stage / "config.json").write_text(
        json.dumps({"detector_context": {"target_wavelength_um": 20.0}}), encoding="utf-8"
    )
    archive = tmp_path / "20um.ssproject"
    create_project_file(root, archive)
    opened = tmp_path / "opened"
    extract_project_file(archive, opened)
    assert read_stage13_wavelength(opened / "13_geometry/config.json") == 20.0


@pytest.mark.parametrize("value", [None, False, -1, 0, float("nan"), "20"])
def test_invalid_saved_wavelength_is_not_restored(tmp_path: Path, value: object) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"detector_context": {"target_wavelength_um": value}}))
    assert read_stage13_wavelength(config) is None


def test_project_file_round_trip_and_hash_validation(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    (root / "01_dataset").mkdir(parents=True)
    (root / "10_phonon" / "results").mkdir(parents=True)
    (root / "13_detector").mkdir(parents=True)
    (root / "01_dataset" / "input.json").write_text('{"formula":"CaSe"}', encoding="utf-8")
    (root / "10_phonon" / "results" / "band.csv").write_text("q,f\n0,1\n", encoding="utf-8")
    (root / "13_detector" / "detector_assessment.csv").write_text(
        "id,cutoff\na,2\n", encoding="utf-8"
    )
    (root / "notes.txt").write_text("not a stage artifact", encoding="utf-8")

    project_file = tmp_path / "demo.ssproject"
    manifest = create_project_file(root, project_file, project_settings={"device": "cpu"})
    assert manifest["artifact_count"] == 3

    extracted = tmp_path / "opened"
    extract_project_file(project_file, extracted)
    assert (extracted / "01_dataset" / "input.json").read_text(
        encoding="utf-8"
    ) == '{"formula":"CaSe"}'
    assert not (extracted / "notes.txt").exists()
    assert (extracted / "13_detector" / "detector_assessment.csv").exists()
    assert json.loads((extracted / ".ssscreen" / "project.json").read_text(encoding="utf-8"))[
        "settings"
    ] == {"device": "cpu"}


def test_project_file_rejects_tampered_manifest(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    (root / "12_recommend").mkdir(parents=True)
    (root / "12_recommend" / "report.md").write_text("ok", encoding="utf-8")
    source = tmp_path / "source.ssproject"
    create_project_file(root, source)

    tampered = tmp_path / "tampered.ssproject"
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(tampered, "w") as changed:
        for member in original.infolist():
            payload = original.read(member)
            if member.filename == "artifacts/12_recommend/report.md":
                payload = b"changed"
            changed.writestr(member, payload)

    with pytest.raises(ValueError, match="checksum mismatch"):
        extract_project_file(tampered, tmp_path / "opened")
