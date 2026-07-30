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

MODEL_MINIMUM_METRICS = (
    ("field_semantics_score", "field_semantics_min", "minimum"),
    ("critical_fields_score", "critical_fields_min", "minimum"),
    ("calibration_error", "calibration_error_max", "maximum"),
    ("worst_slice_score", "worst_slice_min", "minimum"),
)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def evaluate_async_orchestration(evidence: dict[str, Any]) -> dict[str, Any]:
    failures = [key for key in ASYNC_REQUIRED_TRUE if evidence.get(key) is not True]
    execution_count = evidence.get("execution_count")
    if not _is_integer(execution_count) or execution_count < 1:
        failures.append("execution_count")
    marker_schema_version = evidence.get("marker_schema_version")
    if not _is_integer(marker_schema_version) or marker_schema_version < 2:
        failures.append("marker_schema_version")
    active_jobs_after_cancel = evidence.get("active_jobs_after_cancel")
    if not _is_integer(active_jobs_after_cancel) or active_jobs_after_cancel != 0:
        failures.append("active_jobs_after_cancel")
    return {"status": "pass" if not failures else "block", "failures": sorted(set(failures))}


def evaluate_structured_model(evidence: dict[str, Any]) -> dict[str, Any]:
    failures = [key for key in MODEL_REQUIRED_TRUE if evidence.get(key) is not True]
    if evidence.get("syntax_valid_rate") != 1.0:
        failures.append("syntax_valid_rate")
    if evidence.get("schema_valid_rate") != 1.0:
        failures.append("schema_valid_rate")
    for value_key, threshold_key, direction in MODEL_MINIMUM_METRICS:
        value = evidence.get(value_key)
        threshold = evidence.get(threshold_key)
        if not _is_number(value) or not _is_number(threshold):
            failures.extend([value_key, threshold_key])
        elif direction == "minimum" and value < threshold:
            failures.append(value_key)
        elif direction == "maximum" and value > threshold:
            failures.append(value_key)
    if not evidence.get("artifact_digest"):
        failures.append("artifact_digest")
    return {"status": "pass" if not failures else "block", "failures": sorted(set(failures))}
