"""Tests for Materials Project dataset loading helpers."""

from __future__ import annotations

from types import SimpleNamespace

from pymatgen.core import Lattice, Structure

from ssscreen.data.mp import load_mp_dataset, load_mp_dataset_api, normalize_mp_documents


def _structure() -> Structure:
    return Structure(Lattice.cubic(5.4), ["Ca", "S"], [[0, 0, 0], [0.5, 0.5, 0.5]])


def test_normalize_mp_documents_builds_screening_dataframe_schema():
    structure = _structure()
    docs = [
        SimpleNamespace(
            material_id="mp-1",
            composition={"Ca": 1, "S": 1},
            band_gap=0.0,
            energy_above_hull=0.003,
            structure=structure,
        )
    ]

    df = normalize_mp_documents(docs)

    assert list(df.index) == ["mp-1"]
    row = df.loc["mp-1"]
    assert row["composition"].reduced_formula == "CaS"
    assert row["reduced_composition"].reduced_formula == "CaS"
    assert row["nelems"] == 2
    assert row["band_gap"] == 0.0
    assert row["e_hull"] == 0.003
    assert row["source"] == "mp"
    assert row["structure"] is structure
    assert row["primitive_structure"].composition.reduced_formula == "CaS"


def test_load_mp_dataset_defaults_to_mp_offline_backend(tmp_path):
    structure = _structure()
    calls = []

    class FakeMaterialSummary:
        energy_above_hull = "energy_above_hull"

    class FakeClient:
        def __init__(self, database=None):
            calls.append(("init", database))

        def query_all(self, *criteria):
            calls.append(("query_all", criteria))
            return [
                SimpleNamespace(
                    material_id="mp-1",
                    composition={"Ca": 1, "S": 1},
                    json_data={"band_gap": 0.0},
                    energy_above_hull=0.003,
                    structure=structure.as_dict(),
                )
            ]

    output = tmp_path / "mp.df"
    database = tmp_path / "mp-offline.db"

    df = load_mp_dataset(
        output=output,
        max_e_hull=0.01,
        offline_db=database,
        offline_client_factory=FakeClient,
        material_summary_cls=FakeMaterialSummary,
    )

    assert output.exists()
    assert list(df.index) == ["mp-1"]
    assert df.loc["mp-1", "band_gap"] == 0.0
    assert df.loc["mp-1", "source"] == "mp-offline"
    assert calls[0] == ("init", database)
    assert calls[1][0] == "query_all"


def test_load_mp_dataset_api_uses_mprester_without_explicit_api_key(tmp_path):
    structure = _structure()
    calls = []

    class FakeSummary:
        def search(self, **kwargs):
            calls.append(kwargs)
            return [
                {
                    "material_id": "mp-1",
                    "composition": {"Ca": 1, "S": 1},
                    "band_gap": 0.0,
                    "energy_above_hull": 0.003,
                    "structure": structure,
                }
            ]

    class FakeRester:
        def __init__(self):
            calls.append({"api_key": "not-passed"})
            self.materials = SimpleNamespace(summary=FakeSummary())

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    output = tmp_path / "mp.df"

    df = load_mp_dataset_api(output=output, rester_factory=FakeRester)

    assert output.exists()
    assert list(df.index) == ["mp-1"]
    assert calls[0] == {"api_key": "not-passed"}
    assert calls[1]["fields"] == [
        "material_id",
        "composition",
        "band_gap",
        "energy_above_hull",
        "structure",
    ]
