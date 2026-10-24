from dataclasses import replace
from pathlib import Path

import pytest

from engineering_brain.cli import main
from engineering_brain.registry import (
    DEFAULT_LOCAL_LEARNINGS,
    DEFAULT_REGISTRY,
    LocalLearning,
    PACKAGE_ROOT,
    adoption_units,
    check_learning_assurance,
    is_operationally_adopted,
    list_local_learnings,
    load_registry,
    local_learnings,
    plan_adopt_learning,
    plan_learning_transition,
    select_technology_sources,
    select_units,
    start_field_review,
    technology_sources,
    validate_local_learning,
    validate_technology_source,
    validate_unit,
)


def test_registry_loads_required_units() -> None:
    ids = {unit.id for unit in adoption_units()}
    assert "fact_source_gate" in ids
    assert "scope_write_boundary_gate" in ids
    assert "human_publication_review_gate" in ids


IMPORTED_RUNTIME_LEARNING_IDS = (
    "clean-ci-dependency-contract",
    "executable-path-contract",
    "artifact-lineage-contract",
    "workflow-runtime-stopline-contract",
)
RUNTIME_LEARNING_OBSERVATION_SHA = "e7cac84f0f25b2c623b15b177e302544ca505ceb"
RUNTIME_LEARNING_OBSERVATION_DATE = "2026-07-19"


def _local_learnings_text() -> str:
    path = (
        Path(__file__).resolve().parents[1]
        / "engineering_brain"
        / "data"
        / "local-learnings.yaml"
    )
    assert path.is_file()
    return path.read_text(encoding="utf-8")


def _learning_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    parts = text.split("\n  - id: ")
    for part in parts[1:]:
        learning_id, _, rest = part.partition("\n")
        blocks[learning_id.strip()] = rest
    return blocks


def test_candidate_learning_packets_keep_stable_proposed_solution_shape() -> None:
    text = _local_learnings_text()

    assert text.count("proposed_solution:") == 7
    for learning_id in IMPORTED_RUNTIME_LEARNING_IDS:
        assert f"id: {learning_id}" in text


def test_imported_runtime_learnings_keep_retrievable_memory_evidence() -> None:
    blocks = _learning_blocks(_local_learnings_text())

    for learning_id in IMPORTED_RUNTIME_LEARNING_IDS:
        block = blocks[learning_id]
        assert "source_lane: memory" in block
        assert RUNTIME_LEARNING_OBSERVATION_SHA in block
        assert RUNTIME_LEARNING_OBSERVATION_DATE in block
        assert "PR review:" not in block
        assert "local learning; field review pending" not in block


def test_clean_ci_rule_requires_isolated_manifest_environment() -> None:
    block = _learning_blocks(_local_learnings_text())["clean-ci-dependency-contract"]
    rule = next(line for line in block.splitlines() if line.startswith("    reusable_rule:"))
    assert "isolated" in rule
    assert "manifest" in rule


def test_workflow_runtime_rule_preserves_immutable_invariants() -> None:
    block = _learning_blocks(_local_learnings_text())["workflow-runtime-stopline-contract"]
    rule = next(line for line in block.splitlines() if line.startswith("    reusable_rule:"))
    lowered = rule.lower()
    assert "deadline" in lowered
    assert "oidc" in lowered
    assert "budget" in lowered
    assert "immutable" in lowered or "固定" in rule


def test_select_units_matches_triggers() -> None:
    ids = {unit.id for unit in select_units(["security"])}
    assert ids == {"agent_containment_gate"}


def test_validate_unit_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="missing fields"):
        validate_unit({"id": "broken"})


def test_technology_sources_include_requested_domains() -> None:
    domains = {source.domain for source in technology_sources()}
    assert {
        "go",
        "bun",
        "vue-nuxt",
        "azure",
        "server-api",
        "container-kubernetes",
        "node-express",
        "nextjs",
        "python",
        "rust",
        "terraform",
        "github-actions",
        "docker",
        "postgresql",
        "github-repo-lifecycle",
        "gcp-ai-orchestration",
        "ocr-document-ai",
    }.issubset(domains)


def test_select_technology_sources_matches_alias() -> None:
    ids = {source.id for source in select_technology_sources("az")}
    assert ids == {"azure_well_architected_gate"}


def test_validate_technology_source_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="missing fields"):
        validate_technology_source({"id": "broken"})


def test_gcp_and_ocr_sources_are_adopted_not_merely_catalogued() -> None:
    gcp = select_technology_sources("gcp")
    ocr = select_technology_sources("ocr")
    assert {source.id for source in gcp} == {"gcp_ai_orchestration_assurance_sources"}
    assert {source.id for source in ocr} == {"ocr_structured_evaluation_sources"}
    assert all(source.status == "adopted" for source in gcp + ocr)


def test_local_learnings_yaml_loads_with_existing_schema() -> None:
    learnings = local_learnings()
    assert len(learnings) == 7
    assert {item.decision for item in learnings} == {"candidate"}
    assert {item.field_review for item in learnings} == {"pending"}
    assert sum(1 for item in learnings if item.decision == "adopted") == 0
    for item in learnings:
        assert item.source_pointer
        assert item.review_trigger
        assert "assurance_gate" in item.__dataclass_fields__


def test_list_local_learnings_separates_pending_field_review_from_adopted() -> None:
    pending = list_local_learnings(field_review="pending")
    adopted = list_local_learnings(decision="adopted")
    assert len(pending) == 7
    assert adopted == []
    assert all(item.decision == "candidate" for item in pending)


def test_pending_field_review_fails_assurance_and_adopt_checks() -> None:
    learning = local_learnings()[0]
    assurance = check_learning_assurance(learning)
    assert assurance["status"] == "block"
    assert assurance["operationally_guaranteed"] is False
    assert any("field_review is pending" in failure for failure in assurance["failures"])

    adopt = plan_adopt_learning(learning, current_turn_approval=True)
    assert adopt["status"] == "error"
    assert adopt["ssot_mutated"] is False
    assert any("field_review" in error for error in adopt["errors"])


def test_claiming_adopted_with_pending_field_review_is_not_operationally_guaranteed() -> None:
    learning = local_learnings()[0]
    forged = replace(learning, decision="adopted", field_review="pending")
    assurance = check_learning_assurance(forged)
    assert assurance["status"] == "block"
    assert assurance["operationally_guaranteed"] is False


def test_invalid_learning_transitions_fail_closed() -> None:
    learning = local_learnings()[0]
    skipped = plan_learning_transition(learning, target_decision="adopted", current_turn_approval=True)
    assert skipped["status"] == "error"
    assert any("invalid transition" in error or "field_review first" in error for error in skipped["errors"])

    for terminal in ("hold", "rejected"):
        bypass = plan_learning_transition(learning, target_decision=terminal)
        assert bypass["status"] == "error"
        assert any(f"invalid transition: candidate -> {terminal}" in error for error in bypass["errors"])

    rejected = replace(learning, decision="rejected", field_review="passed")
    reopen = plan_learning_transition(rejected, target_decision="adopted", current_turn_approval=True)
    assert reopen["status"] == "error"
    assert any("invalid transition" in error for error in reopen["errors"])


def test_field_review_then_adopt_requires_current_turn_approval() -> None:
    learning = local_learnings()[0]
    started = start_field_review(learning)
    assert started["status"] == "ok"
    assert started["to_decision"] == "field_review"
    assert started["to_field_review"] == "in_progress"
    assert started["ssot_mutated"] is False

    in_review = replace(learning, decision="field_review", field_review="in_progress")
    plan_only = plan_adopt_learning(in_review, current_turn_approval=False)
    assert plan_only["status"] == "plan_only"
    assert plan_only["plan_only"] is True
    assert plan_only["ssot_mutated"] is False
    assert any("current-turn approval" in error for error in plan_only["errors"])

    approved = plan_adopt_learning(in_review, current_turn_approval=True)
    assert approved["status"] == "ok"
    assert approved["to_decision"] == "adopted"
    assert approved["to_field_review"] == "passed"
    assert approved["ssot_mutated"] is False
    planned = approved["planned"]
    assert (
        check_learning_assurance(
            LocalLearning(
                **{
                    **planned,
                    "source_pointer": tuple(planned["source_pointer"]),
                }
            )
        )["status"]
        == "pass"
    )


def test_default_local_learnings_resolves_like_packaged_registry_data() -> None:
    assert DEFAULT_LOCAL_LEARNINGS.parent == DEFAULT_REGISTRY.parent
    assert DEFAULT_LOCAL_LEARNINGS == PACKAGE_ROOT / "data" / "local-learnings.yaml"
    assert DEFAULT_LOCAL_LEARNINGS.is_file()
    assert local_learnings(DEFAULT_LOCAL_LEARNINGS)


def test_adopted_list_and_count_ignore_pending_field_review(tmp_path: Path, capfd) -> None:
    fixture = tmp_path / "mixed-learnings.yaml"
    fixture.write_text(
        """
version: 1
updated_at: "2026-08-28"
learnings:
  - id: pending-but-claims-adopted
    source_lane: memory
    source_pointer:
      - "fixture pointer"
    observed_problem: mixed fail-closed case
    proposed_solution: null
    reusable_rule: pending field_review is never adopted
    evidence: fixture
    freshness: "2026-08-28"
    rights_and_privacy: fixture only
    adoption_target: tests
    decision: adopted
    field_review: pending
    review_trigger: "fixture cycle"
    assurance_gate: null
    decision_reason: forged adopted with pending review
  - id: truly-adopted
    source_lane: memory
    source_pointer:
      - "fixture pointer adopted"
    observed_problem: real adopt
    proposed_solution: null
    reusable_rule: field_review passed
    evidence: fixture
    freshness: "2026-08-28"
    rights_and_privacy: fixture only
    adoption_target: tests
    decision: adopted
    field_review: passed
    review_trigger: "fixture cycle"
    assurance_gate: null
    decision_reason: operationally adopted
""".strip()
        + "\n",
        encoding="utf-8",
    )
    pending_claim = next(
        item for item in local_learnings(fixture) if item.id == "pending-but-claims-adopted"
    )
    assert is_operationally_adopted(pending_claim) is False
    assert list_local_learnings(fixture, decision="adopted") == [
        item for item in local_learnings(fixture) if item.id == "truly-adopted"
    ]

    assert main(["learnings", "list", "--registry", str(fixture), "--json"]) == 0
    listed = capfd.readouterr().out
    assert '"adopted": 1' in listed
    assert '"pending_field_review": 1' in listed
    assert main(["learnings", "list", "--registry", str(fixture), "--decision", "adopted", "--json"]) == 0
    adopted_list = capfd.readouterr().out
    assert "truly-adopted" in adopted_list
    assert "pending-but-claims-adopted" not in adopted_list


def test_block_scalar_keeps_list_looking_lines(tmp_path: Path) -> None:
    fixture = tmp_path / "block-scalar-learnings.yaml"
    fixture.write_text(
        """
version: 1
updated_at: "2026-08-28"
learnings:
  - id: block-scalar-bullets
    source_lane: memory
    source_pointer:
      - "fixture pointer"
    observed_problem: parser must keep bullets inside scalars
    proposed_solution: null
    reusable_rule: keep indented bullet lines
    evidence: fixture
    freshness: "2026-08-28"
    rights_and_privacy: fixture only
    adoption_target: tests
    decision: candidate
    field_review: pending
    review_trigger: "fixture cycle"
    assurance_gate: null
    decision_reason: |
      summary line
      - first reason
      - second reason
""".strip()
        + "\n",
        encoding="utf-8",
    )
    raw = load_registry(fixture)["learnings"][0]
    reason = raw["decision_reason"]
    assert "summary line" in reason
    assert "- first reason" in reason
    assert "- second reason" in reason
    learning = local_learnings(fixture)[0]
    assert "- first reason" in learning.decision_reason


def test_existing_candidate_packets_remain_unchanged_in_decision() -> None:
    text = _local_learnings_text()
    assert text.count("decision: candidate") == 7
    assert "decision: adopted" not in text
    assert "decision: field_review" not in text
    assert text.count("field_review: pending") >= 7


def test_validate_local_learning_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="missing fields"):
        validate_local_learning({"id": "broken"})


def test_cli_learnings_list_and_assurance_fail_closed(capfd) -> None:
    assert main(["learnings", "list", "--field-review", "pending", "--json"]) == 0
    listed = capfd.readouterr().out
    assert "pending_field_review" in listed
    assert '"adopted": 0' in listed

    learning_id = local_learnings()[0].id
    assert main(["learnings", "assurance", "--id", learning_id, "--json"]) == 1
    assurance_out = capfd.readouterr().out
    assert '"status": "block"' in assurance_out

    assert main(["learnings", "adopt", "--id", learning_id, "--json"]) == 1
    adopt_out = capfd.readouterr().out
    assert "ssot_mutated" in adopt_out
    assert "false" in adopt_out.lower()
