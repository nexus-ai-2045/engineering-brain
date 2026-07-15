from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


PROTECTED_BRANCHES = {"main", "master", "develop", "dev"}
HOOK_NAMES = ["post-merge"]


def finish_plan(repo: Path) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    status = run(["git", "status", "--short", "--branch"], cwd=resolved_repo)
    current_branch = _current_branch(status["stdout"])
    dirty_lines = _dirty_lines(status["stdout"])
    if status["returncode"] != 0:
        return {
            "status": "blocked",
            "reason": "git_status_failed",
            "repo": "<REPO>",
            "current_branch": current_branch,
            "git_status": status,
            "local_merged_branches": [],
            "remote_merged_branches": [],
            "human_stoplines": _human_stoplines(),
            "suggested_commands": [],
        }
    if dirty_lines:
        return {
            "status": "blocked",
            "reason": "dirty_worktree",
            "repo": "<REPO>",
            "current_branch": current_branch,
            "dirty": dirty_lines,
            "local_merged_branches": [],
            "remote_merged_branches": [],
            "human_stoplines": _human_stoplines(),
            "suggested_commands": ["git status --short --branch"],
        }

    local_result = run(["git", "branch", "--merged", "main", "--format", "%(refname:short)"], cwd=resolved_repo)
    remote_result = run(["git", "branch", "-r", "--merged", "origin/main", "--format", "%(refname:short)"], cwd=resolved_repo)
    local_branches = _cleanup_local_branches(local_result["stdout"], current_branch=current_branch)
    remote_branches = _cleanup_remote_branches(remote_result["stdout"])
    suggested = _suggested_commands(local_branches, remote_branches)

    return {
        "status": "action_available" if local_branches or remote_branches else "ok",
        "reason": "merged_cleanup_candidates" if local_branches or remote_branches else "nothing_to_clean",
        "repo": "<REPO>",
        "current_branch": current_branch,
        "local_merged_branches": local_branches,
        "remote_merged_branches": remote_branches,
        "human_stoplines": _human_stoplines(),
        "suggested_commands": suggested,
        "apply_policy": {
            "default": "plan_only",
            "local_cleanup": "requires --apply-local",
            "remote_cleanup": "requires --apply-remote and current-turn approval",
        },
    }


def apply_local_cleanup(repo: Path) -> dict[str, Any]:
    plan = finish_plan(repo)
    branches = plan.get("local_merged_branches", [])
    if plan["status"] == "blocked" or not branches:
        plan["mode"] = "apply-local"
        return plan
    result = run(["git", "branch", "-d", *branches], cwd=repo.resolve())
    return {
        "status": "ok" if result["returncode"] == 0 else "blocked",
        "mode": "apply-local",
        "repo": "<REPO>",
        "deleted_local_branches": branches if result["returncode"] == 0 else [],
        "result": result,
        "remote_merged_branches": plan.get("remote_merged_branches", []),
        "human_stoplines": _human_stoplines(),
    }


def install_hooks(repo: Path, *, force: bool = False) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    hooks_dir = resolved_repo / ".git" / "hooks"
    if not hooks_dir.exists():
        return {
            "status": "blocked",
            "reason": "git_hooks_dir_missing",
            "repo": "<REPO>",
            "installed": [],
        }

    source_dir = Path(__file__).resolve().parents[1] / "tools" / "hooks"
    installed: list[str] = []
    skipped: list[str] = []
    for hook_name in HOOK_NAMES:
        source = source_dir / hook_name
        target = hooks_dir / hook_name
        if target.exists() and not force:
            skipped.append(hook_name)
            continue
        shutil.copyfile(source, target)
        installed.append(hook_name)

    return {
        "status": "installed" if installed else "skipped",
        "repo": "<REPO>",
        "installed": installed,
        "skipped": skipped,
        "force": force,
        "policy": "hook prints a finish plan only; branch deletion remains explicit",
    }


def run(command: list[str], *, cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _current_branch(status_stdout: str) -> str | None:
    first = status_stdout.splitlines()[0] if status_stdout.splitlines() else ""
    if first.startswith("## "):
        return first[3:].split("...", maxsplit=1)[0].strip()
    return None


def _dirty_lines(status_stdout: str) -> list[str]:
    return [line for line in status_stdout.splitlines()[1:] if line.strip()]


def _cleanup_local_branches(stdout: str, *, current_branch: str | None) -> list[str]:
    branches = []
    for line in stdout.splitlines():
        branch = line.strip().lstrip("*").strip()
        if not branch or branch in PROTECTED_BRANCHES or branch == current_branch:
            continue
        branches.append(branch)
    return branches


def _cleanup_remote_branches(stdout: str) -> list[str]:
    branches = []
    for line in stdout.splitlines():
        branch = line.strip()
        if not branch or branch in {"origin/main", "origin/HEAD"}:
            continue
        if " -> " in branch:
            continue
        branches.append(branch)
    return branches


def _suggested_commands(local_branches: list[str], remote_branches: list[str]) -> list[str]:
    commands = []
    if local_branches:
        commands.append(f"git branch -d {' '.join(local_branches)}")
    if remote_branches:
        remote_names = [branch.removeprefix("origin/") for branch in remote_branches]
        commands.append(f"git push origin --delete {' '.join(remote_names)}")
    return commands


def _human_stoplines() -> list[str]:
    return ["local_branch_delete", "remote_branch_delete", "worktree_remove"]
