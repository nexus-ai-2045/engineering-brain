from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_adr_index_and_first_decision_exist() -> None:
    index = read_doc("docs/adr/README.md")
    adr = read_doc("docs/adr/ADR-0001-engineering-brain-private-knowledge-repo.md")

    assert "ADR-0001" in index
    assert "engineering-brain" in adr
    assert "private executable SSOT" in adr
    assert "Obsidian" in adr
    assert "Human Review Gate" in adr


def test_knowledge_intake_keeps_obsidian_as_intake() -> None:
    doc = read_doc("docs/KNOWLEDGE_INTAKE.md")

    assert "Obsidian" in doc
    assert "intake" in doc
    assert "raw chat log" in doc
    assert "registry/local-learnings.yaml" in doc


def test_concept_coverage_tracks_required_gaps() -> None:
    doc = read_doc("docs/CONCEPT_COVERAGE.md")

    required_concepts = [
        "Local SSOT",
        "ADR",
        "Reinvention avoidance",
        "Research / GitHub method",
        "TDD / regression",
        "GitHub identity gate",
        "Runtime skill",
        "Operation guarantee",
    ]

    for concept in required_concepts:
        assert concept in doc

    assert "devbrain run" in doc
    assert "registry/local-learnings.yaml" in doc


def test_next_goal_design_defines_run_packet_sequence() -> None:
    doc = read_doc("docs/NEXT_GOAL_DESIGN.md")

    assert "run packet" in doc
    assert "reinvention_check" in doc
    assert "research packet" in doc
    assert "registry/local-learnings.yaml" in doc
    assert "PR packet generator" in doc
    assert "candidate gate is advisory" in doc


def test_community_learning_intake_keeps_external_sources_as_candidates() -> None:
    doc = read_doc("docs/COMMUNITY_LEARNING_INTAKE.md")

    for source in ["vision", "memory", "github", "x", "web", "official"]:
        assert source in doc

    assert "source pointer" in doc
    assert "raw source" in doc
    assert "hold" in doc
    assert "adopt" in doc
    assert "external write" in doc


def test_field_review_loop_requires_local_trial_and_human_review() -> None:
    doc = read_doc("docs/FIELD_REVIEW_LOOP.md")

    for term in [
        "browser discovery",
        "Obsidian capture",
        "candidate packet",
        "local experiment plan",
        "local trial",
        "human field review",
        "adopt|hold|reject",
    ]:
        assert term in doc

    assert "raw dump" in doc
    assert "external write" in doc
    assert "production mutation" in doc


def test_pdca_feedback_loop_connects_execution_back_to_repo() -> None:
    doc = read_doc("docs/PDCA_FEEDBACK_LOOP.md")

    for term in ["Plan", "Do", "Check", "Act", "next Plan"]:
        assert term in doc

    for target in ["docs", "registry", "tests", "ADR", "skill"]:
        assert target in doc

    assert "human field review" in doc
    assert "expected effect" in doc
    assert "local-learnings.yaml" in doc
    assert "Check なしに Act しない" in doc


def test_legacy_dev_brain_absorption_blocks_lossy_cleanup() -> None:
    doc = read_doc("docs/LEGACY_DEV_BRAIN_ABSORPTION.md")
    migration = read_doc("docs/MIGRATION_NOTES.md")

    for term in [
        "local-only commits",
        "approval-gated lifecycle runner",
        "current live surface",
        "target candidate",
        "Delete gate",
    ]:
        assert term in doc

    assert "LEGACY_DEV_BRAIN_ABSORPTION.md" in migration


def test_engineering_autopilot_repo_owned_skill_exists() -> None:
    skill = read_doc("skills/engineering-autopilot/SKILL.md")
    lifecycle = read_doc("skills/engineering-autopilot/references/lifecycle.md")
    roadmap = read_doc("skills/engineering-autopilot/references/roadmap.md")
    docs_roadmap = read_doc("docs/ROADMAP.md")
    coverage = read_doc("docs/CONCEPT_COVERAGE.md")

    assert "薄い入口" in skill
    assert "python -m devbrain closeout --repo . --json" in skill
    assert "runtime install copy" in roadmap
    assert "human stopline" in lifecycle
    assert "skills/engineering-autopilot/" in docs_roadmap
    assert "repo-owned source" in coverage
