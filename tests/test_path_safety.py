from pathlib import Path

from devbrain.path_safety import scan_personal_paths


def test_scan_personal_paths_detects_windows_home(tmp_path: Path) -> None:
    path = tmp_path / "README.md"
    path.write_text("path: " + "C:" + "/Users/" + "alice/Projects/demo\n", encoding="utf-8")

    findings = scan_personal_paths(tmp_path)

    assert findings
    assert findings[0].path == "README.md"


def test_scan_personal_paths_allows_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "README.md"
    path.write_text("path: <PROJECTS_ROOT>/Documents/repos/demo\n", encoding="utf-8")

    assert scan_personal_paths(tmp_path) == []


def test_scan_personal_paths_checks_public_config_files(tmp_path: Path) -> None:
    env_example = tmp_path / ".env.example"
    env_example.write_text("LOCAL_PATH=" + "C:" + "/Users/" + "alice/Projects/demo\n", encoding="utf-8")
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("LABEL local.path=" + "/Users/" + "alice/Projects/demo\n", encoding="utf-8")

    findings = scan_personal_paths(tmp_path)

    assert {finding.path for finding in findings} == {".env.example", "Dockerfile"}
