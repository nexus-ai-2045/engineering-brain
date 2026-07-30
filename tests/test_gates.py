from pathlib import Path

import pytest

from engineering_brain.gates import evaluate_triggers, route_task


def test_route_task_blocks_public_release_actions() -> None:
    result = route_task("implement bug fix and prepare github PR")
    assert "tdd_regression_gate" in result["selected_units"]
    assert "human_publication_review_gate" in result["selected_units"]
    assert "push" in result["blocked_actions"]
    assert "pr" in result["blocked_actions"]


def test_gate_security_is_operational() -> None:
    result = evaluate_triggers(["security"])
    assert result["overall"] == "ok"
    assert result["units"][0]["id"] == "agent_containment_gate"
    assert result["units"][0]["guarantee_tier"] == "G4 operational"


def test_gate_publish_is_blocked() -> None:
    result = evaluate_triggers(["publish"])
    assert result["overall"] == "blocked"
    assert result["units"][0]["id"] == "human_publication_review_gate"


def test_gate_public_path_redaction_is_operational() -> None:
    result = evaluate_triggers(["public_path"])
    assert result["overall"] == "ok"
    assert result["units"][0]["id"] == "public_path_redaction_gate"
    assert result["units"][0]["guarantee_tier"] == "G4 operational"


def test_route_task_selects_public_path_gate() -> None:
    result = route_task("公開前に absolute path redaction を確認")
    assert "public_path_redaction_gate" in result["selected_units"]


def test_route_task_selects_public_path_gate_from_japanese_phrase() -> None:
    result = route_task("絶対パスを公開候補に残さない")
    assert "public_path_redaction_gate" in result["selected_units"]


def test_route_task_always_surfaces_reinvention_candidate_gate() -> None:
    result = route_task("軽いドキュメント修正")

    assert "reinvention_candidate_research_gate" in result["selected_units"]
    assert "reinvention_check" in result["inferred_triggers"]


def test_candidate_gate_is_advisory_not_blocking() -> None:
    result = evaluate_triggers(["reinvention_check"])

    assert result["overall"] == "ok"
    assert result["units"][0]["id"] == "reinvention_candidate_research_gate"
    assert result["units"][0]["status"] == "candidate"


def test_route_task_selects_async_orchestration_assurance() -> None:
    result = route_task("Google Cloud WorkflowsでVertex AIを非同期実行する")
    assert "async_orchestration_evidence_gate" in result["selected_units"]


def test_route_task_selects_structured_model_evaluation() -> None:
    result = route_task("OCR蒸留モデルの構造化出力と量子化を評価する")
    assert "structured_model_evaluation_gate" in result["selected_units"]


def test_assurance_gate_blocks_without_run_evidence() -> None:
    result = evaluate_triggers(["orchestration"])

    assert result["overall"] == "blocked"
    assert result["assurance"]["async_orchestration"]["status"] == "block"


def test_assurance_gate_evaluates_supplied_run_evidence() -> None:
    evidence = {
        "async_orchestration": {
            "execution_count": 1,
            "marker_schema_version": 2,
            "active_jobs_after_cancel": 0,
            **{key: True for key in (
                "control_endpoint_private", "iam_least_privilege", "job_terminal",
                "marker_bound_to_run", "target_schema_valid", "gt_metrics_recorded",
                "budget_reserved_before_dispatch", "compensation_terminal",
            )},
        }
    }

    result = evaluate_triggers(["orchestration"], evidence)

    assert result["overall"] == "ok"
    assert result["assurance"]["async_orchestration"] == {"status": "pass", "failures": []}


@pytest.mark.parametrize("task", ["Implement a Swift parser", "democracy review"])
def test_route_task_does_not_match_short_alias_inside_unrelated_word(task: str) -> None:
    result = route_task(task)

    assert "async_orchestration_evidence_gate" not in result["selected_units"]
    assert "structured_model_evaluation_gate" not in result["selected_units"]


@pytest.mark.parametrize("task", [
    "GCE GPUで学習", "TerraformでVertexを構築", "帳票OCRモデル評価", "蒸留モデル",
    "ワークフローを起動", "Cloud BuildでCustom Jobを作る", "WIFでCloud Runへ接続",
])
def test_route_task_covers_cloud_and_model_aliases(task: str) -> None:
    result = route_task(task)
    assert {"async_orchestration_evidence_gate", "structured_model_evaluation_gate"}.intersection(
        result["selected_units"]
    )
