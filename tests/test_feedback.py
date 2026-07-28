import json
from pathlib import Path

from devbrain.feedback import build_next_plan_context, validate_feedback_packet


ROOT = Path(__file__).resolve().parents[1]


def packet() -> dict:
    return {
        "schema_version": "fde.feedback.v1",
        "feedback_id": "feedback-long-thread-latency-001",
        "source_run_id": "run-long-thread-baseline-001",
        "producer": "engineering-brain",
        "consumer": "fde",
        "observed_at": "2026-07-28T18:00:00+09:00",
        "plan": {
            "hypothesis": "long task reconstruction dominates open latency",
            "expected_effect": "reduce time to interactive",
            "verification_plan": ["compare short and long tasks"],
        },
        "do": {
            "actions": ["collect read-only timing"],
            "changed_artifacts": [],
        },
        "check": {
            "outcome": "partial",
            "evidence": [
                {"kind": "trace", "ref": "run-long-thread-baseline-001"}
            ],
            "human_review": "pending",
        },
        "act": {
            "decision": "revise",
            "update_targets": ["skill", "test"],
            "rollback_path": "remove the candidate detector",
            "next_plan_input": "capture renderer phase timing",
        },
        "boundaries": {
            "external_actions_performed": False,
            "human_gate_required": True,
        },
        "provenance": {
            "source_refs": [
                {"kind": "source", "ref": "rollout-metadata-summary"}
            ],
        },
    }


def test_validate_feedback_packet_accepts_fde_contract() -> None:
    assert validate_feedback_packet(packet()) == []


def test_next_plan_context_carries_act_without_replaying_raw_history() -> None:
    context = build_next_plan_context(packet())

    assert context == {
        "schema_version": "engineering-brain.next-plan.v1",
        "source_feedback_id": "feedback-long-thread-latency-001",
        "source_run_id": "run-long-thread-baseline-001",
        "decision": "revise",
        "next_plan_input": "capture renderer phase timing",
        "evidence_refs": [
            {"kind": "trace", "ref": "run-long-thread-baseline-001"}
        ],
        "human_gate_required": True,
    }


def test_cli_feedback_validate_emits_next_plan_context(tmp_path, capsys) -> None:
    from devbrain.cli import main

    input_path = tmp_path / "feedback.json"
    input_path.write_text(json.dumps(packet()), encoding="utf-8")

    code = main(["feedback", "--input", str(input_path), "--json"])

    assert code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["overall"] == "ok"
    assert output["next_plan"]["source_feedback_id"] == packet()["feedback_id"]


def test_feedback_schema_copy_declares_fde_contract() -> None:
    schema = json.loads(
        (ROOT / "devbrain" / "fde-feedback-packet.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["properties"]["schema_version"]["const"] == "fde.feedback.v1"


def test_validate_feedback_packet_rejects_unknown_update_target() -> None:
    payload = packet()
    payload["act"]["update_targets"] = ["invented-target"]

    errors = validate_feedback_packet(payload)

    assert any("update_targets" in error for error in errors)


def test_validate_feedback_packet_rejects_unknown_nested_field() -> None:
    payload = packet()
    payload["check"]["raw_chat"] = "must not cross the feedback boundary"

    errors = validate_feedback_packet(payload)

    assert any("check: invalid additionalProperties" in error for error in errors)


def test_validate_feedback_packet_rejects_personal_path_in_next_plan() -> None:
    payload = packet()
    payload["act"]["next_plan_input"] = (
        "inspect "
        + "C:"
        + chr(47)
        + "Users/alice/private/session.jsonl"
    )

    errors = validate_feedback_packet(payload)

    assert any("personal path" in error for error in errors)


def test_cli_feedback_returns_structured_error_for_invalid_json(tmp_path, capsys) -> None:
    from devbrain.cli import main

    input_path = tmp_path / "invalid.json"
    input_path.write_text("{", encoding="utf-8")

    code = main(["feedback", "--input", str(input_path), "--json"])

    assert code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["overall"] == "error"
    assert output["errors"] == ["JSONDecodeError: invalid feedback input"]
    assert output["next_plan"] is None
    assert str(input_path) not in json.dumps(output)


def test_feedback_rejects_adopt_while_human_review_is_pending() -> None:
    payload = packet()
    payload["act"]["decision"] = "adopt"

    errors = validate_feedback_packet(payload)

    assert any("adopt requires approved human review" in error for error in errors)


def test_feedback_rejects_secret_like_content() -> None:
    payload = packet()
    payload["act"]["next_plan_input"] = "use token " + "ghp_" + ("x" * 36)

    errors = validate_feedback_packet(payload)

    assert any("secret-like" in error for error in errors)


def test_validation_errors_do_not_echo_rejected_secret() -> None:
    payload = packet()
    secret = "Bearer " + ("x" * 32)
    payload["check"]["evidence"][0]["ref"] = secret

    errors = validate_feedback_packet(payload)

    assert errors
    assert secret not in json.dumps(errors)


def test_feedback_rejects_all_field_paths_tokens_and_rejected_adoption() -> None:
    payload = packet()
    payload["plan"]["hypothesis"] = "github_pat_" + ("x" * 40)
    payload["do"]["changed_artifacts"] = [
        chr(47) + "home/alice/private/trace.json"
    ]
    payload["check"]["human_review"] = "rejected"
    payload["boundaries"]["human_gate_required"] = False
    payload["act"]["decision"] = "adopt"

    errors = validate_feedback_packet(payload)

    assert any("secret-like" in error for error in errors)
    assert any("personal path" in error for error in errors)
    assert any("conflicts with rejected" in error for error in errors)


def test_cli_redacts_secret_bearing_feedback_id(tmp_path, capsys) -> None:
    from devbrain.cli import main

    payload = packet()
    payload["feedback_id"] = "ghp_" + ("x" * 36)
    input_path = tmp_path / "feedback.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    assert main(["feedback", "--input", str(input_path), "--json"]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["feedback_id"] is None


def test_feedback_rejects_invalid_date_large_collection_and_surrogate() -> None:
    payload = packet()
    payload["observed_at"] = "not-a-date"
    payload["do"]["actions"] = ["step"] * 17
    payload["producer"] = "\ud800"

    errors = validate_feedback_packet(payload)

    assert any("observed_at" in error for error in errors)
    assert any("actions" in error for error in errors)
    assert any("Unicode surrogate" in error for error in errors)
