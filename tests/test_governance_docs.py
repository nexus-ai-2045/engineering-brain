from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_adr_index_and_first_decision_exist() -> None:
    index = read_doc("docs/adr/README.md")
    adr = read_doc("docs/adr/ADR-0001-engineering-brain-private-knowledge-repo.md")
    workspace_entrypoint = read_doc("Documents/decisions/README.md")

    assert "ADR-0001" in index
    assert "engineering-brain" in adr
    assert "private executable SSOT" in adr
    assert "Obsidian" in adr
    assert "Human Review Gate" in adr
    assert "docs/adr/" in workspace_entrypoint
    assert "正本" in workspace_entrypoint
    assert "複製せず" in workspace_entrypoint
    assert "ADR-0005" in workspace_entrypoint
    assert "ADR-0005-precedent-research-consumer-contract.md" in workspace_entrypoint
    assert "ADR-0006" in workspace_entrypoint
    assert "ADR-0006-verification-profile-closeout-v2.md" in workspace_entrypoint


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

    assert "engineering_brain run" in doc
    assert "registry/local-learnings.yaml" in doc


def test_next_goal_design_defines_run_packet_sequence() -> None:
    doc = read_doc("docs/NEXT_GOAL_DESIGN.md")

    assert "run packet" in doc
    assert "reinvention_check" in doc
    assert "research packet" in doc
    assert "registry/local-learnings.yaml" in doc
    assert "PR packet generator" in doc
    assert "candidate gate is advisory" in doc


def test_readme_visualizes_full_human_gated_lifecycle() -> None:
    readme = read_doc("README.md")

    assert "`engineering-brain`" in readme
    assert "`engineering-autopilot`" in readme
    assert "`engineering_brain`" in readme
    assert "Python module 名" in readme

    for label in (
        "1. 設計",
        "2. リサーチ",
        "3. TDD計画",
        "4. 実装",
        "5. テスト",
        "6. 運用保証",
        "7. PR準備・作成",
        "8. 人間目視レビュー",
        "9. マージ",
        "10. 後片付け",
    ):
        assert label in readme
    assert 'H -->|"修正が必要"| C' in readme
    assert "current conversation の人間承認" in readme


def test_local_ssot_reflects_public_repo_and_deleted_legacy_runtime() -> None:
    doc = read_doc("docs/LOCAL_SSOT.md")

    assert "public GitHub review / distribution surface" in doc
    assert "deleted legacy runtime install copy" in doc
    assert "完了済み cutover の記録" in doc
    assert "Legacy `dev-brain` repo、stale clone、runtime skill copy は削除済み" in doc
    assert "visibility: public" in doc
    assert "repo_class: own_public" in doc
    assert "visibility: private" not in doc
    assert "private GitHub mirror / review surface" not in doc
    assert "将来の cutover 候補" not in doc
    assert "target candidate" not in doc
    assert "`Documents/repos/second-brain/dev-brain` | `Documents/repos/engineering/engineering-brain`" not in doc
    assert "identity probe と PR readiness preflight" in doc
    assert "active `gh` login が `nexus-ai-2045` 以外" in doc
    assert "gh auth switch --hostname github.com --user nexus-ai-2045" in doc
    assert "auth / credential state 変更" in doc


def test_concept_coverage_tracks_post_public_seed_reality() -> None:
    doc = read_doc("docs/CONCEPT_COVERAGE.md")

    assert "Public GitHub surface" in doc
    assert "engineering_brain research" in doc
    assert "engineering_brain finish" in doc
    assert "engineering_brain pr" in doc
    assert "PR packet generator は未実装" not in doc


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
    assert "python -m engineering_brain closeout --repo . --json" in skill
    assert "runtime install copy" in roadmap
    assert "human stopline" in lifecycle
    assert "skills/engineering-autopilot/" in docs_roadmap
    assert "repo-owned source" in coverage


def test_single_skill_entrypoint_decision_and_capability_preflight_are_documented() -> None:
    skill = read_doc("skills/engineering-autopilot/SKILL.md")
    adr_index = read_doc("docs/adr/README.md")
    adr = read_doc("docs/adr/ADR-0002-single-autopilot-entrypoint.md")

    assert "engineering-brain`という別skillは作らない" in skill
    assert "利用可能commandを実測" in skill
    assert "未確認のcommandを推測実行しない" in skill
    assert "ADR-0002" in adr_index
    assert "single runtime skill entrypoint" in adr
    assert "engineering-autopilot" in adr
    assert "engineering-brain" in adr
    assert "engineering_brain" in adr


def test_current_entrypoints_do_not_reintroduce_dev_brain_branding() -> None:
    issue_template = read_doc(".github/ISSUE_TEMPLATE/research-intake.yml")
    autopilot_design = read_doc("docs/AUTOPILOT_GOAL_DESIGN.md")
    gitignore = read_doc(".gitignore")

    assert "engineering-brain の source catalog" in issue_template
    assert "dev-brain の source catalog" not in issue_template
    assert "互換入口と rollback を残す" not in autopilot_design
    assert ".codex/" in gitignore


def test_public_release_review_packet_names_exact_stopline() -> None:
    public_ready = read_doc("PUBLIC_READY.md")
    packet = read_doc("docs/PUBLIC_RELEASE_REVIEW_PACKET.md")
    license_text = read_doc("LICENSE")

    assert "status: public" in public_ready
    assert "gh repo edit nexus-ai-2045/engineering-brain --visibility public --accept-visibility-change-consequences" in public_ready
    assert "current conversation" in public_ready
    assert "status: public" in packet
    assert "GitHub visibility 変更は実行済み" in packet
    assert "MIT License" in license_text
