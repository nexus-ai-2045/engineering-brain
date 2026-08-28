from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


PROTECTED_BRANCHES = {"main", "master", "develop", "dev"}
HOOK_NAMES = ["pre-commit", "post-merge"]

# 削除の実行正本。FDE の ADR-0006 が宣言している。
# 本 repo は plan と stopline の提示に徹し、削除自体は委譲する。
# CLEANUP_SSOT_COMMAND は FDE checkout 上で動くテンプレートであり、
# この repo の cwd から直接実行できるパスではない。
CLEANUP_SSOT = "fractal-decision-ecosystem scripts/post_merge_cleanup.py"
CLEANUP_SSOT_COMMAND = "python scripts/post_merge_cleanup.py --apply --cwd <REPO>"
CLEANUP_SSOT_COMMAND_NOTE = (
    "Run from a fractal-decision-ecosystem checkout. "
    "Replace <REPO> with the absolute path of the target git root. "
    "This engineering-brain tree does not contain the SSOT script."
)

_LOCAL_BASE_CANDIDATES = ("refs/heads/main", "refs/heads/master")
_REMOTE_BASE_CANDIDATES = ("refs/remotes/origin/main", "refs/remotes/origin/master")


def _ref_exists(repo: Path, ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], cwd=repo)["returncode"] == 0


def resolve_base_refs(repo: Path) -> dict[str, str | None]:
    """local / remote それぞれで解決可能な base ref を返す。

    bare `main` を決め打ちすると、PR checkout のように local main が無い
    環境で `git branch --merged main` が `malformed object name main` で
    失敗する。FDE が ADR-0006 でインシデントとして記録し修正済みの経路。
    解決できない側は None を返し、呼び出し側が候補ゼロと区別できるようにする。
    """
    local = next((ref for ref in _LOCAL_BASE_CANDIDATES if _ref_exists(repo, ref)), None)
    if local is None:
        local = next((ref for ref in _REMOTE_BASE_CANDIDATES if _ref_exists(repo, ref)), None)
    remote = next((ref for ref in _REMOTE_BASE_CANDIDATES if _ref_exists(repo, ref)), None)
    return {"local": local, "remote": remote}


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

    base_refs = resolve_base_refs(resolved_repo)
    if base_refs["local"] is None and base_refs["remote"] is None:
        # 候補ゼロと「base が引けなかった」を混同しない。混同すると
        # 掃除漏れを ok として報告してしまう
        return {
            "status": "blocked",
            "reason": "base_ref_unresolved",
            "repo": "<REPO>",
            "current_branch": current_branch,
            "base_refs": base_refs,
            "local_merged_branches": [],
            "remote_merged_branches": [],
            "human_stoplines": _human_stoplines(),
            "suggested_commands": [],
        }

    local_branches: list[str] = []
    if base_refs["local"] is not None:
        local_result = run(
            ["git", "branch", "--merged", base_refs["local"], "--format", "%(refname:short)"],
            cwd=resolved_repo,
        )
        if local_result["returncode"] != 0:
            # returncode を握りつぶすと「候補ゼロ」と誤認する（bare main と同型）
            return {
                "status": "blocked",
                "reason": "merged_local_list_failed",
                "repo": "<REPO>",
                "current_branch": current_branch,
                "base_refs": base_refs,
                "git_result": local_result,
                "local_merged_branches": [],
                "remote_merged_branches": [],
                "human_stoplines": _human_stoplines(),
                "suggested_commands": [],
                "cleanup_ssot": CLEANUP_SSOT,
            }
        local_branches = _cleanup_local_branches(
            local_result["stdout"], current_branch=current_branch
        )
    remote_branches: list[str] = []
    if base_refs["remote"] is not None:
        remote_result = run(
            ["git", "branch", "-r", "--merged", base_refs["remote"], "--format", "%(refname:short)"],
            cwd=resolved_repo,
        )
        if remote_result["returncode"] != 0:
            return {
                "status": "blocked",
                "reason": "merged_remote_list_failed",
                "repo": "<REPO>",
                "current_branch": current_branch,
                "base_refs": base_refs,
                "git_result": remote_result,
                "local_merged_branches": local_branches,
                "remote_merged_branches": [],
                "human_stoplines": _human_stoplines(),
                "suggested_commands": [],
                "cleanup_ssot": CLEANUP_SSOT,
            }
        remote_branches = _cleanup_remote_branches(
            remote_result["stdout"], remote_base=base_refs["remote"]
        )
    suggested = _suggested_commands(local_branches, remote_branches)

    return {
        "status": "action_available" if local_branches or remote_branches else "ok",
        "reason": "merged_cleanup_candidates" if local_branches or remote_branches else "nothing_to_clean",
        "repo": "<REPO>",
        "current_branch": current_branch,
        "base_refs": base_refs,
        "local_merged_branches": local_branches,
        "remote_merged_branches": remote_branches,
        "human_stoplines": _human_stoplines(),
        "suggested_commands": suggested,
        "cleanup_ssot": CLEANUP_SSOT,
        "cleanup_ssot_command": CLEANUP_SSOT_COMMAND,
        "cleanup_ssot_command_note": CLEANUP_SSOT_COMMAND_NOTE,
        "apply_policy": {
            "default": "plan_only",
            "local_cleanup": "delegated_to_cleanup_ssot",
            "remote_cleanup": "delegated_to_cleanup_ssot",
        },
    }


def apply_local_cleanup(repo: Path) -> dict[str, Any]:
    """削除は実行せず、実行正本への委譲を返す。

    branch 削除の実装は FDE の post_merge_cleanup.py を正本とする
    (ADR-0006)。本 repo が独自に削除すると、正本側で修正済みの学習
    (base ref 解決、remote-tracking の prune、GitHub 設定の確認) が
    届かないまま二重実装が残る。実際に bare `main` 決め打ちという
    正本が既に潰したバグを本 repo は踏んでいた。

    plan と stopline の提示はこの repo の役割として残す。
    """
    plan = finish_plan(repo)
    plan["mode"] = "apply-local"
    plan["applied"] = False
    plan["delegated_to"] = CLEANUP_SSOT
    plan["delegated_command"] = CLEANUP_SSOT_COMMAND
    plan["delegated_command_note"] = CLEANUP_SSOT_COMMAND_NOTE
    plan["reason_not_applied"] = "local_delete_delegated_to_cleanup_ssot"
    return plan


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
        target.chmod(0o755)
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


def _cleanup_remote_branches(stdout: str, *, remote_base: str | None = None) -> list[str]:
    # origin/main だけでなく、解決済み remote base（例: origin/master）も除外する。
    excluded = {"origin/main", "origin/master", "origin/HEAD"}
    if remote_base is not None:
        excluded.add(remote_base.removeprefix("refs/remotes/"))
    branches = []
    for line in stdout.splitlines():
        branch = line.strip()
        if not branch or branch in excluded:
            continue
        if " -> " in branch:
            continue
        branches.append(branch)
    return branches


def _suggested_commands(local_branches: list[str], remote_branches: list[str]) -> list[str]:
    # この checkout には SSOT script が無いので、cwd 相対の実行コマンドは出さない。
    # 委譲先は cleanup_ssot / cleanup_ssot_command(_note) を機械可読に載せる。
    _ = (local_branches, remote_branches)
    return []


def _human_stoplines() -> list[str]:
    return ["local_branch_delete", "remote_branch_delete", "worktree_remove"]
