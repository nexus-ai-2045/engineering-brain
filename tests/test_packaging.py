from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_setuptools_only_discovers_engineering_brain_package() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["tool"]["setuptools"]["packages"]["find"]["include"] == [
        "engineering_brain*"
    ]


def test_algorithm_catalog_is_packaged_inside_engineering_brain() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]["engineering_brain"]

    assert "data/*.json" in package_data
    assert "data/*.yaml" in package_data
    assert (ROOT / "engineering_brain" / "data" / "algorithms.json").is_file()
    assert (ROOT / "engineering_brain" / "data" / "adoption-units.yaml").is_file()
    assert (ROOT / "engineering_brain" / "data" / "technology-sources.yaml").is_file()
    assert (ROOT / "engineering_brain" / "data" / "local-learnings.yaml").is_file()


def test_local_learnings_default_path_matches_packaged_data_layout() -> None:
    from importlib.resources import files

    from engineering_brain.registry import (
        DEFAULT_LOCAL_LEARNINGS,
        DEFAULT_REGISTRY,
        PACKAGE_ROOT,
        local_learnings,
    )

    assert DEFAULT_LOCAL_LEARNINGS == PACKAGE_ROOT / "data" / "local-learnings.yaml"
    assert DEFAULT_LOCAL_LEARNINGS.parent == DEFAULT_REGISTRY.parent
    assert DEFAULT_LOCAL_LEARNINGS.is_file()
    packaged = files("engineering_brain").joinpath("data", "local-learnings.yaml")
    assert packaged.is_file()
    assert "learnings:" in packaged.read_text(encoding="utf-8")
    assert len(local_learnings()) == 7


def test_feedback_schema_is_packaged_inside_engineering_brain() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]["engineering_brain"]

    assert "*.schema.json" in package_data
    assert (ROOT / "engineering_brain" / "fde-feedback-packet.schema.json").is_file()
