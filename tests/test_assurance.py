import pytest

from engineering_brain.assurance import evaluate_async_orchestration, evaluate_structured_model


def test_async_assurance_blocks_active_but_never_executed_workflow() -> None:
    result = evaluate_async_orchestration({"workflow_active": True, "execution_count": 0})
    assert result["status"] == "block"
    assert "execution_count" in result["failures"]


def test_async_assurance_requires_full_non_tautological_evidence() -> None:
    evidence = {
        "execution_count": 1, "marker_schema_version": 2, "active_jobs_after_cancel": 0,
        "control_endpoint_private": True, "iam_least_privilege": True,
        "job_terminal": True, "marker_bound_to_run": True, "target_schema_valid": True,
        "gt_metrics_recorded": True, "budget_reserved_before_dispatch": True,
        "compensation_terminal": True,
    }
    assert evaluate_async_orchestration(evidence) == {"status": "pass", "failures": []}


def test_async_assurance_requires_observed_post_cancel_job_count() -> None:
    evidence = {
        "execution_count": 1,
        "marker_schema_version": 2,
        **{key: True for key in (
            "control_endpoint_private", "iam_least_privilege", "job_terminal",
            "marker_bound_to_run", "target_schema_valid", "gt_metrics_recorded",
            "budget_reserved_before_dispatch", "compensation_terminal",
        )},
    }

    result = evaluate_async_orchestration(evidence)

    assert result["status"] == "block"
    assert "active_jobs_after_cancel" in result["failures"]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("execution_count", True),
        ("execution_count", "1"),
        ("marker_schema_version", None),
        ("marker_schema_version", "2"),
        ("active_jobs_after_cancel", False),
    ],
)
def test_async_assurance_rejects_malformed_numeric_evidence_without_crashing(
    key: str,
    value: object,
) -> None:
    evidence = {
        "execution_count": 1,
        "marker_schema_version": 2,
        "active_jobs_after_cancel": 0,
        **{required: True for required in (
            "control_endpoint_private", "iam_least_privilege", "job_terminal",
            "marker_bound_to_run", "target_schema_valid", "gt_metrics_recorded",
            "budget_reserved_before_dispatch", "compensation_terminal",
        )},
    }
    evidence[key] = value

    result = evaluate_async_orchestration(evidence)

    assert result["status"] == "block"
    assert key in result["failures"]


def test_model_assurance_rejects_json_only_false_green() -> None:
    result = evaluate_structured_model({"syntax_measured": True, "syntax_valid_rate": 1.0})
    assert result["status"] == "block"
    assert "schema_valid_rate" in result["failures"]


def test_model_assurance_requires_artifact_specific_independent_evaluation() -> None:
    evidence = {
        "syntax_measured": True, "schema_measured": True, "field_semantics_measured": True,
        "critical_fields_measured": True, "independent_gt": True,
        "calibration_measured": True, "worst_slice_measured": True,
        "artifact_digest_fixed": True, "syntax_valid_rate": 1.0, "schema_valid_rate": 1.0,
        "field_semantics_score": 0.94, "field_semantics_min": 0.90,
        "critical_fields_score": 0.99, "critical_fields_min": 0.98,
        "calibration_error": 0.04, "calibration_error_max": 0.05,
        "worst_slice_score": 0.88, "worst_slice_min": 0.85,
        "artifact_digest": "sha256:abc",
    }
    assert evaluate_structured_model(evidence) == {"status": "pass", "failures": []}


def test_model_assurance_blocks_measured_metrics_below_explicit_thresholds() -> None:
    evidence = {
        "syntax_measured": True, "schema_measured": True, "field_semantics_measured": True,
        "critical_fields_measured": True, "independent_gt": True,
        "calibration_measured": True, "worst_slice_measured": True,
        "artifact_digest_fixed": True, "syntax_valid_rate": 1.0, "schema_valid_rate": 1.0,
        "field_semantics_score": 0.79, "field_semantics_min": 0.90,
        "critical_fields_score": 0.95, "critical_fields_min": 0.98,
        "calibration_error": 0.08, "calibration_error_max": 0.05,
        "worst_slice_score": 0.70, "worst_slice_min": 0.85,
        "artifact_digest": "sha256:abc",
    }

    result = evaluate_structured_model(evidence)

    assert result["status"] == "block"
    for metric in (
        "field_semantics_score",
        "critical_fields_score",
        "calibration_error",
        "worst_slice_score",
    ):
        assert metric in result["failures"]
