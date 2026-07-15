from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import __version__ as package_version


VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def version_packet(repo: Path) -> dict[str, Any]:
    root = repo.resolve()
    pyproject_version = _read_pyproject_version(root / "pyproject.toml")
    skill_version = _read_skill_manifest_version(root / "skills" / "engineering-autopilot" / "manifest.yaml")
    surfaces = {
        "pyproject": pyproject_version,
        "devbrain": package_version,
        "skill_manifest": skill_version,
    }
    unique_versions = {version for version in surfaces.values() if version}
    status = "ok" if len(unique_versions) == 1 and VERSION_RE.match(pyproject_version or "") else "blocked"

    return {
        "version": pyproject_version,
        "status": status,
        "scheme": "SemVer",
        "public_seed": pyproject_version == "0.1.0",
        "source_of_truth": "pyproject.toml",
        "surfaces": surfaces,
        "tag_policy": "create git tags and GitHub Releases only after explicit approval",
        "next_expected": {
            "patch": "bug fix / docs correction with no behavior change",
            "minor": "new local capability such as research packet or PR packet generator",
            "major": "stable API contract break after 1.0.0",
        },
    }


def _read_pyproject_version(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def _read_skill_manifest_version(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip()
    return None
