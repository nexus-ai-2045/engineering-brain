from __future__ import annotations

from pathlib import Path

import pytest

from engineering_brain import gates
from engineering_brain.cli import main
from engineering_brain.verification import (
    build_closeout_verification,
    detect_repo_signals,
    load_verification_profiles,
    plan_verification,
    select_verification_profiles,
)


ROOT = Path(__file__).resolve().parents[1]


def test_packaged_verification_profiles_load_and_cover_layers() -> None:
    profiles = load_verification_profiles()
    layers = {profile.layer for profile in profiles}
    assert {"unit", "integration", "smoke", "e2e"}.issubset(layers)
    assert any(profile.id == "python_unit" and profile.required for profile in profiles)


def test_detect_repo_signals_for_engineering_brain() -> None:
    signals = detect_repo_signals(ROOT)
    assert "pyproject.toml" in signals
    assert "skills/engineering-autopilot/SKILL.md" in signals


def test_select_profiles_skips_opt_in_and_unmatched_stacks(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    selection = select_verification_profiles(tmp_path)
    selected_ids = {item["id"] for item in selection["selected"]}
    assert "node_unit" in selected_ids
    assert "python_unit" not in selected_ids
    assert "e2e_opt_in" not in selected_ids


def test_plan_verification_marks_checks_not_run(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    plan = plan_verification(tmp_path)
    assert plan["schema_version"] == 2
    assert plan["mode"] == "plan"
    assert plan["summary"]["not_run"] >= 1
    assert all(item["status"] == "not_run" for item in plan["evidence"])


def test_execute_false_profiles_stay_not_run_even_when_selected(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> dict:
        commands.append(command)
        return {"command": " ".join(command), "returncode": 0, "stdout": "", "stderr": ""}

    result = build_closeout_verification(
        tmp_path,
        profile_ids=["node_unit"],
        execute=True,
        run_command=fake_run,
    )

    assert result["status"] == "ok"
    assert result["evidence"][0]["status"] == "not_run"
    assert result["evidence"][0]["execute_planned"] is False
    assert commands == []


def test_required_not_run_blocks_closeout_verification(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

    def fake_run(command: list[str]) -> dict:
        return {"command": " ".join(command), "returncode": 0, "stdout": "", "stderr": ""}

    result = build_closeout_verification(
        tmp_path,
        profile_ids=["python_unit"],
        execute=False,
        run_command=fake_run,
    )

    assert result["status"] == "blocked"
    assert result["summary"]["not_run"] >= 1


def test_closeout_uses_profiles_and_keeps_compat_command_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path):
        commands.append(command)
        stdout = ""
        if command[:3] == ["git", "ls-files", "*.py"]:
            stdout = "src/example/tool.py\ntests/test_tool.py"
        return {
            "command": " ".join(command),
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
        }

    monkeypatch.setattr(gates, "run", fake_run)
    monkeypatch.setattr(gates, "scan_personal_paths", lambda repo: [])

    result = gates.closeout_repo(tmp_path, profile_ids=["python_unit"])

    assert result["schema_version"] == 2
    assert result["verification"]["status"] == "ok"
    assert result["verification"]["schema_version"] == 2
    assert result["verification"]["pytest"]["command"] == (
        "python -m pytest -q --basetemp <TEMP>"
    )
    assert result["verification"]["compileall"]["returncode"] == 0
    assert [
        "python", "-m", "py_compile", "src/example/tool.py", "tests/test_tool.py"
    ] in commands
    assert any(command[:3] == ["python", "-m", "pytest"] for command in commands)


def test_unknown_profile_id_is_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown verification profile"):
        gates.closeout_repo(tmp_path, profile_ids=["does_not_exist"])


def test_cli_verify_emits_plan_json(capfd, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    code = main(["verify", "--repo", str(tmp_path), "--json"])
    assert code == 0
    output = capfd.readouterr().out
    assert '"schema_version": 2' in output
    assert '"mode": "plan"' in output
    assert "python_unit" in output


def test_opt_in_e2e_requires_explicit_profile(tmp_path: Path) -> None:
    selection = select_verification_profiles(tmp_path, profile_ids=["e2e_opt_in"])
    assert selection["selected"][0]["id"] == "e2e_opt_in"
    plan = plan_verification(tmp_path, profile_ids=["e2e_opt_in"])
    assert plan["evidence"][0]["kind"] == "human"
    assert plan["evidence"][0]["status"] == "not_run"
