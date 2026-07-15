import json
from pathlib import Path

from devbrain.cli import main
from devbrain.research import build_research_packet


ROOT = Path(__file__).resolve().parents[1]


def test_research_packet_keeps_catalog_sources_as_candidates() -> None:
    packet = build_research_packet(
        task="choose a Python test approach",
        domain="python",
        decision="hold",
        rationale="upstream maintenance evidence is not attached",
    )

    assert packet["packet_type"] == "engineering_brain_research"
    assert packet["version"] == 1
    assert packet["task"] == "choose a Python test approach"
    assert packet["decision"]["status"] == "hold"
    assert packet["candidates"]
    assert all(candidate["status"] == "candidate" for candidate in packet["candidates"])
    assert "adopt" in packet["human_stoplines"]


def test_research_packet_rejects_unsupported_decision() -> None:
    try:
        build_research_packet(task="x", domain="python", decision="ship", rationale="x")
    except ValueError as error:
        assert "decision" in str(error)
    else:
        raise AssertionError("unsupported decision must fail")


def test_cli_research_emits_json(capsys) -> None:
    code = main([
        "research",
        "--task", "choose a Python test approach",
        "--domain", "python",
        "--decision", "hold",
        "--rationale", "needs review",
        "--json",
    ])

    assert code == 0
    packet = json.loads(capsys.readouterr().out)
    assert packet["packet_type"] == "engineering_brain_research"
    assert packet["decision"]["status"] == "hold"
    assert packet["repo"] == "<REPO>"


def test_research_schema_declares_decision_enum() -> None:
    schema = json.loads((ROOT / "schemas" / "research-packet.schema.json").read_text(encoding="utf-8"))

    assert schema["properties"]["decision"]["properties"]["status"]["enum"] == [
        "reuse", "wrap", "extend", "adopt_oss", "build", "hold", "rejected"
    ]
