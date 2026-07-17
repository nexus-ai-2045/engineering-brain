from __future__ import annotations

from typing import Any


ASYNC_REQUIRED_TRUE = (
    "control_endpoint_private",
    "iam_least_privilege",
    "job_terminal",
    "marker_bound_to_run",
    "target_schema_valid",
    "gt_metrics_recorded",
    "budget_reserved_before_dispatch",
    "compensation_terminal",
)

MODEL_REQUIRED_TRUE = (
    "syntax_measured",
    "schema_measured",
    "field_semantics_measured",
    "critical_fields_measured",
    "independent_gt",
    "calibration_measured",
    "worst_slice_measured",
    "artifact_digest_fixed",
)


def evaluate_async_orchestration(evidence: dict[str, Any]) -> dict[str, Any]:
    failures = [key for key in ASYNC_REQUIRED_TRUE if evidence.get(key) is not True]
    if not isinstance(evidence.get("execution_count"), int) or evidence.get("execution_count", 0) < 1:
        failures.append("execution_count")
    if evidence.get("marker_schema_version", 0) < 2:
        failures.append("marker_schema_version")
    if evidence.get("active_jobs_after_cancel", 0) != 0:
        failures.append("active_jobs_after_cancel")
    return {"status": "pass" if not failures else "block", "failures": sorted(set(failures))}


def evaluate_structured_model(evidence: dict[str, Any]) -> dict[str, Any]:
    failures = [key for key in MODEL_REQUIRED_TRUE if evidence.get(key) is not True]
    if evidence.get("syntax_valid_rate") != 1.0:
        failures.append("syntax_valid_rate")
    if evidence.get("schema_valid_rate") != 1.0:
        failures.append("schema_valid_rate")
    if not evidence.get("artifact_digest"):
        failures.append("artifact_digest")
    return {"status": "pass" if not failures else "block", "failures": sorted(set(failures))}
