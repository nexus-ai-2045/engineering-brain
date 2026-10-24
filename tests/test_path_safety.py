from pathlib import Path

from engineering_brain.path_safety import scan_personal_paths


def test_scan_personal_paths_detects_windows_home(tmp_path: Path) -> None:
    path = tmp_path / "README.md"
    path.write_text("path: " + "C:" + "/".join(["", "Users", "fixture", "Projects", "demo\n"]), encoding="utf-8")

    findings = scan_personal_paths(tmp_path)

    assert findings
    assert findings[0].path == "README.md"


def test_scan_personal_paths_allows_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "README.md"
    path.write_text("path: <PROJECTS_ROOT>/Documents/repos/demo\n", encoding="utf-8")

    assert scan_personal_paths(tmp_path) == []


def test_redact_personal_paths_replaces_unix_and_windows_homes() -> None:
    from engineering_brain.path_safety import redact_personal_paths

    unix = "/".join(["", "Users", "fixture"]) + "/Projects/demo"
    windows = "C:" + "/".join(["", "Users", "fixture"]) + "/Projects/demo"
    assert redact_personal_paths(unix) == "<USER_HOME>/Projects/demo"
    assert "<USER_HOME>" in redact_personal_paths(windows)
    assert "fixture" not in redact_personal_paths(windows)


def test_redact_personal_paths_ignores_relative_home_segments() -> None:
    from engineering_brain.path_safety import PERSONAL_PATH_PATTERN, redact_personal_paths

    relative = "/".join(["packages", "home", "USER", "settings.py"])
    assert redact_personal_paths(relative) == relative
    assert PERSONAL_PATH_PATTERN.search(relative) is None


def test_scan_personal_paths_checks_public_config_files(tmp_path: Path) -> None:
    env_example = tmp_path / ".env.example"
    env_example.write_text("LOCAL_PATH=" + "C:" + "/".join(["", "Users", "fixture", "Projects", "demo\n"]), encoding="utf-8")
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("LABEL local.path=" + "/".join(["", "Users", "fixture", "Projects", "demo\n"]), encoding="utf-8")

    findings = scan_personal_paths(tmp_path)

    assert {finding.path for finding in findings} == {".env.example", "Dockerfile"}
