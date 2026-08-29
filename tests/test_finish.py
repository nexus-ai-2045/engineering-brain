from pathlib import Path

import engineering_brain.cli as cli
from engineering_brain import finish
from engineering_brain.cli import main


def _fake_ref_exists(joined: str, existing: set[str]) -> dict | None:
    if joined.startswith("git rev-parse --verify --quiet "):
        ref = joined.rsplit(" ", maxsplit=1)[1]
        code = 0 if ref in existing else 1
        return {"command": joined, "returncode": code, "stdout": ref if code == 0 else "", "stderr": ""}
    return None


def test_finish_plan_reports_merged_local_and_remote_candidates(monkeypatch) -> None:
    def fake_run(command: list[str], *, cwd: Path) -> dict:
        joined = " ".join(command)
        ref = _fake_ref_exists(joined, {"refs/heads/main", "refs/remotes/origin/main"})
        if ref is not None:
            return ref
        if joined == "git status --short --branch":
            return {"command": joined, "returncode": 0, "stdout": "## main...origin/main", "stderr": ""}
        if joined == "git branch --merged refs/heads/main --format %(refname:short)":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "main\ncodex/done-one\ncodex/done-two",
                "stderr": "",
            }
        if joined == "git branch -r --merged refs/remotes/origin/main --format %(refname:short)":
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
    assert result["suggested_commands"] == []
    assert "post_merge_cleanup.py" in result["cleanup_ssot"]
    assert "--cwd <REPO>" in result["cleanup_ssot_command"]
    assert "fractal-decision-ecosystem" in result["cleanup_ssot_command_note"]


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


# --- base ref 解決と委譲の回帰 -----------------------------------------------
#
# 以前は `git branch --merged main` と bare `main` を決め打ちしていた。
# PR checkout のように local main が無い環境では
# `malformed object name main` で失敗し、run() が returncode を握りつぶす
# ため「候補ゼロ」= 掃除済みと誤って報告されうる。
# FDE ADR-0006 がインシデントとして記録し修正済みの経路だが、
# その学習がこの repo に届いていなかった。

import subprocess as _subprocess


def _git(repo: Path, *args: str) -> None:
    _subprocess.run(
        ["git", "-c", "user.email=t@e", "-c", "user.name=t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _make_repo(tmp_path: Path, *, default_branch: str = "main") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", default_branch, ".")
    (repo / "f.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "init")
    return repo


def test_resolve_base_refs_prefers_local_main(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    assert finish.resolve_base_refs(repo)["local"] == "refs/heads/main"


def test_resolve_base_refs_falls_back_to_origin_main(tmp_path: Path) -> None:
    """local main が無い PR checkout 相当。bare main では落ちていた経路。"""
    repo = _make_repo(tmp_path, default_branch="feature")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    refs = finish.resolve_base_refs(repo)
    assert refs["local"] == "refs/remotes/origin/main"
    assert refs["remote"] == "refs/remotes/origin/main"


def test_finish_plan_works_without_a_local_main(tmp_path: Path) -> None:
    """local main が無くても、merged branch を実際に拾えること。"""
    repo = _make_repo(tmp_path, default_branch="feature")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "branch", "codex/done")

    plan = finish.finish_plan(repo)

    assert plan["status"] == "action_available"
    assert "codex/done" in plan["local_merged_branches"]
    assert plan["base_refs"]["local"] == "refs/remotes/origin/main"


def test_finish_plan_blocks_when_no_base_ref_resolves(tmp_path: Path) -> None:
    """base が引けないことを『候補ゼロ』と混同しない。"""
    repo = _make_repo(tmp_path, default_branch="feature")

    plan = finish.finish_plan(repo)

    assert plan["status"] == "blocked"
    assert plan["reason"] == "base_ref_unresolved"
    assert plan["local_merged_branches"] == []


def test_apply_local_never_deletes_and_names_the_ssot(tmp_path: Path) -> None:
    """削除は実行正本へ委譲する。この repo は branch を消さない。"""
    repo = _make_repo(tmp_path)
    _git(repo, "branch", "codex/done")

    result = finish.apply_local_cleanup(repo)

    assert result["applied"] is False
    assert result["mode"] == "apply-local"
    assert "post_merge_cleanup.py" in result["delegated_to"]
    assert "--cwd <REPO>" in result["delegated_command"]
    assert "fractal-decision-ecosystem" in result["delegated_command_note"]
    assert result["reason_not_applied"] == "local_delete_delegated_to_cleanup_ssot"
    assert result["suggested_commands"] == []
    # 実物の repo で branch が残っていることを確認する
    branches = _subprocess.run(
        ["git", "branch", "--format", "%(refname:short)"],
        cwd=repo,
        capture_output=True,
        text=True,
    ).stdout.split()
    assert "codex/done" in branches


def test_plan_names_the_cleanup_ssot(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    assert "post_merge_cleanup.py" in finish.finish_plan(repo)["cleanup_ssot"]


def test_finish_plan_excludes_resolved_remote_base_master(tmp_path: Path) -> None:
    """origin/master が base のとき、それ自体を削除候補にしない。"""
    repo = _make_repo(tmp_path, default_branch="feature")
    _git(repo, "update-ref", "refs/remotes/origin/master", "HEAD")

    plan = finish.finish_plan(repo)

    assert plan["base_refs"]["remote"] == "refs/remotes/origin/master"
    assert "origin/master" not in plan["remote_merged_branches"]
    assert plan["status"] == "ok"
    assert plan["reason"] == "nothing_to_clean"


def test_cleanup_remote_branches_excludes_resolved_base() -> None:
    stdout = "origin/master\norigin/HEAD -> origin/master\norigin/codex/done\n"
    assert finish._cleanup_remote_branches(
        stdout, remote_base="refs/remotes/origin/master"
    ) == ["origin/codex/done"]


def test_finish_plan_blocks_when_merged_list_fails(monkeypatch) -> None:
    """一覧の returncode 失敗を『候補ゼロ』と混同しない。"""

    def fake_run(command: list[str], *, cwd: Path) -> dict:
        joined = " ".join(command)
        ref = _fake_ref_exists(joined, {"refs/heads/main", "refs/remotes/origin/main"})
        if ref is not None:
            return ref
        if joined == "git status --short --branch":
            return {"command": joined, "returncode": 0, "stdout": "## main...origin/main", "stderr": ""}
        if joined.startswith("git branch --merged "):
            return {
                "command": joined,
                "returncode": 128,
                "stdout": "",
                "stderr": "fatal: malformed object name main",
            }
        raise AssertionError(f"unexpected command: {joined}")

    monkeypatch.setattr(finish, "run", fake_run)

    plan = finish.finish_plan(Path("."))

    assert plan["status"] == "blocked"
    assert plan["reason"] == "merged_local_list_failed"
    assert plan["local_merged_branches"] == []
    assert plan["remote_merged_branches"] == []
