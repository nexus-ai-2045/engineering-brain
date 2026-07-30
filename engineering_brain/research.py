from __future__ import annotations

from typing import Any

from .registry import select_technology_sources


DECISIONS = ("reuse", "wrap", "extend", "adopt_oss", "build", "hold", "rejected")


def build_research_packet(*, task: str, domain: str, decision: str, rationale: str) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of: {', '.join(DECISIONS)}")

    return {
        "packet_type": "engineering_brain_research",
        "version": 1,
        "task": task,
        "repo": "<REPO>",
        "domain": domain,
        "candidates": [_candidate(source) for source in select_technology_sources(domain)],
        "decision": {
            "status": decision,
            "rationale": rationale,
            "rule": "catalog evidence remains candidate until adopted by test, docs, registry, or ADR",
        },
        "human_stoplines": ["adopt", "push", "pr_create", "merge", "visibility_change"],
        "unknowns": [] if rationale else ["decision rationale is not recorded"],
    }


def _candidate(source: Any) -> dict[str, Any]:
    return {
        "id": source.id,
        "domain": source.domain,
        "status": "candidate",
        "catalog_status": source.status,
        "source_refs": list(source.source_refs),
        "use_when": list(source.use_when),
        "adoption_route": source.adoption_route,
        "gate_hint": source.gate_hint,
        "insufficient_if": list(source.insufficient_if),
    }
