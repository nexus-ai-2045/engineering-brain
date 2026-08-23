from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .feedback import SECRET_LIKE_PATTERN
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

SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas"
RUN_PACKET_SCHEMA = json.loads((SCHEMA_ROOT / "run-packet.schema.json").read_text(encoding="utf-8"))
RESEARCH_PACKET_SCHEMA = json.loads(
    (SCHEMA_ROOT / "research-packet.schema.json").read_text(encoding="utf-8")
)


def build_pr_packet(
    *,
    repo: Path,
    purpose: str = "",
    closeout: bool = True,
    base: str | None = None,
    run_packet: dict[str, Any] | None = None,
    research_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    base_branch = base or detect_default_branch(resolved_repo)
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

    validated_run, run_errors = validate_attached_packet(run_packet, kind="run")
    validated_research, research_errors = validate_attached_packet(research_packet, kind="research")

    unknowns = _collect_unknowns(
        base_branch=base_branch,
        closeout_payload=closeout_payload,
        research_packet=validated_research,
        research_errors=research_errors,
        run_errors=run_errors,
        personal_findings=personal_findings,
    )
    reinvention = _reinvention_check(research_packet=validated_research, run_packet=validated_run)
    purpose_text = redact_personal_paths(
        purpose.strip()
        or _infer_purpose(run_packet=validated_run, research_packet=validated_research)
    )
    checks = {
        "closeout": closeout_payload,
        "public_path_redaction": {
            "status": "ok" if not personal_findings else "blocked",
            "findings_count": len(personal_findings),
        },
        "attachment_validation": {
            "run_packet": "ok" if validated_run is not None else ("missing" if run_packet is None else "invalid"),
            "research_packet": (
                "ok"
                if validated_research is not None
                else ("missing" if research_packet is None else "invalid")
            ),
            "run_errors": run_errors,
            "research_errors": research_errors,
        },
    }
    safe_checks, checks_scrubbed = _safe_attached_packet(checks)
    safe_run, run_scrubbed = _safe_attached_packet(validated_run)
    safe_research, research_scrubbed = _safe_attached_packet(validated_research)
    safe_reinvention, _ = _safe_attached_packet(reinvention)
    if checks_scrubbed or run_scrubbed or research_scrubbed:
        unknowns.append("secret-like content was scrubbed from attached evidence")

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
        "checks": safe_checks or checks,
        "run_packet": safe_run,
        "research_packet": safe_research,
        "reinvention_check": safe_reinvention or reinvention,
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


def public_stdout_packet(
    packet: dict[str, Any],
    *,
    purpose_override: str | None = None,
) -> dict[str, Any]:
    """Return a stdout-safe copy without nested command transcripts or raw attachments."""
    closeout = (packet.get("checks") or {}).get("closeout") or {}
    verification = closeout.get("verification") or {}
    public_closeout: dict[str, Any] = {
        "overall": closeout.get("overall"),
        "status": closeout.get("status"),
        "reason": closeout.get("reason"),
    }
    if verification:
        public_closeout["verification"] = {
            "status": verification.get("status"),
            "pytest": _command_summary(verification.get("pytest")),
            "compileall": _command_summary(verification.get("compileall")),
        }
    attachment = (packet.get("checks") or {}).get("attachment_validation") or {}
    purpose = purpose_override if purpose_override is not None else ""
    safe = {
        "packet_type": "engineering_brain_pr",
        "version": 1,
        "repo": "<REPO>",
        "status": "plan_only",
        "purpose": purpose,
        "base_branch": packet.get("base_branch"),
        "current_branch": packet.get("current_branch"),
        "visible_scope": {
            "source": (packet.get("visible_scope") or {}).get("source"),
            "files": list((packet.get("visible_scope") or {}).get("files") or []),
            "summary": str((packet.get("visible_scope") or {}).get("summary") or ""),
            "file_count": (packet.get("visible_scope") or {}).get("file_count", 0),
        },
        "changes": list(packet.get("changes") or []),
        "checks": {
            "closeout": public_closeout,
            "public_path_redaction": (packet.get("checks") or {}).get("public_path_redaction"),
            "attachment_validation": {
                "run_packet": attachment.get("run_packet"),
                "research_packet": attachment.get("research_packet"),
                "run_errors": list(attachment.get("run_errors") or []),
                "research_errors": list(attachment.get("research_errors") or []),
            },
        },
        "run_packet": _attachment_summary(packet.get("run_packet")),
        "research_packet": _attachment_summary(packet.get("research_packet")),
        "reinvention_check": {
            "required": True,
            "decision": _allowlisted_decision((packet.get("reinvention_check") or {}).get("decision")),
            "reason": "research packet attached"
            if attachment.get("research_packet") == "ok"
            else "research packet not yet attached",
        },
        "unknowns": _allowlisted_unknowns(packet.get("unknowns") or []),
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
    safe["pr_body_ja"] = _safe_pr_body({**packet, "purpose": purpose, "checks": safe["checks"]})
    return safe


def _allowlisted_decision(value: Any) -> str:
    allowed = {
        "reuse": "reuse",
        "wrap": "wrap",
        "extend": "extend",
        "adopt_oss": "adopt_oss",
        "build": "build",
        "hold": "hold",
        "rejected": "rejected",
    }
    return allowed.get(str(value), "hold")


def _allowlisted_unknowns(items: list[Any]) -> list[str]:
    catalog = {
        "default branch を検出できず、diff scope が worktree 依存": "default branch を検出できず、diff scope が worktree 依存",
        "closeout 未実行（--no-closeout）": "closeout 未実行（--no-closeout）",
        "closeout overall=blocked": "closeout overall=blocked",
        "research / reinvention evidence 未添付": "research / reinvention evidence 未添付",
        "attached research packet failed schema validation": "attached research packet failed schema validation",
        "attached run packet failed schema validation": "attached run packet failed schema validation",
        "personal path findings remain in repo text files": "personal path findings remain in repo text files",
        "secret-like content was scrubbed from attached evidence": "secret-like content was scrubbed from attached evidence",
        "decision rationale is not recorded": "decision rationale is not recorded",
    }
    return [catalog[str(item)] for item in items if str(item) in catalog]


def _safe_pr_body(packet: dict[str, Any]) -> str:
    """Rebuild Japanese body from allowlisted fields only (no raw attachment free text)."""
    safe_packet = {
        "purpose": str(packet.get("purpose") or "（目的未記入）"),
        "changes": list(packet.get("changes") or []),
        "reinvention_check": {
            "decision": _allowlisted_decision((packet.get("reinvention_check") or {}).get("decision")),
            "reason": "research packet attached"
            if (packet.get("checks") or {}).get("attachment_validation", {}).get("research_packet") == "ok"
            else "research packet not yet attached",
        },
        "checks": {
            "closeout": {
                "overall": ((packet.get("checks") or {}).get("closeout") or {}).get("overall")
                or ((packet.get("checks") or {}).get("closeout") or {}).get("status"),
                "verification": {
                    "pytest": _command_summary(
                        (((packet.get("checks") or {}).get("closeout") or {}).get("verification") or {}).get(
                            "pytest"
                        )
                    ),
                    "compileall": _command_summary(
                        (((packet.get("checks") or {}).get("closeout") or {}).get("verification") or {}).get(
                            "compileall"
                        )
                    ),
                },
            },
            "public_path_redaction": (packet.get("checks") or {}).get("public_path_redaction")
            or {"status": "unknown"},
        },
        "visible_scope": {
            "source": (packet.get("visible_scope") or {}).get("source", "unknown"),
            "summary": str((packet.get("visible_scope") or {}).get("summary") or "（未収集）"),
            "file_count": (packet.get("visible_scope") or {}).get("file_count", 0),
        },
        "unknowns": _allowlisted_unknowns(packet.get("unknowns") or []),
        "human_stoplines": list(HUMAN_STOPLINES),
        "merge": {"status": "承認待ち"},
        "external_actions": {"performed": False},
    }
    return render_pr_body_ja(safe_packet)


def _command_summary(result: Any) -> dict[str, Any] | None:
    if not isinstance(result, dict):
        return None
    return {
        "command": result.get("command"),
        "returncode": result.get("returncode"),
    }


def _attachment_summary(packet: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(packet, dict):
        return None
    decision = packet.get("decision")
    raw_status = decision.get("status") if isinstance(decision, dict) else packet.get("status")
    allowed = {
        "reuse": "reuse",
        "wrap": "wrap",
        "extend": "extend",
        "adopt_oss": "adopt_oss",
        "build": "build",
        "hold": "hold",
        "rejected": "rejected",
        "blocked_until_human_review": "blocked_until_human_review",
        "ready_for_local_work": "ready_for_local_work",
        "skipped": "skipped",
    }
    status = allowed.get(str(raw_status), "hold")
    packet_type = (
        "engineering_autopilot_run"
        if packet.get("packet_type") == "engineering_autopilot_run"
        else "engineering_brain_research"
    )
    return {
        "packet_type": packet_type,
        "version": 1,
        "status": status,
        "attached": True,
    }


def detect_default_branch(repo: Path) -> str | None:
    """Resolve the remote default branch without calling `git remote show`.

    `git remote show origin` can echo credential-bearing remote URLs into stdout.
    Prefer symbolic-ref / rev-parse which return only ref names.
    """
    symbolic = run(["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd=repo)
    if symbolic["returncode"] == 0 and symbolic["stdout"].strip():
        ref = symbolic["stdout"].strip()
        if ref.startswith("refs/remotes/"):
            return ref.removeprefix("refs/remotes/")
        return ref

    abbrev = run(["git", "rev-parse", "--abbrev-ref", "origin/HEAD"], cwd=repo)
    if abbrev["returncode"] == 0:
        name = abbrev["stdout"].strip()
        if name and name != "origin/HEAD":
            return name
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
                parsed = _parse_name_status_line(line)
                if parsed is None:
                    continue
                files.append(parsed)
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
        summary = (
            redact_personal_paths(status["stdout"])
            if status["stdout"]
            else "差分なし（または base branch 未検出）"
        )
    return {
        "source": source,
        "files": files,
        "summary": summary or "差分なし",
        "file_count": len(files),
    }


def _parse_name_status_line(line: str) -> dict[str, str] | None:
    """Parse `git diff --name-status` including rename/copy (`R100\\told\\tnew`)."""
    raw = line.rstrip()
    if not raw.strip():
        return None
    parts = raw.split("\t")
    if len(parts) < 2:
        return None
    status = parts[0].strip()
    if status[:1] in {"R", "C"} and len(parts) >= 3:
        return {
            "status": status,
            "old_path": redact_personal_paths(parts[1].strip()),
            "new_path": redact_personal_paths(parts[2].strip()),
            "path": redact_personal_paths(parts[2].strip()),
        }
    return {
        "status": status,
        "path": redact_personal_paths(parts[1].strip()),
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
        change_lines = []
        for item in changes:
            status = item.get("status", "?")
            if item.get("old_path") and item.get("new_path"):
                change_lines.append(
                    f"- `{status}` `{item['old_path']}` → `{item['new_path']}`"
                )
            else:
                change_lines.append(f"- `{status}` `{item.get('path', '')}`")
        change_block = "\n".join(change_lines)
    else:
        change_block = "- （差分なし / base branch 未検出）"

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
        *_verification_command_lines(closeout),
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

{change_block}

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
    scrubbed, _ = scrub_secret_like(redact_personal_paths(body.strip() + "\n"))
    return scrubbed


def _verification_command_lines(closeout: dict[str, Any]) -> list[str]:
    if closeout.get("status") == "skipped":
        return ["- verification commands: （closeout 未実行）"]
    verification = closeout.get("verification") or {}
    lines: list[str] = []
    for key in ("pytest", "compileall"):
        result = verification.get(key)
        if not isinstance(result, dict):
            continue
        command = result.get("command")
        if not command:
            continue
        code = result.get("returncode")
        lines.append(f"- `{command}` → returncode={code}")
    if not lines:
        lines.append("- verification commands: （closeout payload に command 記録なし）")
    return lines


def load_packet_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("packet file must contain a JSON object")
    # Scrub before the value becomes PR evidence / stdout material.
    scrubbed, _ = scrub_secret_like(json.dumps(payload, ensure_ascii=False))
    loaded = json.loads(scrubbed)
    if not isinstance(loaded, dict):
        raise ValueError("packet file must contain a JSON object")
    return loaded


def validate_attached_packet(
    packet: dict[str, Any] | None,
    *,
    kind: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    if packet is None:
        return None, []
    schema = RUN_PACKET_SCHEMA if kind == "run" else RESEARCH_PACKET_SCHEMA
    expected_type = (
        "engineering_autopilot_run" if kind == "run" else "engineering_brain_research"
    )
    errors: list[str] = []
    if packet.get("packet_type") != expected_type:
        errors.append(f"{kind} packet_type must be {expected_type}")
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(packet), key=lambda item: list(item.absolute_path)):
        path = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{path}: {error.message}")
    if errors:
        return None, errors
    return packet, []


def scrub_secret_like(text: str) -> tuple[str, bool]:
    found = bool(SECRET_LIKE_PATTERN.search(text))
    return SECRET_LIKE_PATTERN.sub("<REDACTED_SECRET>", text), found


def _current_branch(repo: Path) -> str | None:
    result = run(["git", "branch", "--show-current"], cwd=repo)
    if result["returncode"] != 0:
        return None
    branch = result["stdout"].strip()
    return branch or None


def _safe_attached_packet(packet: dict[str, Any] | None) -> tuple[dict[str, Any] | None, bool]:
    if packet is None:
        return None, False
    serialized = redact_personal_paths(json.dumps(packet, ensure_ascii=False))
    scrubbed, found = scrub_secret_like(serialized)
    return json.loads(scrubbed), found


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
    research_errors: list[str],
    run_errors: list[str],
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
    if research_errors:
        unknowns.append("attached research packet failed schema validation")
    elif research_packet is None:
        unknowns.append("research / reinvention evidence 未添付")
    else:
        for item in research_packet.get("unknowns") or []:
            unknowns.append(str(item))
    if run_errors:
        unknowns.append("attached run packet failed schema validation")
    if personal_findings:
        unknowns.append("personal path findings remain in repo text files")
    return unknowns
