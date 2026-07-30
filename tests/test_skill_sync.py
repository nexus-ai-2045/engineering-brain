from pathlib import Path

from engineering_brain.cli import main
from engineering_brain.skill_sync import compare_skill, sync_skill


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "engineering-autopilot"


def test_compare_skill_reports_missing_runtime_copy(tmp_path: Path) -> None:
    result = compare_skill(source_dir=SOURCE, runtime_root=tmp_path)

    assert result["status"] == "missing"
    assert result["source"] == "skills/engineering-autopilot"
    assert result["target"] == "<RUNTIME_SKILLS>/engineering-autopilot"
    assert result["apply_required"] is True


def test_sync_skill_dry_run_does_not_write_runtime_copy(tmp_path: Path) -> None:
    result = sync_skill(source_dir=SOURCE, runtime_root=tmp_path, apply=False)

    assert result["status"] == "missing"
    assert result["mode"] == "dry-run"
    assert not (tmp_path / "engineering-autopilot").exists()


def test_sync_skill_apply_copies_projection_and_reports_ok(tmp_path: Path) -> None:
    result = sync_skill(source_dir=SOURCE, runtime_root=tmp_path, apply=True)

    assert result["status"] == "synced"
    assert result["mode"] == "apply"
    assert (tmp_path / "engineering-autopilot" / "SKILL.md").exists()
    assert (tmp_path / "engineering-autopilot" / "references" / "lifecycle.md").exists()

    drift = compare_skill(source_dir=SOURCE, runtime_root=tmp_path)

    assert drift["status"] == "ok"
    assert drift["changed_files"] == []


def test_compare_skill_detects_runtime_drift(tmp_path: Path) -> None:
    sync_skill(source_dir=SOURCE, runtime_root=tmp_path, apply=True)
    skill = tmp_path / "engineering-autopilot" / "SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nlocal drift\n", encoding="utf-8")

    result = compare_skill(source_dir=SOURCE, runtime_root=tmp_path)

    assert result["status"] == "drift"
    assert result["apply_required"] is True
    assert "SKILL.md" in result["changed_files"]


def test_cli_skill_sync_dry_run_uses_runtime_root(tmp_path: Path, capsys) -> None:
    code = main(["skill-sync", "--runtime-root", str(tmp_path), "--json"])

    assert code == 0
    output = capsys.readouterr().out
    assert '"status": "missing"' in output
    assert '"target": "<RUNTIME_SKILLS>/engineering-autopilot"' in output
    assert not (tmp_path / "engineering-autopilot").exists()
