"""Project packaging and CI configuration tests."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_dev_tools_are_uv_dependency_group_not_package_extra():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())

    optional = data["project"].get("optional-dependencies", {})
    assert "dev" not in optional

    dev_group = data["dependency-groups"]["dev"]
    assert "pytest>=7" in dev_group
    assert "ruff" in dev_group
    assert "black" in dev_group


def test_ci_workflow_runs_core_tests_without_all_extras():
    workflow = ROOT / ".github" / "workflows" / "ci.yml"

    text = workflow.read_text()

    assert "uv sync" in text
    assert "uv run pytest" in text
    assert "--all-extras" not in text
    assert "dft" not in text
