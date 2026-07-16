from __future__ import annotations

from pathlib import Path
from typing import Any

from .gates import closeout_repo, evaluate_triggers, route_task
from .registry import select_technology_sources
from .skill_sync import compare_skill, default_runtime_root


HUMAN_STOPLINES = [
    "push",
    "pr_create",
    "merge",
    "remote_branch_delete",
    "visibility_change",
    "credential_change",
    "runtime_copy_direct_edit",
]


def build_run_packet(*, task: str, repo: Path, domain: str | None, closeout: bool) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    route = route_task(task)
    gates = evaluate_triggers(route["inferred_triggers"])
    catalog_domain = domain or _infer_catalog_domain(task)
    sources = select_technology_sources(catalog_domain) if catalog_domain else []
    skill_source = resolved_repo / "skills" / "engineering-autopilot"
    skill_sync = compare_skill(source_dir=skill_source, runtime_root=default_runtime_root())
    closeout_payload: dict[str, Any]
    if closeout:
        closeout_payload = closeout_repo(resolved_repo)
    else:
        closeout_payload = {
            "status": "skipped",
            "reason": "run packet MVP defaults to planning; pass --closeout to execute local verification",
        }

    blocked = set(route["blocked_actions"])
    blocked.update(HUMAN_STOPLINES)
    status = "blocked_until_human_review" if blocked else "ready_for_local_work"

    return {
        "packet_type": "engineering_autopilot_run",
        "version": 1,
        "task": task,
        "repo": "<REPO>",
        "status": status,
        "route": route,
        "gates": gates,
        "catalog": {
            "domain": catalog_domain,
            "sources": [_serialize_source(source) for source in sources],
            "adoption_rule": "candidate sources are advisory until adopted by test/docs/ADR",
        },
        "skill_sync": skill_sync,
        "closeout": closeout_payload,
        "verification": {
            "closeout_status": closeout_payload.get("overall", closeout_payload.get("status")),
            "skill_sync_status": skill_sync["status"],
        },
        "human_stoplines": sorted(blocked),
        "next_actions": [
            "review run packet",
            "add or confirm targeted tests before implementation",
            "keep push, PR, merge, cleanup, visibility, and credential actions behind current-turn approval",
        ],
    }


def _infer_catalog_domain(task: str) -> str | None:
    normalized = task.lower()
    if any(token in normalized for token in ("python", "pytest", "cli")):
        return "python"
    if any(token in normalized for token in ("go", "golang")):
        return "go"
    if any(token in normalized for token in ("frontend", "react", "ui")):
        return "frontend"
    if any(token in normalized for token in ("azure", "az", "cloud")):
        return "azure"
    return None


def _serialize_source(source: Any) -> dict[str, Any]:
    return {
        "id": source.id,
        "domain": source.domain,
        "status": source.status,
        "source_refs": list(source.source_refs),
        "use_when": list(source.use_when),
        "adoption_route": source.adoption_route,
        "gate_hint": source.gate_hint,
        "insufficient_if": list(source.insufficient_if),
    }
