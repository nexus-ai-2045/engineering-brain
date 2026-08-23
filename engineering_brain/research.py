from __future__ import annotations

from typing import Any, Sequence

from .registry import select_technology_sources


DECISIONS = ("reuse", "wrap", "extend", "adopt_oss", "build", "hold", "rejected")
PRECEDENT_REQUIRED_DECISIONS = ("wrap", "extend", "adopt_oss", "build")
PRECEDENT_DECISION_CONTRACT = ("adopt", "revise", "reject", "hold")
PRECEDENT_ALLOW_IMPLEMENTATION = ("adopt", "revise")


def build_research_packet(
    *,
    task: str,
    domain: str,
    decision: str,
    rationale: str,
    precedent_outcome: str | None = None,
    precedent_evidence: Sequence[str] | None = None,
) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of: {', '.join(DECISIONS)}")

    evidence = [item for item in (precedent_evidence or ()) if str(item).strip()]
    effective_decision, unknowns = _apply_precedent_gate(
        decision=decision,
        rationale=rationale,
        precedent_outcome=precedent_outcome,
        precedent_evidence=evidence,
    )

    return {
        "packet_type": "engineering_brain_research",
        "version": 2,
        "task": task,
        "repo": "<REPO>",
        "domain": domain,
        "candidates": [_candidate(source) for source in select_technology_sources(domain)],
        "precedent_research": {
            "skill": "implementation-precedent-research",
            "source_owner": "nexus-ai-skills",
            "role": "consumer",
            "required_before": ["wrap", "extend", "adopt_oss", "build"],
            "decision_contract": ["adopt", "revise", "reject", "hold"],
        },
        "decision": {
            "status": effective_decision,
            "rationale": rationale,
            "rule": "catalog evidence remains candidate until adopted by test, docs, registry, or ADR",
        },
        "human_stoplines": ["adopt", "push", "pr_create", "merge", "visibility_change"],
        "unknowns": unknowns,
    }


def _apply_precedent_gate(
    *,
    decision: str,
    rationale: str,
    precedent_outcome: str | None,
    precedent_evidence: Sequence[str],
) -> tuple[str, list[str]]:
    unknowns: list[str] = []
    if not rationale:
        unknowns.append("decision rationale is not recorded")

    if decision not in PRECEDENT_REQUIRED_DECISIONS:
        return decision, unknowns

    if precedent_outcome is None or precedent_outcome == "":
        unknowns.append(
            "precedent research was not run or is unavailable; "
            f"forced hold instead of {decision}"
        )
        return "hold", unknowns

    if precedent_outcome not in PRECEDENT_DECISION_CONTRACT:
        unknowns.append(
            "precedent research outcome is outside decision_contract; "
            f"forced hold instead of {decision}"
        )
        return "hold", unknowns

    if not precedent_evidence:
        unknowns.append(
            "precedent research evidence is missing; "
            f"forced hold instead of {decision}"
        )
        return "hold", unknowns

    if precedent_outcome not in PRECEDENT_ALLOW_IMPLEMENTATION:
        unknowns.append(
            f"precedent research outcome is {precedent_outcome}; "
            f"forced hold instead of {decision}"
        )
        return "hold", unknowns

    return decision, unknowns


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
