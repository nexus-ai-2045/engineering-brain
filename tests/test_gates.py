from pathlib import Path

from devbrain.gates import evaluate_triggers, route_task


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
