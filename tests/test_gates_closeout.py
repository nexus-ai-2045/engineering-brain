from pathlib import Path

from engineering_brain import gates


def test_closeout_compiles_tracked_python_files_not_fixed_package(
    monkeypatch,
    tmp_path: Path,
) -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path):
        commands.append(command)
        stdout = "src/example/tool.py\ntests/test_tool.py" if command[:3] == [
            "git", "ls-files", "*.py"
        ] else ""
        return {
            "command": " ".join(command),
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
        }

    monkeypatch.setattr(gates, "run", fake_run)
    monkeypatch.setattr(gates, "scan_personal_paths", lambda repo: [])

    result = gates.closeout_repo(tmp_path)

    assert result["verification"]["status"] == "ok"
    pytest_command = next(
        command for command in commands if command[:3] == ["python", "-m", "pytest"]
    )
    assert pytest_command[:4] == ["python", "-m", "pytest", "-q"]
    assert pytest_command[4] == "--basetemp"
    assert Path(pytest_command[5]).name == "pytest"
    assert result["verification"]["pytest"]["command"] == (
        "python -m pytest -q --basetemp <TEMP>"
    )
    assert [
        "python", "-m", "py_compile", "src/example/tool.py", "tests/test_tool.py"
    ] in commands
