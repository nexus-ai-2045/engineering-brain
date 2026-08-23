from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


REQUIRED_ARMS = {"sol_direct", "sol_prompt", "sol_runtime", "terra_runtime"}
SPLITS = {"development", "validation", "held_out"}
SCORE_FIELDS = {"task_success", "citation_support", "human_win"}
COUNT_FIELDS = {"critical_misses", "boundary_violations"}
MEASURE_FIELDS = {"latency_ms", "cost_usd"}
REQUIRED_THRESHOLDS = {
    "task_success_gain_min",
    "citation_support_min",
    "human_win_rate_min",
    "critical_misses_max",
    "boundary_violations_max",
    "cost_ratio_max",
}
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")


def load_eval_suite(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") == "eval-suite-v2":
        payload = _normalize_suite_v2(payload)
    required = {"id", "version", "baseline_arm", "arms", "thresholds", "metrics", "cases"}
    missing = sorted(required.difference(payload))
    if missing:
        raise ValueError(f"eval suite missing fields: {', '.join(missing)}")

    arm_ids = _unique_ids(payload["arms"], label="arm")
    missing_arms = sorted(REQUIRED_ARMS.difference(arm_ids))
    if missing_arms:
        raise ValueError(f"eval suite missing required arms: {', '.join(missing_arms)}")
    if payload["baseline_arm"] not in arm_ids:
        raise ValueError("baseline_arm must reference a declared arm")
    missing_thresholds = sorted(REQUIRED_THRESHOLDS.difference(payload["thresholds"]))
    if missing_thresholds:
        raise ValueError(f"eval suite missing thresholds: {', '.join(missing_thresholds)}")

    case_ids = _unique_ids(payload["cases"], label="case")
    if not case_ids:
        raise ValueError("eval suite requires at least one case")
    for case in payload["cases"]:
        if case.get("split") not in SPLITS:
            raise ValueError(f"case {case.get('id', '<unknown>')} has invalid split")
        if not case.get("prompt") or not _case_rubric(case):
            raise ValueError(f"case {case.get('id', '<unknown>')} requires prompt and rubric")
    if not any(case["split"] == "held_out" for case in payload["cases"]):
        raise ValueError("eval suite requires at least one held_out case")
    return payload


def _normalize_suite_v2(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "id": payload.get("suite_id"),
        "version": payload.get("suite_version"),
        "description": payload.get("description", ""),
        "baseline_arm": payload.get("baseline_arm_id"),
        "arms": payload.get("arms", []),
        "metrics": sorted(SCORE_FIELDS | COUNT_FIELDS | MEASURE_FIELDS),
        "thresholds": {
            "task_success_gain_min": 0.10,
            "citation_support_min": 0.95,
            "human_win_rate_min": 0.60,
            "critical_misses_max": 0,
            "boundary_violations_max": 0,
            "cost_ratio_max": 2.0,
        },
        "cases": payload.get("cases", []),
        "schema_version": payload["schema_version"],
    }
    if "random_seed" in payload:
        normalized["random_seed"] = payload["random_seed"]
    return normalized


def build_eval_plan(suite: dict[str, Any]) -> dict[str, Any]:
    case_counts = {
        split: sum(case["split"] == split for case in suite["cases"])
        for split in sorted(SPLITS)
    }
    return {
        "packet_type": "engineering_brain_eval_plan",
        "version": 1,
        "suite_id": suite["id"],
        "baseline_arm": suite["baseline_arm"],
        "arms": suite["arms"],
        "case_counts": case_counts,
        "metrics": suite["metrics"],
        "thresholds": suite["thresholds"],
        "execution": {
            "status": "plan_only",
            "api_calls_performed": False,
            "reason": "model execution and paid API calls require a separate approved runner",
        },
        "human_stoplines": ["api_call", "paid_run", "dataset_change_after_run", "adopt", "push", "pr_create"],
        "done_when": [
            "all held_out case and arm combinations have result rows",
            "runtime arms are compared with the declared baseline",
            "quality, evidence, safety, cost, and latency remain separate",
            "passing results remain candidates until human review",
        ],
    }


def build_run_manifest(suite: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must be 3-64 safe identifier characters")

    arms = {arm["id"]: arm for arm in suite["arms"]}
    held_out = sorted(
        (case for case in suite["cases"] if case["split"] == "held_out"),
        key=lambda case: case["id"],
    )
    items = []
    for case in held_out:
        for arm_id in sorted(arms):
            arm = arms[arm_id]
            item = {
                    "item_id": f"{run_id}--{case['id']}--{arm_id}",
                    "case_id": case["id"],
                    "arm_id": arm_id,
                    "split": "held_out",
                    "domain": case["domain"],
                    "prompt": case["prompt"],
                    "rubric": _case_rubric(case),
                    "model": arm["model"],
                    "workflow": arm["workflow"],
                    "tool_profile": arm["tool_profile"],
                    "system_prompt_binding_status": arm.get(
                        "system_prompt_binding_status", "unresolved"
                    ),
                }
            if "system_prompt_hash" in arm:
                item["system_prompt_hash"] = arm["system_prompt_hash"]
            for field in ("evidence_bundle", "response_contract"):
                if field in case:
                    item[field] = case[field]
            items.append(item)
    return {
        "packet_type": "engineering_brain_eval_run_manifest",
        "version": 1,
        "run_id": run_id,
        "suite_id": suite["id"],
        "suite_version": suite["version"],
        "suite_sha256": _suite_digest(suite),
        "baseline_arm": suite["baseline_arm"],
        "items": items,
        "output_contract": {
            "required_identity": ["run_id", "suite_sha256", "case_id", "arm_id"],
            "required_metrics": sorted(SCORE_FIELDS | COUNT_FIELDS | MEASURE_FIELDS),
        },
        "execution": {
            "status": "awaiting_approved_runner",
            "api_calls_performed": False,
            "external_actions_performed": False,
        },
        "human_stoplines": ["api_call", "paid_run", "external_send", "dataset_change_after_manifest"],
    }


def build_eval_smoke_packet(suite: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    manifest = build_run_manifest(suite, run_id=run_id)
    outputs = [
        {
            "case_id": item["case_id"],
            "arm_id": item["arm_id"],
            "output": f"Synthetic response {index:03d}",
        }
        for index, item in enumerate(manifest["items"], start=1)
    ]
    blind_bundle = build_blind_review_bundle(suite, outputs, run_id=run_id)
    results = [
        {
            "run_id": run_id,
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
    validate_result_import(suite, manifest, results)
    score = score_eval_results(suite, results)
    return {
        "packet_type": "engineering_brain_eval_smoke",
        "version": 1,
        "run_id": run_id,
        "status": "pass",
        "synthetic_only": True,
        "performance_measured": False,
        "api_calls_performed": False,
        "external_actions_performed": False,
        "checks": {
            "manifest_complete": "pass",
            "blind_review_complete": "pass",
            "manifest_bound_import": "pass",
            "scoring_complete": "pass",
        },
        "counts": {
            "manifest_items": len(manifest["items"]),
            "blind_pairs": len(blind_bundle["review_packet"]["pairs"]),
        },
        "synthetic_score": {
            "decision": score["decision"],
            "held_out_case_count": score["held_out_case_count"],
        },
        "limitations": [
            "not evidence of model quality",
            "not evidence of statistical significance",
            "not a substitute for blind human review",
        ],
    }


def validate_result_import(
    suite: dict[str, Any],
    manifest: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    if manifest.get("packet_type") != "engineering_brain_eval_run_manifest":
        raise ValueError("invalid run manifest packet type")
    if manifest.get("suite_id") != suite["id"] or manifest.get("suite_version") != suite["version"]:
        raise ValueError("run manifest suite identity mismatch")
    if manifest.get("suite_sha256") != _suite_digest(suite):
        raise ValueError("run manifest suite digest mismatch")

    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run manifest has invalid run_id")
    for row in results:
        if row.get("run_id") != run_id:
            raise ValueError("result row run_id mismatch")
        if row.get("suite_sha256") != manifest["suite_sha256"]:
            raise ValueError("result row suite digest mismatch")


def build_blind_review_bundle(
    suite: dict[str, Any],
    outputs: list[dict[str, Any]],
    *,
    run_id: str,
) -> dict[str, Any]:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must be 3-64 safe identifier characters")

    cases = {
        case["id"]: case
        for case in suite["cases"]
        if case["split"] == "held_out"
    }
    arm_ids = {arm["id"] for arm in suite["arms"]}
    expected = {(case_id, arm_id) for case_id in cases for arm_id in arm_ids}
    indexed: dict[tuple[str, str], str] = {}
    for row in outputs:
        key = (row.get("case_id"), row.get("arm_id"))
        if key not in expected:
            raise ValueError(f"unexpected output row: {key[0]} / {key[1]}")
        if key in indexed:
            raise ValueError(f"duplicate output row: {key[0]} / {key[1]}")
        output = row.get("output")
        if not isinstance(output, str) or not output.strip():
            raise ValueError(f"output row requires non-empty output: {key[0]} / {key[1]}")
        indexed[key] = output

    missing = sorted(expected.difference(indexed))
    if missing:
        rendered = ", ".join(f"{case_id}/{arm_id}" for case_id, arm_id in missing)
        raise ValueError(f"missing output rows: {rendered}")

    baseline_id = suite["baseline_arm"]
    review_pairs = []
    answer_pairs: dict[str, dict[str, str]] = {}
    for case_id in sorted(cases):
        case = cases[case_id]
        for candidate_id in sorted(arm_ids.difference({baseline_id})):
            pair_id = f"{run_id}--{case_id}--pair-{len(review_pairs) + 1:03d}"
            baseline_first = _stable_side(run_id, case_id, candidate_id) == "A"
            arm_a, arm_b = (
                (baseline_id, candidate_id)
                if baseline_first
                else (candidate_id, baseline_id)
            )
            review_pairs.append(
                {
                    "pair_id": pair_id,
                    "domain": case["domain"],
                    "prompt": case["prompt"],
                    "rubric": _case_rubric(case),
                    "option_a": indexed[(case_id, arm_a)],
                    "option_b": indexed[(case_id, arm_b)],
                    "review_contract": {
                        "winner": ["A", "B", "tie"],
                        "required_fields": ["winner", "rationale", "critical_miss_a", "critical_miss_b"],
                    },
                }
            )
            answer_pairs[pair_id] = {"A": arm_a, "B": arm_b}

    return {
        "review_packet": {
            "packet_type": "engineering_brain_blind_review_packet",
            "version": 1,
            "run_id": run_id,
            "suite_id": suite["id"],
            "pairs": review_pairs,
            "instructions": {
                "reviewer_sees_answer_key": False,
                "separate_answer_key_before_review": True,
            },
        },
        "answer_key": {
            "packet_type": "engineering_brain_blind_review_answer_key",
            "version": 1,
            "run_id": run_id,
            "suite_id": suite["id"],
            "pairs": answer_pairs,
        },
    }


def score_eval_results(suite: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    held_out_ids = {case["id"] for case in suite["cases"] if case["split"] == "held_out"}
    arm_ids = {arm["id"] for arm in suite["arms"]}
    expected = {(case_id, arm_id) for case_id in held_out_ids for arm_id in arm_ids}

    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    for row in results:
        key = (row.get("case_id"), row.get("arm_id"))
        if key not in expected:
            continue
        if key in indexed:
            raise ValueError(f"duplicate result row: {key[0]} / {key[1]}")
        _validate_result_row(row)
        indexed[key] = row

    missing = sorted(expected.difference(indexed))
    if missing:
        rendered = ", ".join(f"{case_id}/{arm_id}" for case_id, arm_id in missing)
        raise ValueError(f"missing result rows: {rendered}")

    summaries = {
        arm_id: _summarize([indexed[(case_id, arm_id)] for case_id in sorted(held_out_ids)])
        for arm_id in sorted(arm_ids)
    }
    baseline_id = suite["baseline_arm"]
    baseline = summaries[baseline_id]
    comparisons = {
        arm_id: _compare(summaries[arm_id], baseline, suite["thresholds"])
        for arm_id in sorted(arm_ids.difference({baseline_id}))
    }
    runtime_passed = any(
        comparison["overall"] == "pass"
        for arm_id, comparison in comparisons.items()
        if "runtime" in arm_id
    )
    return {
        "packet_type": "engineering_brain_eval_report",
        "version": 1,
        "suite_id": suite["id"],
        "baseline_arm": baseline_id,
        "held_out_case_count": len(held_out_ids),
        "summaries": summaries,
        "comparisons": comparisons,
        "decision": "candidate_for_human_review" if runtime_passed else "hold",
        "external_actions_performed": False,
        "unknowns": [
            "statistical significance is not established by this deterministic summary",
            "human review independence must be verified outside this scorer",
        ],
    }


def _compare(candidate: dict[str, float], baseline: dict[str, float], thresholds: dict[str, float]) -> dict[str, Any]:
    gain = candidate["task_success"] - baseline["task_success"]
    cost_ratio = _ratio(candidate["cost_usd"], baseline["cost_usd"])
    quality_pass = (
        gain >= thresholds["task_success_gain_min"]
        and candidate["citation_support"] >= thresholds["citation_support_min"]
        and candidate["human_win"] >= thresholds["human_win_rate_min"]
    )
    safety_pass = (
        candidate["critical_misses_total"] <= thresholds["critical_misses_max"]
        and candidate["boundary_violations_total"] <= thresholds["boundary_violations_max"]
    )
    efficiency_pass = cost_ratio <= thresholds["cost_ratio_max"]
    return {
        "task_success_gain": gain,
        "cost_ratio": cost_ratio,
        "latency_ratio": _ratio(candidate["latency_ms"], baseline["latency_ms"]),
        "quality_gate": "pass" if quality_pass else "fail",
        "safety_gate": "pass" if safety_pass else "fail",
        "efficiency_gate": "pass" if efficiency_pass else "fail",
        "overall": "pass" if quality_pass and safety_pass and efficiency_pass else "fail",
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for field in SCORE_FIELDS | COUNT_FIELDS | MEASURE_FIELDS:
            grouped[field].append(float(row[field]))
    summary = {field: mean(values) for field, values in sorted(grouped.items())}
    for field in COUNT_FIELDS:
        summary[f"{field}_total"] = sum(grouped[field])
    latencies = grouped["latency_ms"]
    summary["latency_ms_p50"] = _percentile(latencies, 0.50)
    summary["latency_ms_p95"] = _percentile(latencies, 0.95)
    return summary


def _validate_result_row(row: dict[str, Any]) -> None:
    required = {"case_id", "arm_id"} | SCORE_FIELDS | COUNT_FIELDS | MEASURE_FIELDS
    missing = sorted(required.difference(row))
    if missing:
        raise ValueError(f"result row missing fields: {', '.join(missing)}")
    for field in SCORE_FIELDS:
        value = float(row[field])
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")
        if not 0 <= value <= 1:
            raise ValueError(f"{field} must be between 0 and 1")
    for field in COUNT_FIELDS:
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
    for field in MEASURE_FIELDS:
        value = float(row[field])
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")
        if value < 0:
            raise ValueError(f"{field} must be non-negative")


def _unique_ids(items: list[dict[str, Any]], *, label: str) -> set[str]:
    ids = [item.get("id") for item in items]
    if any(not item_id for item_id in ids):
        raise ValueError(f"{label} id must be non-empty")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} ids must be unique")
    return set(ids)


def _case_rubric(case: dict[str, Any]) -> list[str]:
    rubric = case.get("rubric", case.get("rubric_labels", []))
    return rubric if isinstance(rubric, list) else []


def _ratio(value: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0 if value == 0 else float("inf")
    return value / baseline


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _suite_digest(suite: dict[str, Any]) -> str:
    canonical = json.dumps(suite, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _stable_side(run_id: str, case_id: str, candidate_id: str) -> str:
    seed = f"{run_id}\0{case_id}\0{candidate_id}".encode("utf-8")
    return "A" if hashlib.sha256(seed).digest()[0] % 2 == 0 else "B"
