from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY = PACKAGE_ROOT / "data" / "adoption-units.yaml"
DEFAULT_TECHNOLOGY_SOURCES = PACKAGE_ROOT / "data" / "technology-sources.yaml"
DEFAULT_LOCAL_LEARNINGS = PACKAGE_ROOT / "data" / "local-learnings.yaml"

LEARNING_DECISIONS = frozenset({"candidate", "field_review", "adopted", "hold", "rejected"})
LEARNING_DECISION_ALIASES = {"adopt": "adopted", "reject": "rejected"}
FIELD_REVIEW_STATES = frozenset({"pending", "in_progress", "passed"})
LEARNING_TRANSITIONS: dict[str, frozenset[str]] = {
    "candidate": frozenset({"field_review"}),
    "field_review": frozenset({"adopted", "hold", "rejected"}),
    "hold": frozenset({"field_review"}),
    "adopted": frozenset(),
    "rejected": frozenset(),
}
ADOPTION_TARGETS = frozenset({"docs", "registry", "tests", "skill", "adr", "hold"})


@dataclass(frozen=True)
class AdoptionUnit:
    id: str
    status: str
    source_refs: tuple[str, ...]
    applies_when: tuple[str, ...]
    timing: tuple[str, ...]
    boundary: str
    route: str
    guarantee_tier: str
    checks: tuple[dict[str, Any], ...]
    insufficient_if: tuple[str, ...]


@dataclass(frozen=True)
class TechnologySource:
    id: str
    domain: str
    status: str
    source_refs: tuple[str, ...]
    use_when: tuple[str, ...]
    adoption_route: str
    gate_hint: str
    insufficient_if: tuple[str, ...]


@dataclass(frozen=True)
class LocalLearning:
    id: str
    source_lane: str
    source_pointer: tuple[str, ...]
    observed_problem: str
    proposed_solution: Any
    reusable_rule: str
    evidence: str
    freshness: str
    rights_and_privacy: str
    adoption_target: str
    decision: str
    field_review: str
    review_trigger: str
    assurance_gate: str | None
    decision_reason: str
    adopted_doc: str | None = None


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [part.strip().strip('"') for part in body.split(",")]
    return value


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    """Load the constrained YAML shape used by this repository.

    The registry intentionally uses a small YAML subset so the CLI has no
    runtime dependency on PyYAML.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    data: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    current_section: str | None = None
    current_list_key: str | None = None
    current_check: dict[str, Any] | None = None
    current_folded_key: str | None = None
    folded_parts: list[str] = []

    def flush_folded() -> None:
        nonlocal current_folded_key, folded_parts
        if current is None or current_folded_key is None:
            current_folded_key = None
            folded_parts = []
            return
        current[current_folded_key] = " ".join(part.strip() for part in folded_parts if part.strip())
        current_folded_key = None
        folded_parts = []

    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if indent == 0 and text.startswith("version:"):
            flush_folded()
            data["version"] = int(text.split(":", 1)[1].strip())
            continue
        if indent == 0 and text.startswith("updated_at:"):
            flush_folded()
            data["updated_at"] = _parse_scalar(text.split(":", 1)[1])
            continue
        if indent == 0 and text in {"units:", "sources:", "learnings:"}:
            flush_folded()
            current_section = text[:-1]
            data[current_section] = []
            current = None
            current_list_key = None
            current_check = None
            continue
        if indent == 2 and text.startswith("- id:"):
            if current_section is None:
                raise ValueError("list item found before registry section")
            flush_folded()
            current = {"id": text.split(":", 1)[1].strip()}
            data[current_section].append(current)
            current_list_key = None
            current_check = None
            continue
        if current is None or indent < 4:
            continue
        if current_folded_key is not None and indent >= 6:
            # Keep list-looking lines (e.g. "- reason") inside active > / | scalars.
            folded_parts.append(text)
            continue
        if indent == 4 and ":" in text:
            flush_folded()
            key, raw_value = text.split(":", 1)
            value = raw_value.strip()
            if value in {">", "|"}:
                current_folded_key = key
                folded_parts = []
                current_list_key = None
                current_check = None
            elif value:
                current[key] = _parse_scalar(value)
                current_list_key = None
                current_check = None
            else:
                current[key] = []
                current_list_key = key
                current_check = None
            continue
        if text.startswith("- ") and current_list_key:
            flush_folded()
            item = text[2:].strip()
            if current_list_key == "checks":
                current_check = {}
                current[current_list_key].append(current_check)
                if ":" in item:
                    key, raw_value = item.split(":", 1)
                    current_check[key] = _parse_scalar(raw_value)
            elif isinstance(current[current_list_key], list):
                current[current_list_key].append(_parse_scalar(item))
            continue
        if indent == 8 and current_list_key == "checks" and current_check is not None and ":" in text:
            key, raw_value = text.split(":", 1)
            current_check[key] = _parse_scalar(raw_value)

    flush_folded()
    return data


def adoption_units(path: Path = DEFAULT_REGISTRY) -> list[AdoptionUnit]:
    units = []
    for raw in load_registry(path)["units"]:
        validate_unit(raw)
        units.append(
            AdoptionUnit(
                id=raw["id"],
                status=raw["status"],
                source_refs=tuple(raw["source_refs"]),
                applies_when=tuple(raw["applies_when"]),
                timing=tuple(raw["timing"]),
                boundary=raw["boundary"],
                route=raw["route"],
                guarantee_tier=raw["guarantee_tier"],
                checks=tuple(raw["checks"]),
                insufficient_if=tuple(raw["insufficient_if"]),
            )
        )
    return units


def technology_sources(path: Path = DEFAULT_TECHNOLOGY_SOURCES) -> list[TechnologySource]:
    sources = []
    for raw in load_registry(path)["sources"]:
        validate_technology_source(raw)
        sources.append(
            TechnologySource(
                id=raw["id"],
                domain=raw["domain"],
                status=raw["status"],
                source_refs=tuple(raw["source_refs"]),
                use_when=tuple(raw["use_when"]),
                adoption_route=raw["adoption_route"],
                gate_hint=raw["gate_hint"],
                insufficient_if=tuple(raw["insufficient_if"]),
            )
        )
    return sources


def select_technology_sources(domain: str | None = None) -> list[TechnologySource]:
    sources = technology_sources()
    if domain is None:
        return sources
    normalized = domain.lower()
    return [
        source
        for source in sources
        if source.domain.lower() == normalized or normalized in {item.lower() for item in source.use_when}
    ]


def validate_unit(raw: dict[str, Any]) -> None:
    required = {
        "id",
        "status",
        "source_refs",
        "applies_when",
        "timing",
        "boundary",
        "route",
        "guarantee_tier",
        "checks",
        "insufficient_if",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise ValueError(f"adoption unit {raw.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if raw["status"] not in {"adopted", "candidate", "hold", "rejected"}:
        raise ValueError(f"adoption unit {raw['id']} has invalid status: {raw['status']}")
    for list_key in ("source_refs", "applies_when", "timing", "checks", "insufficient_if"):
        if not raw[list_key]:
            raise ValueError(f"adoption unit {raw['id']} has empty {list_key}")
    if not str(raw["guarantee_tier"]).startswith("G"):
        raise ValueError(f"adoption unit {raw['id']} has invalid guarantee_tier")


def validate_technology_source(raw: dict[str, Any]) -> None:
    required = {
        "id",
        "domain",
        "status",
        "source_refs",
        "use_when",
        "adoption_route",
        "gate_hint",
        "insufficient_if",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise ValueError(f"technology source {raw.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if raw["status"] not in {"adopted", "candidate", "hold", "rejected"}:
        raise ValueError(f"technology source {raw['id']} has invalid status: {raw['status']}")
    for list_key in ("source_refs", "use_when", "insufficient_if"):
        if not raw[list_key]:
            raise ValueError(f"technology source {raw['id']} has empty {list_key}")


def select_units(triggers: list[str], *, include_candidates: bool = False) -> list[AdoptionUnit]:
    normalized = {trigger.lower() for trigger in triggers}
    selected = []
    for unit in adoption_units():
        if unit.status == "candidate" and not include_candidates:
            continue
        if normalized.intersection({item.lower() for item in unit.applies_when}):
            selected.append(unit)
    return selected


def normalize_learning_decision(value: str) -> str:
    normalized = LEARNING_DECISION_ALIASES.get(value, value)
    if normalized not in LEARNING_DECISIONS:
        raise ValueError(f"invalid learning decision: {value}")
    return normalized


def validate_local_learning(raw: dict[str, Any]) -> None:
    required = {
        "id",
        "source_lane",
        "source_pointer",
        "observed_problem",
        "reusable_rule",
        "evidence",
        "freshness",
        "rights_and_privacy",
        "adoption_target",
        "decision",
        "field_review",
        "review_trigger",
        "decision_reason",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise ValueError(f"local learning {raw.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    normalize_learning_decision(str(raw["decision"]))
    if raw["field_review"] not in FIELD_REVIEW_STATES:
        raise ValueError(
            f"local learning {raw['id']} has invalid field_review: {raw['field_review']}"
        )
    if raw["adoption_target"] not in ADOPTION_TARGETS:
        raise ValueError(
            f"local learning {raw['id']} has invalid adoption_target: {raw['adoption_target']}"
        )
    pointers = raw["source_pointer"]
    if not isinstance(pointers, list) or not pointers:
        raise ValueError(f"local learning {raw['id']} requires non-empty source_pointer list")
    if "proposed_solution" not in raw:
        raise ValueError(f"local learning {raw['id']} missing fields: proposed_solution")
    if "assurance_gate" not in raw:
        raise ValueError(f"local learning {raw['id']} missing fields: assurance_gate")


def local_learnings(path: Path = DEFAULT_LOCAL_LEARNINGS) -> list[LocalLearning]:
    payload = load_registry(path)
    if "learnings" not in payload:
        raise ValueError(f"local learnings registry missing learnings section: {path}")
    learnings: list[LocalLearning] = []
    for raw in payload["learnings"]:
        validate_local_learning(raw)
        learnings.append(
            LocalLearning(
                id=raw["id"],
                source_lane=raw["source_lane"],
                source_pointer=tuple(raw["source_pointer"]),
                observed_problem=raw["observed_problem"],
                proposed_solution=raw.get("proposed_solution"),
                reusable_rule=raw["reusable_rule"],
                evidence=raw["evidence"],
                freshness=raw["freshness"],
                rights_and_privacy=raw["rights_and_privacy"],
                adoption_target=raw["adoption_target"],
                decision=normalize_learning_decision(str(raw["decision"])),
                field_review=raw["field_review"],
                review_trigger=raw["review_trigger"],
                assurance_gate=raw.get("assurance_gate"),
                decision_reason=raw["decision_reason"],
                adopted_doc=raw.get("adopted_doc"),
            )
        )
    return learnings


def list_local_learnings(
    path: Path = DEFAULT_LOCAL_LEARNINGS,
    *,
    decision: str | None = None,
    field_review: str | None = None,
) -> list[LocalLearning]:
    selected = local_learnings(path)
    if decision is not None:
        wanted = normalize_learning_decision(decision)
        if wanted == "adopted":
            # Fail-closed: decision string alone is not enough while field_review is pending.
            selected = [item for item in selected if is_operationally_adopted(item)]
        else:
            selected = [item for item in selected if item.decision == wanted]
    if field_review is not None:
        if field_review not in FIELD_REVIEW_STATES:
            raise ValueError(f"invalid field_review filter: {field_review}")
        selected = [item for item in selected if item.field_review == field_review]
    return selected


def serialize_local_learning(learning: LocalLearning) -> dict[str, Any]:
    payload = asdict(learning)
    payload["source_pointer"] = list(learning.source_pointer)
    return payload


def check_learning_assurance(learning: LocalLearning) -> dict[str, Any]:
    """Fail-closed operational guarantee check for a local learning packet.

    field_review=pending must never be reported as adopted / operationally guaranteed.
    """
    failures: list[str] = []
    decision = normalize_learning_decision(learning.decision)
    if learning.field_review == "pending":
        failures.append("field_review is pending; not operationally guaranteed")
    if decision != "adopted":
        failures.append(f"decision is {decision}, not adopted")
    if decision == "adopted" and learning.field_review != "passed":
        failures.append("adopted decision requires field_review=passed")
    return {
        "id": learning.id,
        "decision": decision,
        "field_review": learning.field_review,
        "status": "pass" if not failures else "block",
        "failures": failures,
        "operationally_guaranteed": not failures,
    }


def is_operationally_adopted(learning: LocalLearning) -> bool:
    return check_learning_assurance(learning)["operationally_guaranteed"] is True


def _field_review_for_target(current: LocalLearning, target: str) -> str:
    if target == "field_review":
        return "in_progress"
    if target == "adopted":
        if current.decision == "field_review" and current.field_review != "pending":
            return "passed"
        return current.field_review
    if target in {"hold", "rejected"} and current.decision == "field_review":
        return "passed"
    return current.field_review


def plan_learning_transition(
    learning: LocalLearning,
    *,
    target_decision: str,
    current_turn_approval: bool = False,
) -> dict[str, Any]:
    """Plan a decision ladder transition.

    Ladder: candidate -> field_review -> adopted|hold|rejected.
    Adopt remains plan/evidence only unless current-turn approval is present.
    This API never mutates ``engineering_brain/data/local-learnings.yaml``.
    """
    current = normalize_learning_decision(learning.decision)
    target = normalize_learning_decision(target_decision)
    allowed = LEARNING_TRANSITIONS.get(current, frozenset())
    errors: list[str] = []
    approval_missing = False

    if target not in allowed:
        errors.append(f"invalid transition: {current} -> {target}")
    if target == "adopted" and current != "field_review":
        errors.append("adopt requires decision=field_review first")
    if target == "adopted" and learning.field_review == "pending":
        errors.append("cannot adopt while field_review is pending")
    if target == "adopted" and not current_turn_approval:
        approval_missing = True
        errors.append("adopt requires current-turn approval; returning plan-only")

    planned_field_review = _field_review_for_target(learning, target)
    planned = replace(
        learning,
        decision=target,
        field_review=planned_field_review,
    )
    assurance = check_learning_assurance(planned) if target == "adopted" else None
    if (
        target == "adopted"
        and assurance is not None
        and assurance["status"] != "pass"
        and "cannot adopt while field_review is pending" not in errors
    ):
        errors.extend(f"adopt assurance blocked: {item}" for item in assurance["failures"])

    hard_errors = [
        error
        for error in errors
        if error != "adopt requires current-turn approval; returning plan-only"
    ]
    if hard_errors:
        status = "error"
        plan_only = True
    elif approval_missing:
        status = "plan_only"
        plan_only = True
    else:
        status = "ok"
        # Non-adopt transitions validate only; adopt with approval marks readiness
        # without writing SSOT (human/PR persists).
        plan_only = target != "adopted"

    return {
        "id": learning.id,
        "status": status,
        "plan_only": plan_only,
        "current_turn_approval": current_turn_approval,
        "from_decision": current,
        "to_decision": target,
        "from_field_review": learning.field_review,
        "to_field_review": planned_field_review,
        "adoption_target": learning.adoption_target,
        "assurance_gate": learning.assurance_gate,
        "review_trigger": learning.review_trigger,
        "errors": errors,
        "planned": serialize_local_learning(planned),
        "assurance": assurance,
        "ssot_mutated": False,
        "human_stopline": (
            "adopt is plan/evidence only unless current-turn approval exists; "
            "SSOT is not mutated by this call"
        ),
    }


def start_field_review(learning: LocalLearning) -> dict[str, Any]:
    return plan_learning_transition(learning, target_decision="field_review")


def plan_adopt_learning(
    learning: LocalLearning,
    *,
    current_turn_approval: bool = False,
) -> dict[str, Any]:
    return plan_learning_transition(
        learning,
        target_decision="adopted",
        current_turn_approval=current_turn_approval,
    )


def get_local_learning(learning_id: str, path: Path = DEFAULT_LOCAL_LEARNINGS) -> LocalLearning:
    for learning in local_learnings(path):
        if learning.id == learning_id:
            return learning
    raise ValueError(f"local learning not found: {learning_id}")
