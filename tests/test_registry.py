from pathlib import Path

import pytest

from engineering_brain.registry import (
    adoption_units,
    select_technology_sources,
    select_units,
    technology_sources,
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
        / "registry"
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
