from pathlib import Path

import devbrain.run_packet as run_packet
from devbrain.cli import main
from devbrain.run_packet import build_run_packet


ROOT = Path(__file__).resolve().parents[1]


def test_build_run_packet_combines_route_gates_catalog_skill_sync_and_closeout() -> None:
    packet = build_run_packet(
        task="implement small python CLI feature and prepare PR",
        repo=ROOT,
        domain="python",
        closeout=False,
    )

    assert packet["packet_type"] == "engineering_autopilot_run"
    assert packet["task"] == "implement small python CLI feature and prepare PR"
    assert packet["status"] == "blocked_until_human_review"
    assert packet["route"]["mode"] == "implement"
    assert "human_publication_review_gate" in packet["route"]["selected_units"]
    assert packet["gates"]["overall"] == "blocked"
    assert packet["catalog"]["domain"] == "python"
    assert packet["catalog"]["sources"]
    assert packet["skill_sync"]["status"] == "ok"
    assert packet["closeout"]["status"] == "skipped"
    assert "push" in packet["human_stoplines"]
    assert "pr_create" in packet["human_stoplines"]
    assert packet["next_actions"][0] == "review run packet"


def test_build_run_packet_can_include_closeout(monkeypatch) -> None:
    def fake_closeout(repo: Path) -> dict:
        return {"overall": "ok", "implementation": {"repo": "<REPO>"}}

    monkeypatch.setattr(run_packet, "closeout_repo", fake_closeout)

    packet = build_run_packet(
        task="review current engineering-brain status",
        repo=ROOT,
        domain=None,
        closeout=True,
    )

    assert packet["closeout"]["overall"] == "ok"
    assert packet["verification"]["closeout_status"] == "ok"


def test_cli_run_emits_json_packet(capsys) -> None:
    code = main(["run", "--task", "implement CLI run packet", "--repo", str(ROOT), "--domain", "python", "--json"])

    assert code == 0
    output = capsys.readouterr().out
    assert '"packet_type": "engineering_autopilot_run"' in output
    assert '"task": "implement CLI run packet"' in output
    assert '"skill_sync"' in output
