from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .finish import run
from .gates import closeout_repo
from .path_safety import redact_personal_paths, scan_personal_paths


HUMAN_STOPLINES = [
    "push",
    "pr_create",
    "merge",
    "remote_branch_delete",
    "visibility_change",
    "credential_change",
    "release_tag",
]

DEFAULT_BRANCH_CANDIDATES = (
    "origin/main",
    "main",
    "origin/master",
    "master",
)


def build_pr_packet(
    *,
    repo: Path,
    purpose: str = "",
    closeout: bool = True,
    run_packet: dict[str, Any] | None = None,
    research_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    base_branch = detect_default_branch(resolved_repo)
    current_branch = _current_branch(resolved_repo)
    visible_scope = collect_visible_scope(resolved_repo, base_branch=base_branch)
    closeout_payload = (
        closeout_repo(resolved_repo)
        if closeout
        else {
            "status": "skipped",
            "reason": "closeout skipped via --no-closeout",
        }
    )
    personal_findings = scan_personal_paths(resolved_repo)
    unknowns = _collect_unknowns(
        base_branch=base_branch,
        closeout_payload=closeout_payload,
        research_packet=research_packet,
        personal_findings=personal_findings,
    )
    reinvention = _reinvention_check(research_packet=research_packet, run_packet=run_packet)
    purpose_text = redact_personal_paths(
        purpose.strip() or _infer_purpose(run_packet=run_packet, research_packet=research_packet)
    )
    checks = {
        "closeout": closeout_payload,
        "public_path_redaction": {
            "status": "ok" if not personal_findings else "blocked",
            "findings_count": len(personal_findings),
        },
    }
    packet: dict[str, Any] = {
        "packet_type": "engineering_brain_pr",
        "version": 1,
        "repo": "<REPO>",
        "status": "plan_only",
        "purpose": purpose_text,
        "base_branch": base_branch,
        "current_branch": current_branch,
        "visible_scope": visible_scope,
        "changes": visible_scope.get("files", []),
        "checks": _safe_attached_packet(checks) or checks,
        "run_packet": _safe_attached_packet(run_packet),
        "research_packet": _safe_attached_packet(research_packet),
        "reinvention_check": _safe_attached_packet(reinvention) or reinvention,
        "unknowns": [redact_personal_paths(item) for item in unknowns],
        "human_stoplines": list(HUMAN_STOPLINES),
        "merge": {
            "status": "承認待ち",
            "allowed": False,
            "reason": "current-turn merge approval required",
        },
        "external_actions": {
            "allowed": False,
            "performed": False,
            "reason": "plan-only; push / PR create / merge require current-turn approval",
        },
    }
    packet["pr_body_ja"] = render_pr_body_ja(packet)
    return packet


def detect_default_branch(repo: Path) -> str | None:
    for candidate in DEFAULT_BRANCH_CANDIDATES:
        result = run(["git", "rev-parse", "--verify", candidate], cwd=repo)
        if result["returncode"] == 0:
            return candidate
    return None


def collect_visible_scope(repo: Path, *, base_branch: str | None) -> dict[str, Any]:
    files: list[dict[str, str]] = []
    summary = ""
    source = "worktree"
    if base_branch:
        name_status = run(["git", "diff", "--name-status", f"{base_branch}...HEAD"], cwd=repo)
        if name_status["returncode"] == 0 and name_status["stdout"].strip():
            source = f"diff:{base_branch}...HEAD"
            for line in name_status["stdout"].splitlines():
                parts = line.split("\t", maxsplit=1)
                if len(parts) != 2:
                    continue
                status, path = parts
                files.append({"status": status.strip(), "path": redact_personal_paths(path.strip())})
            stat = run(["git", "diff", "--stat", f"{base_branch}...HEAD"], cwd=repo)
            if stat["returncode"] == 0:
                summary = redact_personal_paths(stat["stdout"])
    if not files:
        status = run(["git", "status", "--short"], cwd=repo)
        source = "worktree"
        for line in status["stdout"].splitlines():
            parsed = _parse_status_line(line)
            if parsed is None:
                continue
            file_status, path = parsed
            files.append({"status": file_status, "path": redact_personal_paths(path)})
        summary = redact_personal_paths(status["stdout"]) if status["stdout"] else "差分なし（または base branch 未検出）"
    return {
        "source": source,
        "files": files,
        "summary": summary or "差分なし",
        "file_count": len(files),
    }


def _parse_status_line(line: str) -> tuple[str, str] | None:
    """Parse `git status --short` lines, including stdout that lost a leading space via strip()."""
    raw = line.rstrip()
    if not raw.strip():
        return None
    if len(raw) >= 4 and raw[2] == " ":
        status = raw[:2].replace(" ", "").strip() or "M"
        return status, raw[3:]
    parts = raw.lstrip().split(maxsplit=1)
    if len(parts) != 2:
        return "M", raw.strip()
    return parts[0].strip() or "M", parts[1]


def render_pr_body_ja(packet: dict[str, Any]) -> str:
    purpose = packet.get("purpose") or "（目的未記入）"
    changes = packet.get("changes") or []
    if changes:
        change_lines = "\n".join(
            f"- `{item.get('status', '?')}` `{item.get('path', '')}`" for item in changes
        )
    else:
        change_lines = "- （差分なし / base branch 未検出）"

    reinvention = packet.get("reinvention_check") or {}
    reinvention_lines = [
        f"- decision: `{reinvention.get('decision', 'hold')}`",
        f"- reason: {reinvention.get('reason', 'research packet not attached')}",
    ]

    checks = packet.get("checks") or {}
    closeout = checks.get("closeout") or {}
    closeout_overall = closeout.get("overall", closeout.get("status", "unknown"))
    path_status = (checks.get("public_path_redaction") or {}).get("status", "unknown")
    verification_lines = [
        f"- closeout: `{closeout_overall}`",
        f"- public_path_redaction: `{path_status}`",
        "- `python -m pytest -q`",
        "- `python -m compileall -q engineering_brain tests`",
    ]

    visible = packet.get("visible_scope") or {}
    visible_summary = visible.get("summary") or "（未収集）"
    unknowns = packet.get("unknowns") or []
    unknown_lines = "\n".join(f"- {item}" for item in unknowns) if unknowns else "- （なし）"
    stoplines = packet.get("human_stoplines") or []
    stopline_lines = "\n".join(f"- [ ] `{item}`" for item in stoplines)
    merge = packet.get("merge") or {}
    merge_status = merge.get("status", "承認待ち")

    body = f"""## 目的

{purpose}

## 変更内容

{change_lines}

## Research / reinvention check

{chr(10).join(reinvention_lines)}

## TDD / 検証

{chr(10).join(verification_lines)}

## Security / operation

- secret / token / credential を混ぜていないことを確認する
- 実ユーザー名入りローカル絶対パスは `<USER_HOME>` / `<PROJECTS_ROOT>` / `<REPO>` へ置換する
- external_actions.performed = `{bool((packet.get('external_actions') or {}).get('performed'))}`（plan-only）

## Visible scope

- source: `{visible.get('source', 'unknown')}`
- file_count: `{visible.get('file_count', 0)}`
- summary:
```
{visible_summary}
```

## 未確認と残リスク

{unknown_lines}

## Human stoplines

{stopline_lines}

## Merge

- status: **{merge_status}**
- push / PR create / merge は current-turn の明示承認が必要
"""
    return redact_personal_paths(body.strip() + "\n")


def load_packet_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("packet file must contain a JSON object")
    return payload


def _current_branch(repo: Path) -> str | None:
    result = run(["git", "branch", "--show-current"], cwd=repo)
    if result["returncode"] != 0:
        return None
    branch = result["stdout"].strip()
    return branch or None


def _safe_attached_packet(packet: dict[str, Any] | None) -> dict[str, Any] | None:
    if packet is None:
        return None
    serialized = redact_personal_paths(json.dumps(packet, ensure_ascii=False))
    return json.loads(serialized)


def _reinvention_check(
    *,
    research_packet: dict[str, Any] | None,
    run_packet: dict[str, Any] | None,
) -> dict[str, Any]:
    if research_packet:
        decision = (research_packet.get("decision") or {}).get("status", "hold")
        rationale = (research_packet.get("decision") or {}).get("rationale", "")
        return {
            "required": True,
            "decision": decision,
            "reason": rationale or "research packet attached",
        }
    if run_packet and isinstance(run_packet.get("reinvention_check"), dict):
        check = run_packet["reinvention_check"]
        return {
            "required": bool(check.get("required", True)),
            "decision": check.get("decision", "hold"),
            "reason": check.get("reason", "run packet reinvention_check"),
        }
    return {
        "required": True,
        "decision": "hold",
        "reason": "research packet not yet attached",
    }


def _infer_purpose(
    *,
    run_packet: dict[str, Any] | None,
    research_packet: dict[str, Any] | None,
) -> str:
    if run_packet and run_packet.get("task"):
        return str(run_packet["task"])
    if research_packet and research_packet.get("task"):
        return str(research_packet["task"])
    return ""


def _collect_unknowns(
    *,
    base_branch: str | None,
    closeout_payload: dict[str, Any],
    research_packet: dict[str, Any] | None,
    personal_findings: list[Any],
) -> list[str]:
    unknowns: list[str] = []
    if base_branch is None:
        unknowns.append("default branch を検出できず、diff scope が worktree 依存")
    if closeout_payload.get("status") == "skipped":
        unknowns.append("closeout 未実行（--no-closeout）")
    elif closeout_payload.get("overall") not in {None, "ok"} and closeout_payload.get("status") != "ok":
        if closeout_payload.get("overall") == "blocked":
            unknowns.append("closeout overall=blocked")
    if research_packet is None:
        unknowns.append("research / reinvention evidence 未添付")
    if personal_findings:
        unknowns.append("personal path findings remain in repo text files")
    return unknowns
