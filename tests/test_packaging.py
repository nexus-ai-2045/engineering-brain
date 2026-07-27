from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_setuptools_only_discovers_engineering_brain_package() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["tool"]["setuptools"]["packages"]["find"]["include"] == [
        "engineering_brain*"
    ]
