import json
from pathlib import Path

from jsonschema import Draft202012Validator

from engineering_brain.cli import main
from engineering_brain.research import build_research_packet


ROOT = Path(__file__).resolve().parents[1]


def test_research_packet_keeps_catalog_sources_as_candidates() -> None:
    packet = build_research_packet(
        task="choose a Python test approach",
        domain="python",
        decision="hold",
        rationale="upstream maintenance evidence is not attached",
    )

    assert packet["packet_type"] == "engineering_brain_research"
    assert packet["version"] == 2
    assert packet["task"] == "choose a Python test approach"
    assert packet["decision"]["status"] == "hold"
    assert packet["candidates"]
    assert all(candidate["status"] == "candidate" for candidate in packet["candidates"])
    assert packet["precedent_research"] == {
        "skill": "implementation-precedent-research",
        "source_owner": "nexus-ai-skills",
        "role": "consumer",
        "required_before": ["wrap", "extend", "adopt_oss", "build"],
        "decision_contract": ["adopt", "revise", "reject", "hold"],
        "outcome": None,
        "evidence": [],
    }
    assert "adopt" in packet["human_stoplines"]


def test_research_packet_rejects_unsupported_decision() -> None:
    try:
        build_research_packet(task="x", domain="python", decision="ship", rationale="x")
    except ValueError as error:
        assert "decision" in str(error)
    else:
        raise AssertionError("unsupported decision must fail")


def test_cli_research_emits_json(capfd) -> None:
    code = main([
        "research",
        "--task", "choose a Python test approach",
        "--domain", "python",
        "--decision", "hold",
        "--rationale", "needs review",
        "--json",
    ])

    assert code == 0
    packet = json.loads(capfd.readouterr().out)
    assert packet["packet_type"] == "engineering_brain_research"
    assert packet["decision"]["status"] == "hold"
    assert packet["repo"] == "<REPO>"


def test_research_schema_declares_decision_enum() -> None:
    schema = json.loads((ROOT / "schemas" / "research-packet.schema.json").read_text(encoding="utf-8"))

    assert schema["properties"]["decision"]["properties"]["status"]["enum"] == [
        "reuse", "wrap", "extend", "adopt_oss", "build", "hold", "rejected"
    ]
    assert schema["properties"]["version"]["const"] == 2
    assert "precedent_research" in schema["required"]


def test_engineering_autopilot_routes_precedent_research_without_copying_it() -> None:
    skill = (ROOT / "skills" / "engineering-autopilot" / "SKILL.md").read_text(encoding="utf-8")
    lifecycle = (
        ROOT / "skills" / "engineering-autopilot" / "references" / "lifecycle.md"
    ).read_text(encoding="utf-8")

    assert "$implementation-precedent-research" in skill
    assert "nexus-ai-skills" in skill
    assert "本体を複製しない" in skill
    assert "precedent research" in lifecycle


def test_build_forces_hold_when_precedent_required_without_outcome_or_evidence() -> None:
    for decision in ("wrap", "extend", "adopt_oss", "build"):
        packet = build_research_packet(
            task="choose approach",
            domain="python",
            decision=decision,
            rationale="rationale alone must not complete the packet",
        )
        assert packet["decision"]["status"] == "hold"
        assert any("precedent research" in item for item in packet["unknowns"])


def test_build_allows_gated_decision_with_precedent_outcome_and_evidence() -> None:
    packet = build_research_packet(
        task="choose approach",
        domain="python",
        decision="build",
        rationale="local fit confirmed after precedent research",
        precedent_outcome="adopt",
        precedent_evidence=["docs/adr/ADR-0005-precedent-research-consumer-contract.md"],
    )

    assert packet["decision"]["status"] == "build"
    assert packet["precedent_research"]["outcome"] == "adopt"
    assert packet["precedent_research"]["evidence"] == [
        "docs/adr/ADR-0005-precedent-research-consumer-contract.md"
    ]
    assert packet["unknowns"] == []


def test_build_forces_hold_when_precedent_outcome_is_hold_or_reject() -> None:
    for outcome in ("hold", "reject"):
        packet = build_research_packet(
            task="choose approach",
            domain="python",
            decision="extend",
            rationale="skill ran but did not adopt",
            precedent_outcome=outcome,
            precedent_evidence=["skills/engineering-autopilot/references/lifecycle.md"],
        )
        assert packet["decision"]["status"] == "hold"
        assert any(outcome in item for item in packet["unknowns"])


def test_cli_research_forces_hold_without_precedent_gate(capfd) -> None:
    code = main([
        "research",
        "--task", "choose approach",
        "--domain", "python",
        "--decision", "wrap",
        "--rationale", "rationale alone is insufficient",
        "--json",
    ])

    assert code == 0
    packet = json.loads(capfd.readouterr().out)
    assert packet["decision"]["status"] == "hold"
    assert any("precedent research" in item for item in packet["unknowns"])


def test_cli_research_emits_gated_decision_with_precedent_inputs(capfd) -> None:
    code = main([
        "research",
        "--task", "choose approach",
        "--domain", "python",
        "--decision", "adopt_oss",
        "--rationale", "precedent adopt with evidence",
        "--precedent-outcome", "revise",
        "--precedent-evidence", "https://example.invalid/precedent",
        "--json",
    ])

    assert code == 0
    packet = json.loads(capfd.readouterr().out)
    assert packet["decision"]["status"] == "adopt_oss"
    assert packet["precedent_research"]["outcome"] == "revise"
    assert packet["precedent_research"]["evidence"] == [
        "https://example.invalid/precedent"
    ]
    assert packet["unknowns"] == []


def test_research_schema_requires_full_contract_arrays() -> None:
    schema = json.loads((ROOT / "schemas" / "research-packet.schema.json").read_text(encoding="utf-8"))
    precedent = schema["properties"]["precedent_research"]["properties"]
    assert precedent["required_before"]["minItems"] == 4
    assert precedent["decision_contract"]["minItems"] == 4

    packet = build_research_packet(
        task="choose approach",
        domain="python",
        decision="hold",
        rationale="schema check",
    )
    Draft202012Validator(schema).validate(packet)

    for field in ("required_before", "decision_contract"):
        broken = json.loads(json.dumps(packet))
        broken["precedent_research"][field] = []
        errors = list(Draft202012Validator(schema).iter_errors(broken))
        assert any(error.validator == "minItems" for error in errors)

        short = json.loads(json.dumps(packet))
        short["precedent_research"][field] = short["precedent_research"][field][:1]
        errors = list(Draft202012Validator(schema).iter_errors(short))
        assert any(error.validator == "minItems" for error in errors)
