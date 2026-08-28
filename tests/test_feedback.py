import json
from pathlib import Path

from engineering_brain.feedback import build_next_plan_context, validate_feedback_packet


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
            "failure_kind": "latency_regression",
            "update_targets": ["skill", "test"],
            "regression_test": "tests/test_feedback.py::test_validate_feedback_packet_accepts_fde_contract",
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


def test_cli_feedback_validate_emits_next_plan_context(tmp_path, capfd) -> None:
    from engineering_brain.cli import main

    input_path = tmp_path / "feedback.json"
    input_path.write_text(json.dumps(packet()), encoding="utf-8")

    code = main(["feedback", "--input", str(input_path), "--json"])

    assert code == 0
    output = json.loads(capfd.readouterr().out)
    assert output["overall"] == "ok"
    assert output["next_plan"]["source_feedback_id"] == packet()["feedback_id"]


def test_feedback_schema_copy_declares_fde_contract() -> None:
    schema = json.loads(
        (ROOT / "engineering_brain" / "fde-feedback-packet.schema.json").read_text(
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


def test_cli_feedback_returns_structured_error_for_invalid_json(tmp_path, capfd) -> None:
    from engineering_brain.cli import main

    input_path = tmp_path / "invalid.json"
    input_path.write_text("{", encoding="utf-8")

    code = main(["feedback", "--input", str(input_path), "--json"])

    assert code == 1
    output = json.loads(capfd.readouterr().out)
    assert output["overall"] == "error"
    assert output["errors"] == ["JSONDecodeError: invalid feedback input"]
    assert output["next_plan"] is None
    assert str(input_path) not in json.dumps(output)


def test_feedback_rejects_adopt_while_human_review_is_pending() -> None:
    payload = packet()
    payload["act"]["decision"] = "adopt"

    errors = validate_feedback_packet(payload)

    assert any("adopt requires approved human review" in error for error in errors)


def test_feedback_rejects_adopt_without_review_even_when_packet_disables_gate() -> None:
    payload = packet()
    payload["act"]["decision"] = "adopt"
    payload["boundaries"]["human_gate_required"] = False

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


def test_cli_redacts_secret_bearing_feedback_id(tmp_path, capfd) -> None:
    from engineering_brain.cli import main

    payload = packet()
    payload["feedback_id"] = "ghp_" + ("x" * 36)
    input_path = tmp_path / "feedback.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    assert main(["feedback", "--input", str(input_path), "--json"]) == 1
    output = json.loads(capfd.readouterr().out)
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


def test_feedback_accepts_valid_non_bmp_unicode() -> None:
    payload = packet()
    payload["plan"]["hypothesis"] = "emoji is valid \U0001f680"

    assert validate_feedback_packet(payload) == []


def test_feedback_accepts_lowercase_rfc3339_utc_marker() -> None:
    payload = packet()
    payload["observed_at"] = "2026-07-28T18:00:00z"

    assert validate_feedback_packet(payload) == []


def test_feedback_rejects_personal_path_in_evidence_reference() -> None:
    payload = packet()
    payload["check"]["evidence"][0]["ref"] = (
        "C:" + chr(47) + "Users/alice/private/trace.json"
    )

    errors = validate_feedback_packet(payload)

    assert any("personal path" in error for error in errors)


def test_cli_redacts_all_metadata_for_sensitive_rejection(tmp_path, capfd) -> None:
    from engineering_brain.cli import main

    payload = packet()
    payload["schema_version"] = "ghp_" + ("x" * 36)
    payload["feedback_id"] = (
        "C:" + chr(47) + "Users/alice/private/feedback.json"
    )
    input_path = tmp_path / "feedback.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    assert main(["feedback", "--input", str(input_path), "--json"]) == 1
    output = json.loads(capfd.readouterr().out)
    assert output["schema_version"] is None
    assert output["feedback_id"] is None


def test_human_readable_output_preserves_unicode() -> None:
    from engineering_brain.cli import render_text

    rendered = render_text({"task": "日本語の実装"})

    assert "日本語の実装" in rendered
    assert "\\u65e5" not in rendered


# --- FDE 受入 contract -------------------------------------------------------
#
# このファイルの schema は fractal-decision-ecosystem の
# schemas/fde_feedback_packet.v1.schema.json を正本とする複製である
# ($id と docs/PDCA_FEEDBACK_LOOP.md を参照)。ADR-0004 は人力同期を前提に
# 置いていたが、実際には drift して非互換になった実績がある:
#   - act.required が 6 項目 (正本) に対し 4 項目まで減っていた
#   - update_targets の enum が双方向に非互換だった
#     (docs/registry/adr は正本が reject、none は複製が reject)
#   - consumer / ID 3 種の制約が失われていた
#
# 以下は「正本が受け付ける形」を複製側に固定するための contract test。
# 正本を変更したときは、ここも同時に更新すること。ここが落ちたら
# 「複製が正本から離れた」か「正本が変わった」のどちらかであり、
# どちらの場合も人間が同期を判断する必要がある。

FDE_ACT_REQUIRED = [
    "decision",
    "failure_kind",
    "update_targets",
    "regression_test",
    "rollback_path",
    "next_plan_input",
]
FDE_UPDATE_TARGET_VALUES = [
    "route",
    "skill",
    "gate",
    "test",
    "ssot",
    "roadmap",
    "none",
]
FDE_ID_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._:-]*$"


def _schema() -> dict:
    return json.loads(
        (ROOT / "engineering_brain" / "fde-feedback-packet.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_schema_declares_fde_as_its_canonical_source() -> None:
    """複製であることを $id が示し続けること。"""
    assert _schema()["$id"].endswith(
        "fractal-decision-ecosystem/blob/main/schemas/fde_feedback_packet.v1.schema.json"
    )


def test_act_required_matches_the_fde_contract() -> None:
    """必須項目が減ると、正本が reject する packet を通してしまう。"""
    assert _schema()["properties"]["act"]["required"] == FDE_ACT_REQUIRED


def test_update_targets_enum_matches_the_fde_contract() -> None:
    """enum が食い違うと、どちらか一方でしか通らない packet が生まれる。"""
    enum = _schema()["properties"]["act"]["properties"]["update_targets"]["items"]["enum"]
    assert enum == FDE_UPDATE_TARGET_VALUES


def test_consumer_is_pinned_to_fde() -> None:
    """正本は fde 宛て以外を受け付けない。"""
    assert _schema()["properties"]["consumer"] == {"const": "fde"}


def test_identifier_fields_keep_the_fde_pattern() -> None:
    """pattern が抜けると、空白や記号入りの ID を通してしまう。"""
    props = _schema()["properties"]
    for field in ("feedback_id", "source_run_id", "producer"):
        assert props[field].get("pattern") == FDE_ID_PATTERN, field


def test_packet_missing_failure_kind_is_rejected() -> None:
    """正本が必須にしている項目は、複製側でも落ちること。"""
    broken = packet()
    del broken["act"]["failure_kind"]
    assert validate_feedback_packet(broken) != []


def test_packet_missing_regression_test_is_rejected() -> None:
    broken = packet()
    del broken["act"]["regression_test"]
    assert validate_feedback_packet(broken) != []


def test_update_target_outside_the_fde_enum_is_rejected() -> None:
    """docs / registry / adr は正本が受け付けないので、ここでも通さない。"""
    for value in ("docs", "registry", "adr"):
        broken = packet()
        broken["act"]["update_targets"] = [value]
        assert validate_feedback_packet(broken) != [], value


def test_update_target_none_is_accepted() -> None:
    """逆に none は正本が受け付けるので、ここで弾いてはいけない。"""
    ok = packet()
    ok["act"]["update_targets"] = ["none"]
    assert validate_feedback_packet(ok) == []


def test_consumer_other_than_fde_is_rejected() -> None:
    broken = packet()
    broken["consumer"] = "someone-else"
    assert validate_feedback_packet(broken) != []


def test_identifier_with_whitespace_is_rejected() -> None:
    broken = packet()
    broken["feedback_id"] = "has space"
    assert validate_feedback_packet(broken) != []
