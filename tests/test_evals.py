import copy
import json
from pathlib import Path

import pytest

from engineering_brain.cli import main
from engineering_brain.evals import (
    build_blind_review_bundle,
    build_eval_plan,
    build_eval_smoke_packet,
    build_run_manifest,
    load_eval_suite,
    score_eval_results,
    validate_result_import,
)


ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "engineering_brain" / "data" / "eval-suites" / "research-review-v1.json"
SUITE_V2_PATH = ROOT / "engineering_brain" / "data" / "eval-suites" / "research-review-v2.json"
GROUND_TRUTH_V2_PATH = (
    ROOT / "engineering_brain" / "data" / "eval-suites" / "research-review-v2-ground-truth.json"
)


def test_eval_plan_defines_fair_baseline_and_human_stoplines() -> None:
    suite = load_eval_suite(SUITE_PATH)

    plan = build_eval_plan(suite)

    assert plan["packet_type"] == "engineering_brain_eval_plan"
    assert plan["baseline_arm"] == "sol_direct"
    assert {arm["id"] for arm in plan["arms"]} == {
        "sol_direct",
        "sol_prompt",
        "sol_runtime",
        "terra_runtime",
    }
    assert plan["case_counts"]["held_out"] >= 1
    assert plan["execution"]["status"] == "plan_only"
    assert "api_call" in plan["human_stoplines"]
    assert "paid_run" in plan["human_stoplines"]


def test_run_manifest_freezes_held_out_matrix_without_executing_models() -> None:
    suite = load_eval_suite(SUITE_PATH)

    manifest = build_run_manifest(suite, run_id="rr-20260730-seed")

    held_out_count = sum(case["split"] == "held_out" for case in suite["cases"])
    assert manifest["packet_type"] == "engineering_brain_eval_run_manifest"
    assert manifest["run_id"] == "rr-20260730-seed"
    assert len(manifest["suite_sha256"]) == 64
    assert len(manifest["items"]) == held_out_count * len(suite["arms"])
    assert len({item["item_id"] for item in manifest["items"]}) == len(manifest["items"])
    assert {item["split"] for item in manifest["items"]} == {"held_out"}
    assert manifest["execution"]["status"] == "awaiting_approved_runner"
    assert manifest["execution"]["api_calls_performed"] is False
    assert set(manifest["output_contract"]["required_metrics"]) == {
        "task_success",
        "citation_support",
        "human_win",
        "critical_misses",
        "boundary_violations",
        "latency_ms",
        "cost_usd",
    }


def test_run_manifest_rejects_unsafe_run_id() -> None:
    suite = load_eval_suite(SUITE_PATH)

    with pytest.raises(ValueError, match="run_id"):
        build_run_manifest(suite, run_id="../escape")


def test_eval_smoke_exercises_pipeline_without_performance_claim() -> None:
    suite = load_eval_suite(SUITE_PATH)

    packet = build_eval_smoke_packet(suite, run_id="rr-smoke-local")

    assert packet["packet_type"] == "engineering_brain_eval_smoke"
    assert packet["status"] == "pass"
    assert packet["synthetic_only"] is True
    assert packet["performance_measured"] is False
    assert packet["api_calls_performed"] is False
    assert packet["external_actions_performed"] is False
    assert packet["checks"] == {
        "manifest_complete": "pass",
        "blind_review_complete": "pass",
        "manifest_bound_import": "pass",
        "scoring_complete": "pass",
    }
    assert packet["counts"]["manifest_items"] == 12
    assert packet["counts"]["blind_pairs"] == 9
    assert packet["synthetic_score"]["decision"] == "hold"
    assert "not evidence of model quality" in packet["limitations"]


def test_result_import_rejects_manifest_digest_mismatch() -> None:
    suite = load_eval_suite(SUITE_PATH)
    manifest = build_run_manifest(suite, run_id="rr-20260730-seed")
    manifest["suite_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="suite digest"):
        validate_result_import(suite, manifest, [])


def test_blind_review_bundle_separates_packet_from_answer_key() -> None:
    suite = load_eval_suite(SUITE_PATH)
    manifest = build_run_manifest(suite, run_id="rr-20260730-seed")
    outputs = _outputs(suite, manifest, run_id="rr-20260730-seed")

    bundle = build_blind_review_bundle(suite, outputs, run_id="rr-20260730-seed")

    packet = bundle["review_packet"]
    answer_key = bundle["answer_key"]
    held_out_count = sum(case["split"] == "held_out" for case in suite["cases"])
    assert len(packet["pairs"]) == held_out_count * (len(suite["arms"]) - 1)
    assert "sol_direct" not in json.dumps(packet)
    assert "sol_runtime" not in json.dumps(packet)
    assert set(answer_key["pairs"]) == {pair["pair_id"] for pair in packet["pairs"]}
    assert packet["instructions"]["reviewer_sees_answer_key"] is False


def test_blind_review_bundle_requires_complete_outputs() -> None:
    suite = load_eval_suite(SUITE_PATH)
    manifest = build_run_manifest(suite, run_id="rr-20260730-seed")
    outputs = _outputs(suite, manifest, run_id="rr-20260730-seed")
    outputs.pop()

    with pytest.raises(ValueError, match="missing output rows"):
        build_blind_review_bundle(suite, outputs, run_id="rr-20260730-seed")


def test_load_eval_suite_rejects_missing_required_arm(tmp_path: Path) -> None:
    payload = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    payload["arms"] = [arm for arm in payload["arms"] if arm["id"] != "sol_direct"]
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="required arms"):
        load_eval_suite(broken)


def test_load_eval_suite_rejects_missing_threshold(tmp_path: Path) -> None:
    payload = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    del payload["thresholds"]["task_success_gain_min"]
    broken = tmp_path / "broken-threshold.json"
    broken.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="thresholds"):
        load_eval_suite(broken)


def test_score_eval_results_requires_complete_held_out_matrix() -> None:
    suite = load_eval_suite(SUITE_PATH)
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    results = [
        _result(case["id"], arm["id"], task_success=0.8)
        for case in held_out
        for arm in suite["arms"]
    ]
    results.pop()

    with pytest.raises(ValueError, match="missing result rows"):
        score_eval_results(suite, results)


def test_score_eval_results_compares_runtime_against_sol_direct() -> None:
    suite = load_eval_suite(SUITE_PATH)
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    scores = {
        "sol_direct": 0.70,
        "sol_prompt": 0.76,
        "sol_runtime": 0.85,
        "terra_runtime": 0.82,
    }
    results = [
        _result(
            case["id"],
            arm["id"],
            task_success=scores[arm["id"]],
            citation_support=0.98 if "runtime" in arm["id"] else 0.85,
            human_win=0.70 if arm["id"] == "sol_runtime" else 0.50,
            cost_usd=1.50 if arm["id"] == "sol_runtime" else 1.00,
        )
        for case in held_out
        for arm in suite["arms"]
    ]

    report = score_eval_results(suite, results)

    sol_runtime = report["comparisons"]["sol_runtime"]
    assert sol_runtime["task_success_gain"] == pytest.approx(0.15)
    assert sol_runtime["quality_gate"] == "pass"
    assert sol_runtime["overall"] == "pass"
    assert report["decision"] == "candidate_for_human_review"
    assert report["external_actions_performed"] is False


def test_score_eval_results_rejects_non_finite_scores() -> None:
    suite = load_eval_suite(SUITE_PATH)
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    results = [
        _result(case["id"], arm["id"], task_success=0.8)
        for case in held_out
        for arm in suite["arms"]
    ]
    results[0]["task_success"] = float("nan")

    with pytest.raises(ValueError, match="finite"):
        score_eval_results(suite, results)


def test_score_eval_results_sums_safety_events_instead_of_averaging_them() -> None:
    suite = load_eval_suite(SUITE_PATH)
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    results = [
        _result(case["id"], arm["id"], task_success=0.8)
        for case in held_out
        for arm in suite["arms"]
    ]
    unsafe = next(row for row in results if row["arm_id"] == "sol_runtime")
    unsafe["critical_misses"] = 1

    report = score_eval_results(suite, results)

    assert report["summaries"]["sol_runtime"]["critical_misses"] == pytest.approx(1 / 3)
    assert report["summaries"]["sol_runtime"]["critical_misses_total"] == 1
    assert report["comparisons"]["sol_runtime"]["safety_gate"] == "fail"


def test_score_eval_results_reports_latency_distribution() -> None:
    suite = load_eval_suite(SUITE_PATH)
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    results = [
        _result(case["id"], arm["id"], task_success=0.8)
        for case in held_out
        for arm in suite["arms"]
    ]
    latencies = [100, 200, 900]
    runtime_rows = [row for row in results if row["arm_id"] == "sol_runtime"]
    for row, latency in zip(runtime_rows, latencies, strict=True):
        row["latency_ms"] = latency

    report = score_eval_results(suite, results)

    summary = report["summaries"]["sol_runtime"]
    assert summary["latency_ms_p50"] == 200
    assert summary["latency_ms_p95"] == pytest.approx(830)


def test_cli_eval_plan_emits_json(capfd: pytest.CaptureFixture[str]) -> None:
    code = main(["eval-plan", "--suite", str(SUITE_PATH), "--json"])

    assert code == 0
    packet = json.loads(capfd.readouterr().out)
    assert packet["baseline_arm"] == "sol_direct"
    assert packet["execution"]["status"] == "plan_only"


def test_cli_eval_manifest_emits_frozen_run(capfd: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "eval-manifest",
            "--suite",
            str(SUITE_PATH),
            "--run-id",
            "rr-20260730-seed",
            "--json",
        ]
    )

    assert code == 0
    packet = json.loads(capfd.readouterr().out)
    assert packet["run_id"] == "rr-20260730-seed"
    assert packet["execution"]["status"] == "awaiting_approved_runner"


def test_cli_eval_smoke_runs_synthetic_pipeline(capfd: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "eval-smoke",
            "--suite",
            str(SUITE_PATH),
            "--run-id",
            "rr-smoke-local",
            "--json",
        ]
    )

    assert code == 0
    packet = json.loads(capfd.readouterr().out)
    assert packet["status"] == "pass"
    assert packet["synthetic_only"] is True
    assert packet["performance_measured"] is False


def test_cli_eval_blind_emits_separated_bundle(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    suite = load_eval_suite(SUITE_PATH)
    manifest = build_run_manifest(suite, run_id="rr-20260730-seed")
    outputs = _outputs(suite, manifest, run_id="rr-20260730-seed")
    outputs_path = tmp_path / "outputs.json"
    outputs_path.write_text(json.dumps(outputs), encoding="utf-8")

    code = main(
        [
            "eval-blind",
            "--suite",
            str(SUITE_PATH),
            "--outputs",
            str(outputs_path),
            "--run-id",
            "rr-20260730-seed",
            "--json",
        ]
    )

    assert code == 0
    bundle = json.loads(capfd.readouterr().out)
    assert bundle["review_packet"]["instructions"]["reviewer_sees_answer_key"] is False
    assert bundle["answer_key"]["pairs"]


def test_eval_suite_schema_requires_comparison_contract() -> None:
    schema = json.loads((ROOT / "schemas" / "eval-suite.schema.json").read_text(encoding="utf-8"))

    for field in ["baseline_arm", "arms", "thresholds", "metrics", "cases"]:
        assert field in schema["required"]


def test_v2_suite_is_schema_valid_and_contains_no_ground_truth() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    suite_payload = json.loads(SUITE_V2_PATH.read_text(encoding="utf-8"))
    suite_schema = json.loads(
        (ROOT / "schemas" / "eval-suite-v2.schema.json").read_text(encoding="utf-8")
    )

    jsonschema.Draft202012Validator(suite_schema).validate(suite_payload)
    assert {case["id"] for case in suite_payload["cases"]} == {
        "triage-worker-concurrency-drop",
        "triage-single-zone-errors",
        "dependency-retry-library",
        "dependency-build-narrow-parser",
        "performance-n-plus-one",
        "performance-top-k-stream",
        "refactor-extract-policy-seam",
        "refactor-defer-retiring-module",
    }
    assert "expected_decision" not in json.dumps(suite_payload)
    assert not GROUND_TRUTH_V2_PATH.exists()


def test_safety_event_counts_reject_fractional_values() -> None:
    suite = load_eval_suite(SUITE_PATH)
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    results = [
        _result(case["id"], arm["id"], task_success=0.8)
        for case in held_out
        for arm in suite["arms"]
    ]
    results[0]["critical_misses"] = 0.5

    with pytest.raises(ValueError, match="non-negative integer"):
        score_eval_results(suite, results)


def test_v2_suite_loads_into_existing_runner_without_ground_truth_leakage() -> None:
    suite = load_eval_suite(SUITE_V2_PATH)

    manifest = build_run_manifest(suite, run_id="rr-v2-local")

    assert suite["id"] == "research-review-v2"
    assert {item["case_id"] for item in manifest["items"]} == {
        "performance-top-k-stream",
        "refactor-defer-retiring-module",
    }
    assert "expected_decision" not in json.dumps(manifest)
    assert all(item["evidence_bundle"] for item in manifest["items"])
    assert manifest["random_seed"] == 20260730


def test_result_import_rejects_tampered_manifest_items() -> None:
    suite = load_eval_suite(SUITE_PATH)
    manifest = build_run_manifest(suite, run_id="rr-20260730-seed")
    results = _bound_results(manifest)
    manifest["items"][0]["prompt"] = "tampered prompt"

    with pytest.raises(ValueError, match="manifest item"):
        validate_result_import(suite, manifest, results)


def test_blind_review_rejects_outputs_from_another_run() -> None:
    suite = load_eval_suite(SUITE_PATH)
    manifest = build_run_manifest(suite, run_id="rr-20260730-seed")
    outputs = _outputs(suite, manifest, run_id="rr-old-run")

    with pytest.raises(ValueError, match="run_id"):
        build_blind_review_bundle(suite, outputs, run_id="rr-20260730-seed")


def test_run_manifest_preserves_arm_and_case_execution_controls(tmp_path: Path) -> None:
    payload = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    payload["random_seed"] = 20260730
    payload["arms"][2]["model_revision"] = "sol-2026-07-30"
    payload["arms"][2]["parameters"] = {"temperature": 0}
    held_out = next(case for case in payload["cases"] if case["split"] == "held_out")
    held_out["allowed_tools"] = ["read_file"]
    held_out["time_limit_seconds"] = 30
    suite_path = tmp_path / "suite-with-execution.json"
    suite_path.write_text(json.dumps(payload), encoding="utf-8")

    suite = load_eval_suite(suite_path)
    manifest = build_run_manifest(suite, run_id="rr-exec-local")

    assert manifest["random_seed"] == 20260730
    runtime_item = next(
        item
        for item in manifest["items"]
        if item["case_id"] == held_out["id"] and item["arm_id"] == "sol_runtime"
    )
    assert runtime_item["model_revision"] == "sol-2026-07-30"
    assert runtime_item["parameters"] == {"temperature": 0}
    assert runtime_item["allowed_tools"] == ["read_file"]
    assert runtime_item["time_limit_seconds"] == 30


def test_blind_review_pairs_include_case_evidence() -> None:
    suite = load_eval_suite(SUITE_V2_PATH)
    manifest = build_run_manifest(suite, run_id="rr-v2-local")
    outputs = _outputs(suite, manifest, run_id="rr-v2-local")

    bundle = build_blind_review_bundle(suite, outputs, run_id="rr-v2-local")

    for pair in bundle["review_packet"]["pairs"]:
        assert pair["evidence_bundle"]
        assert pair["response_contract"]["required_sections"]
        assert pair["response_contract"]["prohibited_actions"]


def test_load_eval_suite_rejects_missing_domain(tmp_path: Path) -> None:
    payload = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    held_out = next(case for case in payload["cases"] if case["split"] == "held_out")
    del held_out["domain"]
    broken = tmp_path / "missing-domain.json"
    broken.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="domain"):
        load_eval_suite(broken)


def test_score_eval_results_uses_workflow_not_arm_id_substring() -> None:
    suite = copy.deepcopy(load_eval_suite(SUITE_PATH))
    suite["arms"].append(
        {
            "id": "runtime_disabled",
            "model": "gpt-5.6-sol",
            "workflow": "direct",
            "tool_profile": "matched",
        }
    )
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    results = []
    for case in held_out:
        for arm in suite["arms"]:
            passing = arm["id"] == "runtime_disabled"
            results.append(
                _result(
                    case["id"],
                    arm["id"],
                    task_success=0.90 if passing else 0.70,
                    citation_support=0.98 if passing else 0.85,
                    human_win=0.70 if passing else 0.50,
                    cost_usd=1.00,
                )
            )

    report = score_eval_results(suite, results)

    assert report["comparisons"]["runtime_disabled"]["overall"] == "pass"
    assert report["comparisons"]["sol_runtime"]["overall"] == "fail"
    assert report["decision"] == "hold"


def test_score_eval_results_emits_json_safe_undefined_ratio() -> None:
    suite = load_eval_suite(SUITE_PATH)
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    results = [
        _result(
            case["id"],
            arm["id"],
            task_success=0.85 if "runtime" in arm["id"] else 0.70,
            cost_usd=1.50 if arm["id"] == "sol_runtime" else 0.0,
        )
        for case in held_out
        for arm in suite["arms"]
    ]

    report = score_eval_results(suite, results)
    payload = json.dumps(report)

    assert "Infinity" not in payload
    parsed = json.loads(payload)
    assert parsed["comparisons"]["sol_runtime"]["cost_ratio"] is None
    assert parsed["comparisons"]["sol_runtime"]["efficiency_gate"] == "fail"


def test_score_eval_results_accepts_decimal_gain_at_threshold() -> None:
    suite = load_eval_suite(SUITE_PATH)
    held_out = [case for case in suite["cases"] if case["split"] == "held_out"]
    results = [
        _result(
            case["id"],
            arm["id"],
            task_success=0.6 if arm["id"] == "sol_direct" else 0.7 if arm["id"] == "sol_runtime" else 0.5,
            citation_support=0.98 if arm["id"] == "sol_runtime" else 0.95,
            human_win=0.70 if arm["id"] == "sol_runtime" else 0.60,
        )
        for case in held_out
        for arm in suite["arms"]
    ]

    report = score_eval_results(suite, results)

    assert report["comparisons"]["sol_runtime"]["task_success_gain"] == pytest.approx(0.1)
    assert report["comparisons"]["sol_runtime"]["quality_gate"] == "pass"


def test_review_result_schema_rejects_score_above_max_score() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "schemas" / "eval-review-result.schema.json").read_text(encoding="utf-8"))
    payload = {
        "schema_version": "eval-review-result-v1",
        "review_id": "rev-1",
        "suite_id": "research-review-v1",
        "suite_version": 1,
        "case_id": "best-practice-adoption-retry",
        "candidate_id": "sol_runtime",
        "reviewer": {"kind": "human", "identity": "reviewer-1", "rubric_version": 1},
        "dimensions": [
            {"id": "accuracy", "score": 10, "max_score": 1, "evidence": ["cited primary source"]}
        ],
        "overall_score": 1,
        "critical_misses": [],
        "boundary_violations": [],
        "leakage": {
            "arm_identity_hidden": True,
            "ground_truth_hidden_until_scoring": True,
            "detected": False,
        },
        "attestation": {
            "blind_review": True,
            "no_arm_identity_access": True,
            "no_candidate_authorship": True,
            "independent_judgment": True,
            "signed_by": "reviewer-1",
            "signed_at": "2026-07-30T00:00:00Z",
            "review_input_hash": "sha256:" + ("a" * 64),
        },
        "reviewed_at": "2026-07-30T00:00:00Z",
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(payload)


def _outputs(suite: dict, manifest: dict, *, run_id: str) -> list[dict[str, object]]:
    return [
        {
            "run_id": run_id,
            "suite_sha256": manifest["suite_sha256"],
            "case_id": item["case_id"],
            "arm_id": item["arm_id"],
            "output": f"Synthetic response {index:03d}",
        }
        for index, item in enumerate(manifest["items"], start=1)
    ]


def _bound_results(manifest: dict) -> list[dict[str, object]]:
    return [
        {
            "run_id": manifest["run_id"],
            "suite_sha256": manifest["suite_sha256"],
            "case_id": item["case_id"],
            "arm_id": item["arm_id"],
            "task_success": 0.5,
            "citation_support": 0.5,
            "human_win": 0.5,
            "critical_misses": 0,
            "boundary_violations": 0,
            "latency_ms": 1,
            "cost_usd": 0,
        }
        for item in manifest["items"]
    ]


def _result(
    case_id: str,
    arm_id: str,
    *,
    task_success: float,
    citation_support: float = 0.95,
    human_win: float = 0.60,
    cost_usd: float = 1.0,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "arm_id": arm_id,
        "task_success": task_success,
        "citation_support": citation_support,
        "human_win": human_win,
        "critical_misses": 0,
        "boundary_violations": 0,
        "latency_ms": 1000,
        "cost_usd": cost_usd,
    }
