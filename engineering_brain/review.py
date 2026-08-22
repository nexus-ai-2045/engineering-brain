from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .gates import closeout_repo, run
from .path_safety import PERSONAL_PATH_PATTERN, redact_personal_paths


HUMAN_STOPLINES = [
    "pr_create",
    "push",
    "merge",
    "visibility_change",
    "credential_change",
    "remote_branch_delete",
    "release_tag",
]

DEFAULT_BASE_CANDIDATES = ("main", "master")


def build_pr_packet(
    *,
    repo: Path,
    purpose: str = "",
    closeout: bool = False,
    run_packet: dict[str, Any] | Path | None = None,
    research_packet: dict[str, Any] | Path | None = None,
    base: str | None = None,
) -> dict[str, Any]:
    """Build a plan-only PR packet from local repo state.

    Never creates or pushes a GitHub PR. Reuses ``closeout_repo`` for
    verification evidence instead of inventing a second closeout path.
    """
    resolved_repo = repo.resolve()
    attached_run = _load_optional_packet(run_packet)
    attached_research = _load_optional_packet(research_packet)

    if closeout:
        closeout_payload = closeout_repo(resolved_repo)
    else:
        closeout_payload = {
            "status": "skipped",
            "reason": "PR packet defaults to planning without local verification; pass --closeout to execute",
            "overall": "skipped",
        }

    diff_summary = _collect_diff_summary(resolved_repo, base=base)
    purpose_text = purpose.strip() or _infer_purpose(diff_summary, attached_run)
    changes = _summarize_changes(diff_summary)
    visible_scope = _visible_scope(diff_summary, closeout_payload)
    checks = _checks_from_closeout(closeout_payload)
    unknowns = _collect_unknowns(closeout_payload, attached_run, attached_research, diff_summary)
    reinvention = _reinvention_from_research(attached_research, attached_run)

    packet: dict[str, Any] = {
        "packet_type": "engineering_brain_pr",
        "version": 1,
        "repo": "<REPO>",
        "mode": "plan_only",
        "status": "awaiting_human_approval",
        "merge_status": "承認待ち",
        "purpose": purpose_text,
        "changes": changes,
        "visible_scope": visible_scope,
        "checks": checks,
        "unknowns": unknowns,
        "reinvention_check": reinvention,
        "human_stoplines": list(HUMAN_STOPLINES),
        "external_actions": {
            "allowed": False,
            "actions_performed": False,
            "reason": "PR packet is plan-only; push / pr_create / merge require current-turn approval",
            "blocked_actions": [
                "github pr create",
                "git push",
                "merge",
                "visibility change",
                "release / tag",
            ],
        },
        "diff": diff_summary,
        "closeout": closeout_payload,
        "run_packet": attached_run,
        "research_packet": attached_research,
    }
    packet["pr_body_ja"] = render_pr_body_ja(packet)
    return _redact_packet(packet, repo=resolved_repo)


def render_pr_body_ja(packet: dict[str, Any]) -> str:
    purpose = str(packet.get("purpose") or "（目的未記入）")
    changes = packet.get("changes") or []
    if isinstance(changes, list) and changes:
        change_lines = "\n".join(f"- {item}" for item in changes)
    else:
        change_lines = "- （変更要約なし）"

    reinvention = packet.get("reinvention_check") or {}
    decision = reinvention.get("decision", "hold")
    reason = reinvention.get("reason", "research packet 未添付")

    checks = packet.get("checks") or {}
    verification_lines = [
        f"- closeout overall: `{checks.get('closeout_overall', 'unknown')}`",
        f"- pytest: `{checks.get('pytest', 'unknown')}`",
        f"- compile: `{checks.get('compile', 'unknown')}`",
        f"- public_path_redaction: `{checks.get('public_path_redaction', 'unknown')}`",
    ]

    visible = packet.get("visible_scope") or {}
    files = visible.get("changed_files") or []
    file_lines = "\n".join(f"- `{path}`" for path in files) if files else "- （差分ファイルなし / base 未解決）"

    unknowns = packet.get("unknowns") or []
    unknown_lines = "\n".join(f"- {item}" for item in unknowns) if unknowns else "- なし"

    stoplines = packet.get("human_stoplines") or HUMAN_STOPLINES
    stopline_lines = "\n".join(f"- [ ] `{item}` は現在会話の明示承認が必要" for item in stoplines)

    merge_status = packet.get("merge_status", "承認待ち")

    return "\n".join(
        [
            "## 目的",
            "",
            purpose,
            "",
            "## 変更内容",
            "",
            change_lines,
            "",
            "## Research / reinvention check",
            "",
            f"- decision: `{decision}`",
            f"- reason: {reason}",
            "",
            "## TDD / 検証",
            "",
            *verification_lines,
            "",
            "## Security / operation",
            "",
            "- secret / credential は混入していない想定（closeout / 目視で再確認）",
            "- 実ユーザー名入りローカル絶対パスは redaction 済み",
            "- 外部状態変更は `external_actions.allowed=false`",
            "",
            "## Visible scope",
            "",
            f"- base: `{visible.get('base', 'unknown')}`",
            f"- head: `{visible.get('head', 'unknown')}`",
            "- 外から見える変更ファイル:",
            file_lines,
            "",
            "## 未確認と残リスク",
            "",
            unknown_lines,
            "",
            "## Human stoplines",
            "",
            stopline_lines,
            "",
            f"## Merge",
            "",
            f"- 状態: **{merge_status}**（この generator は PR 作成・push・merge を実行しない）",
            "",
        ]
    )


def _load_optional_packet(value: dict[str, Any] | Path | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    path = Path(value)
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_diff_summary(repo: Path, *, base: str | None) -> dict[str, Any]:
    status = run(["git", "status", "--short", "--branch"], cwd=repo)
    head = _current_branch(status.get("stdout", ""))
    resolved_base = base or _detect_default_base(repo)
    files: list[str] = []
    name_status: list[str] = []
    stat = ""
    available = False
    reason = "no_default_base"

    if resolved_base:
        range_ref = f"{resolved_base}...HEAD"
        name_result = run(["git", "diff", "--name-only", range_ref], cwd=repo)
        status_result = run(["git", "diff", "--name-status", range_ref], cwd=repo)
        stat_result = run(["git", "diff", "--stat", range_ref], cwd=repo)
        if name_result["returncode"] == 0:
            available = True
            reason = "ok"
            files = [line.strip() for line in name_result["stdout"].splitlines() if line.strip()]
            name_status = [line.strip() for line in status_result["stdout"].splitlines() if line.strip()]
            stat = redact_personal_paths(stat_result["stdout"], repo=repo)
        else:
            reason = "diff_failed"

    worktree_files, worktree_status = _worktree_changes(repo)
    for path in worktree_files:
        if path not in files:
            files.append(path)
    for line in worktree_status:
        if line not in name_status:
            name_status.append(line)
    if worktree_files and not available and resolved_base is None:
        available = True
        reason = "worktree_only"

    dirty = [line for line in status.get("stdout", "").splitlines()[1:] if line.strip()]
    return {
        "available": available or bool(files),
        "reason": reason if (available or files) else reason,
        "base": resolved_base,
        "head": head,
        "files": files,
        "name_status": name_status,
        "stat": stat,
        "dirty": dirty,
        "git_status": {
            "returncode": status.get("returncode"),
            "stdout": redact_personal_paths(status.get("stdout", ""), repo=repo),
            "stderr": redact_personal_paths(status.get("stderr", ""), repo=repo),
        },
    }


def _worktree_changes(repo: Path) -> tuple[list[str], list[str]]:
    files: list[str] = []
    name_status: list[str] = []
    unstaged = run(["git", "diff", "--name-status"], cwd=repo)
    staged = run(["git", "diff", "--cached", "--name-status"], cwd=repo)
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo)
    for result in (unstaged, staged):
        if result["returncode"] != 0:
            continue
        for line in result["stdout"].splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            name_status.append(stripped)
            parts = stripped.split("\t", maxsplit=1)
            if len(parts) == 2 and parts[1] not in files:
                files.append(parts[1])
    if untracked["returncode"] == 0:
        for path in untracked["stdout"].splitlines():
            stripped = path.strip()
            if not stripped:
                continue
            if stripped not in files:
                files.append(stripped)
            entry = f"?\t{stripped}"
            if entry not in name_status:
                name_status.append(entry)
    return files, name_status


def _detect_default_base(repo: Path) -> str | None:
    symbolic = run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=repo)
    if symbolic["returncode"] == 0 and symbolic["stdout"].strip():
        ref = symbolic["stdout"].strip()
        if ref.startswith("refs/remotes/origin/"):
            remote_branch = ref.removeprefix("refs/remotes/")
            probe = run(["git", "rev-parse", "--verify", remote_branch], cwd=repo)
            if probe["returncode"] == 0:
                return remote_branch

    for candidate in DEFAULT_BASE_CANDIDATES:
        for ref in (f"origin/{candidate}", candidate):
            probe = run(["git", "rev-parse", "--verify", ref], cwd=repo)
            if probe["returncode"] == 0:
                return ref
    return None


def _current_branch(status_stdout: str) -> str | None:
    first = status_stdout.splitlines()[0] if status_stdout.splitlines() else ""
    if first.startswith("## "):
        return first[3:].split("...", maxsplit=1)[0].strip() or None
    return None


def _infer_purpose(diff_summary: dict[str, Any], run_packet: dict[str, Any] | None) -> str:
    if run_packet and run_packet.get("task"):
        return str(run_packet["task"])
    files = diff_summary.get("files") or []
    if files:
        return f"local changes against {diff_summary.get('base') or 'unknown base'} ({len(files)} files)"
    return "PR packet generated from local repo state"


def _summarize_changes(diff_summary: dict[str, Any]) -> list[str]:
    name_status = diff_summary.get("name_status") or []
    if name_status:
        return [redact_personal_paths(line) for line in name_status]
    files = diff_summary.get("files") or []
    if files:
        return [f"M\t{path}" for path in files]
    if diff_summary.get("dirty"):
        return ["uncommitted local changes present (see git status)"]
    return []


def _visible_scope(diff_summary: dict[str, Any], closeout_payload: dict[str, Any]) -> dict[str, Any]:
    redaction = (
        closeout_payload.get("operation", {})
        .get("public_path_redaction", {})
        .get("status", closeout_payload.get("status", "unknown"))
    )
    return {
        "base": diff_summary.get("base"),
        "head": diff_summary.get("head"),
        "changed_files": list(diff_summary.get("files") or []),
        "public_path_redaction": redaction,
        "note": "外から見えるのは上記 changed_files と PR body。secret / personal path は含めない。",
    }


def _checks_from_closeout(closeout_payload: dict[str, Any]) -> dict[str, Any]:
    if closeout_payload.get("status") == "skipped":
        return {
            "closeout_overall": "skipped",
            "pytest": "skipped",
            "compile": "skipped",
            "public_path_redaction": "skipped",
        }
    verification = closeout_payload.get("verification", {})
    pytest_rc = verification.get("pytest", {}).get("returncode")
    compile_rc = verification.get("compileall", {}).get("returncode")
    redaction = (
        closeout_payload.get("operation", {})
        .get("public_path_redaction", {})
        .get("status", "unknown")
    )
    return {
        "closeout_overall": closeout_payload.get("overall", "unknown"),
        "pytest": "ok" if pytest_rc == 0 else ("blocked" if pytest_rc is not None else "unknown"),
        "compile": "ok" if compile_rc == 0 else ("blocked" if compile_rc is not None else "unknown"),
        "public_path_redaction": redaction,
    }


def _collect_unknowns(
    closeout_payload: dict[str, Any],
    run_packet: dict[str, Any] | None,
    research_packet: dict[str, Any] | None,
    diff_summary: dict[str, Any],
) -> list[str]:
    unknowns: list[str] = []
    if closeout_payload.get("status") == "skipped":
        unknowns.append("closeout 未実行（--closeout で verification を添付できる）")
    elif closeout_payload.get("overall") not in {"ok", None} and closeout_payload.get("overall") != "skipped":
        if closeout_payload.get("overall") == "blocked":
            unknowns.append("closeout overall=blocked（失敗または path findings を確認）")

    if not diff_summary.get("available"):
        unknowns.append(f"default branch との diff を解決できない: {diff_summary.get('reason')}")
    if diff_summary.get("dirty"):
        unknowns.append("未コミット変更がある")
    if research_packet is None and (run_packet is None or not run_packet.get("reinvention_check")):
        unknowns.append("research / reinvention evidence 未添付")
    if research_packet and research_packet.get("unknowns"):
        unknowns.extend(str(item) for item in research_packet["unknowns"])
    return unknowns


def _reinvention_from_research(
    research_packet: dict[str, Any] | None,
    run_packet: dict[str, Any] | None,
) -> dict[str, Any]:
    if research_packet and isinstance(research_packet.get("decision"), dict):
        decision = research_packet["decision"]
        return {
            "required": True,
            "decision": decision.get("status", "hold"),
            "reason": decision.get("rationale") or decision.get("rule") or "research packet attached",
        }
    if run_packet and isinstance(run_packet.get("reinvention_check"), dict):
        return dict(run_packet["reinvention_check"])
    return {
        "required": True,
        "decision": "hold",
        "reason": "research packet not yet attached",
    }


def _redact_packet(packet: dict[str, Any], *, repo: Path) -> dict[str, Any]:
    return json.loads(redact_personal_paths(json.dumps(packet, ensure_ascii=False), repo=repo))


def assert_no_personal_paths(text: str) -> None:
    if PERSONAL_PATH_PATTERN.search(text):
        raise ValueError("personal absolute path must be redacted before public packet emission")
