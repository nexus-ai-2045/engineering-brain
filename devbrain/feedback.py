from __future__ import annotations

import json
import re
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .path_safety import PERSONAL_PATH_PATTERN


SCHEMA = json.loads(
    files("devbrain").joinpath("fde-feedback-packet.schema.json").read_text(encoding="utf-8")
)
SECRET_LIKE_PATTERN = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._-]{20,})"
)
SURROGATE_ESCAPE_PATTERN = re.compile(r"\\u[dD][89aAbB][0-9a-fA-F]{2}")


def validate_feedback_packet(packet: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    errors = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: invalid {error.validator}"
        for error in sorted(
            validator.iter_errors(packet), key=lambda item: list(item.absolute_path)
        )
    ]
    act = packet.get("act")
    serialized = json.dumps(packet, ensure_ascii=True)
    if PERSONAL_PATH_PATTERN.search(serialized):
        errors.append("<root>: personal path is not allowed")
    if SECRET_LIKE_PATTERN.search(serialized):
        errors.append("<root>: secret-like content is not allowed")
    if SURROGATE_ESCAPE_PATTERN.search(serialized):
        errors.append("<root>: invalid Unicode surrogate")
    observed_at = packet.get("observed_at")
    if isinstance(observed_at, str):
        try:
            datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("observed_at: invalid date-time")
    check = packet.get("check")
    boundaries = packet.get("boundaries")
    if (
        isinstance(act, dict)
        and act.get("decision") == "adopt"
        and isinstance(check, dict)
        and check.get("human_review") == "rejected"
    ):
        errors.append("act/decision: adopt conflicts with rejected human review")
    elif (
        isinstance(act, dict)
        and act.get("decision") == "adopt"
        and isinstance(boundaries, dict)
        and boundaries.get("human_gate_required") is True
        and (
            not isinstance(check, dict)
            or check.get("human_review") != "approved"
        )
    ):
        errors.append("act/decision: adopt requires approved human review")
    return errors


def build_next_plan_context(packet: dict[str, Any]) -> dict[str, Any]:
    errors = validate_feedback_packet(packet)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "schema_version": "engineering-brain.next-plan.v1",
        "source_feedback_id": packet["feedback_id"],
        "source_run_id": packet["source_run_id"],
        "decision": packet["act"]["decision"],
        "next_plan_input": packet["act"]["next_plan_input"],
        "evidence_refs": packet["check"]["evidence"],
        "human_gate_required": packet["boundaries"]["human_gate_required"],
    }


def load_feedback_packet(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("feedback packet must be a JSON object")
    return payload
