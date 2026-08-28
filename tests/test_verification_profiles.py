from __future__ import annotations

import json
from pathlib import Path

import pytest

from engineering_brain import gates
from engineering_brain.cli import main
from engineering_brain.verification import (
    build_closeout_verification,
    detect_repo_signals,
    load_profiles_for_repo,
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
    smoke = next(profile for profile in profiles if profile.id == "python_smoke_cli")
    assert smoke.detect_any == ("skills/engineering-autopilot/manifest.yaml",)
    skill = next(profile for profile in profiles if profile.id == "python_integration_skill_sync")
    assert skill.checks[0].kind == "json_status"
    assert skill.checks[0].ok_statuses == ("ok",)


def test_detect_repo_signals_uses_loaded_profile_markers() -> None:
    profiles = load_verification_profiles()
    markers = {marker for profile in profiles for marker in profile.detect_any}
    signals = detect_repo_signals(ROOT, markers)
    assert "pyproject.toml" in signals
    assert "skills/engineering-autopilot/SKILL.md" in signals
    assert "skills/engineering-autopilot/manifest.yaml" in signals


def test_plain_pyproject_does_not_select_engineering_brain_smoke(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="demo"\nversion="0.0.1"\n',
        encoding="utf-8",
    )
    selection = select_verification_profiles(tmp_path)
    selected_ids = {item["id"] for item in selection["selected"]}
    assert "python_unit" in selected_ids
    assert "python_smoke_cli" not in selected_ids
    assert any(
        item["id"] == "python_smoke_cli" for item in selection["not_applicable"]
    )


def test_select_profiles_skips_opt_in_and_unmatched_stacks(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    selection = select_verification_profiles(tmp_path)
    selected_ids = {item["id"] for item in selection["selected"]}
    assert "node_unit" in selected_ids
    assert "python_unit" not in selected_ids
    assert "e2e_opt_in" not in selected_ids
    assert any(item["id"] == "e2e_opt_in" for item in selection["not_applicable"])


def test_plan_verification_marks_applicable_checks_not_run(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    plan = plan_verification(tmp_path)
    assert plan["schema_version"] == 2
    assert plan["mode"] == "plan"
    assert plan["summary"]["not_run"] >= 1
    assert plan["summary"]["not_applicable"] >= 1
    statuses = {item["status"] for item in plan["evidence"]}
    assert statuses <= {"not_run", "not_applicable"}
    assert all(
        item["status"] == "not_run"
        for item in plan["evidence"]
        if item["profile_id"] == "python_unit"
    )


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


def test_json_status_check_fails_on_action_required_even_when_exit_zero(
    tmp_path: Path,
) -> None:
    (tmp_path / "skills" / "engineering-autopilot").mkdir(parents=True)
    (tmp_path / "skills" / "engineering-autopilot" / "SKILL.md").write_text(
        "# skill\n", encoding="utf-8"
    )

    def fake_run(command: list[str]) -> dict:
        payload = {"status": "action_required", "targets": [{"status": "drift"}]}
        return {
            "command": " ".join(command),
            "returncode": 0,
            "stdout": json.dumps(payload),
            "stderr": "",
        }

    result = build_closeout_verification(
        tmp_path,
        profile_ids=["python_integration_skill_sync"],
        execute=True,
        run_command=fake_run,
    )

    evidence = next(
        item for item in result["evidence"] if item["check_id"] == "skill_sync_drift"
    )
    assert evidence["status"] == "fail"
    assert "action_required" in evidence["stderr"]


def test_repo_profiles_extend_packaged_defaults_by_default(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "verification-profiles.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                'updated_at: "2026-08-28"',
                "profiles:",
                "  - id: cargo_unit",
                "    layer: unit",
                "    status: candidate",
                "    detect_any:",
                "      - Cargo.toml",
                "    required: false",
                "    execute: false",
                "    checks:",
                "      - id: cargo_test",
                "        argv: [\"cargo\", \"test\"]",
                "    insufficient_if:",
                "      - cargo tests missing",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "Cargo.toml").write_text("[package]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

    profiles, label = load_profiles_for_repo(tmp_path)
    ids = {profile.id for profile in profiles}
    assert "python_unit" in ids
    assert "cargo_unit" in ids
    assert "extend" in label

    selection = select_verification_profiles(tmp_path)
    selected_ids = {item["id"] for item in selection["selected"]}
    assert "cargo_unit" in selected_ids
    assert "python_unit" in selected_ids


def test_repo_profile_replace_mode_requires_explicit_flag(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "verification-profiles.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                'updated_at: "2026-08-28"',
                "profile_load_mode: replace",
                "profiles:",
                "  - id: only_custom",
                "    layer: unit",
                "    status: adopted",
                "    detect_any:",
                "      - custom.marker",
                "    required: false",
                "    execute: false",
                "    checks:",
                "      - id: custom_check",
                "        argv: [\"true\"]",
                "    insufficient_if:",
                "      - custom missing",
                "",
            ]
        ),
        encoding="utf-8",
    )
    profiles, label = load_profiles_for_repo(tmp_path)
    assert [profile.id for profile in profiles] == ["only_custom"]
    assert "replace" in label


def test_detect_signals_include_custom_profile_markers(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "verification-profiles.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                'updated_at: "2026-08-28"',
                "profiles:",
                "  - id: maven_unit",
                "    layer: unit",
                "    status: candidate",
                "    detect_any:",
                "      - pom.xml",
                "    required: false",
                "    execute: false",
                "    checks:",
                "      - id: mvn_test",
                "        argv: [\"mvn\", \"test\"]",
                "    insufficient_if:",
                "      - maven tests missing",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "pom.xml").write_text("<project/>", encoding="utf-8")
    selection = select_verification_profiles(tmp_path)
    assert "pom.xml" in selection["detected_signals"]
    assert any(item["id"] == "maven_unit" for item in selection["selected"])


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


def test_cli_verify_rejects_unknown_profile_id(capfd, tmp_path: Path) -> None:
    code = main(
        ["verify", "--repo", str(tmp_path), "--profile", "does_not_exist", "--json"]
    )
    assert code == 1
    output = capfd.readouterr().out
    assert '"status": "blocked"' in output
    assert "unknown verification profile" in output


def test_cli_verify_emits_plan_json(capfd, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    code = main(["verify", "--repo", str(tmp_path), "--json"])
    assert code == 0
    output = capfd.readouterr().out
    assert '"schema_version": 2' in output
    assert '"mode": "plan"' in output
    assert "python_unit" in output
    assert '"not_applicable"' in output


def test_opt_in_e2e_requires_explicit_profile(tmp_path: Path) -> None:
    selection = select_verification_profiles(tmp_path, profile_ids=["e2e_opt_in"])
    assert selection["selected"][0]["id"] == "e2e_opt_in"
    plan = plan_verification(tmp_path, profile_ids=["e2e_opt_in"])
    assert plan["evidence"][0]["kind"] == "human"
    assert plan["evidence"][0]["status"] == "not_run"


def test_plan_emits_not_applicable_for_unmatched_profiles(tmp_path: Path) -> None:
    plan = plan_verification(tmp_path)
    assert plan["summary"]["not_applicable"] >= 1
    assert any(item["status"] == "not_applicable" for item in plan["evidence"])
    assert any(item["id"] == "python_unit" for item in plan["not_applicable_profiles"])
