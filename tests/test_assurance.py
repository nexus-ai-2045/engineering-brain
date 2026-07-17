from devbrain.assurance import evaluate_async_orchestration, evaluate_structured_model


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
        "artifact_digest": "sha256:abc",
    }
    assert evaluate_structured_model(evidence) == {"status": "pass", "failures": []}
