from pathlib import Path

import engineering_brain.cli as cli
from engineering_brain import finish
from engineering_brain.cli import main


def test_finish_plan_reports_merged_local_and_remote_candidates(monkeypatch) -> None:
    def fake_run(command: list[str], *, cwd: Path) -> dict:
        joined = " ".join(command)
        if joined == "git status --short --branch":
            return {"command": joined, "returncode": 0, "stdout": "## main...origin/main", "stderr": ""}
        if joined == "git branch --merged main --format %(refname:short)":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "main\ncodex/done-one\ncodex/done-two",
                "stderr": "",
            }
        if joined == "git branch -r --merged origin/main --format %(refname:short)":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "origin/main\norigin/codex/done-one",
                "stderr": "",
            }
        raise AssertionError(f"unexpected command: {joined}")

    monkeypatch.setattr(finish, "run", fake_run)

    result = finish.finish_plan(Path("."))

    assert result["status"] == "action_available"
    assert result["current_branch"] == "main"
    assert result["local_merged_branches"] == ["codex/done-one", "codex/done-two"]
    assert result["remote_merged_branches"] == ["origin/codex/done-one"]
    assert "remote_branch_delete" in result["human_stoplines"]
    assert "git branch -d codex/done-one codex/done-two" in result["suggested_commands"]


def test_finish_plan_blocks_on_dirty_worktree(monkeypatch) -> None:
    def fake_run(command: list[str], *, cwd: Path) -> dict:
        joined = " ".join(command)
        return {"command": joined, "returncode": 0, "stdout": "## main...origin/main\n M README.md", "stderr": ""}

    monkeypatch.setattr(finish, "run", fake_run)

    result = finish.finish_plan(Path("."))

    assert result["status"] == "blocked"
    assert result["reason"] == "dirty_worktree"
    assert result["local_merged_branches"] == []


def test_cli_finish_outputs_plan(capfd, monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "finish_plan",
        lambda repo: {"status": "ok", "repo": "<REPO>", "local_merged_branches": []},
    )

    code = main(["finish", "--json"])

    assert code == 0
    assert '"status": "ok"' in capfd.readouterr().out


def test_hook_install_copies_repo_template(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(parents=True)

    result = finish.install_hooks(repo)

    post_merge = hooks / "post-merge"
    pre_commit = hooks / "pre-commit"
    assert result["status"] == "installed"
    assert set(result["installed"]) == {"post-merge", "pre-commit"}
    assert post_merge.exists()
    assert pre_commit.exists()
    assert "engineering_brain finish" in post_merge.read_text(encoding="utf-8")
    assert "ai-ratchet-gate" in pre_commit.read_text(encoding="utf-8")
