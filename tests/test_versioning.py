from pathlib import Path

from devbrain.cli import main
from devbrain.versioning import version_packet


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_version_surfaces_are_synced_to_public_seed() -> None:
    packet = version_packet(ROOT)

    assert packet["version"] == "0.1.0"
    assert packet["status"] == "ok"
    assert packet["public_seed"] is True
    assert packet["surfaces"]["pyproject"] == "0.1.0"
    assert packet["surfaces"]["devbrain"] == "0.1.0"
    assert packet["surfaces"]["skill_manifest"] == "0.1.0"


def test_cli_version_emits_json(capsys) -> None:
    code = main(["version", "--json"])

    assert code == 0
    output = capsys.readouterr().out
    assert '"version": "0.1.0"' in output
    assert '"status": "ok"' in output


def test_versioning_docs_exist() -> None:
    changelog = read_text("CHANGELOG.md")
    versioning = read_text("docs/VERSIONING.md")

    assert "0.1.0" in changelog
    assert "public seed" in changelog
    assert "SemVer" in versioning
    assert "pyproject.toml" in versioning
    assert "GitHub Release" in versioning
