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
    }.issubset(domains)


def test_select_technology_sources_matches_alias() -> None:
    ids = {source.id for source in select_technology_sources("az")}
    assert ids == {"azure_well_architected_gate"}


def test_validate_technology_source_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="missing fields"):
        validate_technology_source({"id": "broken"})
