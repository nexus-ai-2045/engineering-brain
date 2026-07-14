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

