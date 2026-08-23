from pathlib import Path

import engineering_brain.run_packet as run_packet
from engineering_brain.cli import main
from engineering_brain.run_packet import build_run_packet


ROOT = Path(__file__).resolve().parents[1]


def test_build_run_packet_combines_route_gates_catalog_skill_sync_and_closeout(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        run_packet,
        "compare_skill_targets",
        lambda **_: {
            "status": "ok",
            "targets": [
                {"runtime": "codex", "status": "ok"},
                {"runtime": "claude-code", "status": "ok"},
            ],
        },
    )

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
    assert packet["algorithms"]["selection"] == []
    assert packet["algorithms"]["unknown_rule"]
    assert packet["skill_sync"]["status"] == "ok"
    assert [target["runtime"] for target in packet["skill_sync"]["targets"]] == [
        "codex",
        "claude-code",
    ]
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


def test_build_run_packet_reports_claude_runtime_drift(monkeypatch) -> None:
    monkeypatch.setattr(
        run_packet,
        "compare_skill_targets",
        lambda **_: {
            "status": "action_required",
            "targets": [
                {"runtime": "codex", "status": "ok"},
                {"runtime": "claude-code", "status": "drift"},
            ],
        },
    )

    packet = build_run_packet(
        task="review runtime projections",
        repo=ROOT,
        domain=None,
        closeout=False,
    )

    assert packet["skill_sync"]["status"] == "action_required"
    assert packet["verification"]["skill_sync_status"] == "action_required"


def test_build_run_packet_selects_algorithms_from_task_signals() -> None:
    packet = build_run_packet(
        task="ソート済み配列を二分探索して ordered lookup を実装する",
        repo=ROOT,
        domain="python",
        closeout=False,
    )

    assert packet["algorithms"]["selection"][0]["id"] == "binary_search"
    assert "sorted_input" in packet["algorithms"]["signals"]


def test_cli_run_emits_json_packet(capfd) -> None:
    code = main(["run", "--task", "implement CLI run packet", "--repo", str(ROOT), "--domain", "python", "--json"])

    assert code == 0
    output = capfd.readouterr().out
    assert '"packet_type": "engineering_autopilot_run"' in output
    assert '"task": "implement CLI run packet"' in output
    assert '"skill_sync"' in output
