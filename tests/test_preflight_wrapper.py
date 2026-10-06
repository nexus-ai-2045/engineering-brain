from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location(
    "preflight_wrapper", Path(__file__).resolve().parents[1] / "tools" / "run_repo_preflight.py"
)
assert SPEC and SPEC.loader
wrapper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wrapper)


def invoke(monkeypatch, tmp_path, scan, consistency, *, args=(), scan_rc=0, consistency_rc=0):
    calls = []
    replies = iter([(scan, scan_rc), (consistency, consistency_rc)])
    monkeypatch.setattr(wrapper, "ensure_checkout", lambda cache: None)

    def run(command, **kwargs):
        calls.append(command)
        payload, code = next(replies)
        stdout = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
        return subprocess.CompletedProcess(command, code, stdout, "")

    monkeypatch.setattr(wrapper.subprocess, "run", run)
    code = wrapper.main(["--repo", str(tmp_path), *args])
    return code, calls


def test_default_passes_scoped_read_only_intent_and_parses_pretty_json(monkeypatch, tmp_path, capsys):
    code, calls = invoke(
        monkeypatch, tmp_path,
        {"status": "ready_after_confirmation"}, {"status": "pass", "mode": "shadow"},
    )
    assert code == 0
    assert calls[0][calls[0].index("--intent") + 1] == "open_pr"
    assert calls[0][calls[0].index("--base-ref") + 1] == "origin/main"
    summary = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert summary["status"] == "pass"
    assert summary["mode"] == "shadow"
    assert summary["publication_decision"] == "blocked_human_review_required"


@pytest.mark.parametrize("intent", ["publish", "release"])
def test_repository_intents_use_consistency_base(monkeypatch, tmp_path, intent):
    _, calls = invoke(monkeypatch, tmp_path, {"status": "ready_after_confirmation"},
                      {"status": "pass", "mode": "shadow"}, args=("--intent", intent))
    assert "--base-ref" not in calls[0]
    assert calls[0][calls[0].index("--consistency-base-ref") + 1] == "origin/main"


@pytest.mark.parametrize("scan,scan_rc,consistency,consistency_rc,expected", [
    ({"status": "needs_human_input"}, 1, {"status": "pass", "mode": "shadow"}, 0, 1),
    ({"status": "blocked"}, 1, {"status": "pass", "mode": "shadow"}, 0, 1),
    ({"status": "blocked", "scan": {"status": "tool_error"}}, 1, {"status": "pass", "mode": "shadow"}, 0, 2),
    ({"status": "tool_error"}, 2, {"status": "pass", "mode": "shadow"}, 0, 2),
    ({"status": "pass"}, 0, {"status": "tool_error", "mode": None}, 1, 2),
    ({"status": "pass"}, 0, {"status": "blocked", "mode": "enforce"}, 1, 1),
    ({"status": "pass"}, 0, {"status": "shadow_findings", "mode": "shadow"}, 1, 1),
    ({"status": "pass"}, 0, {"status": "fail", "mode": "enforce"}, 1, 1),
    ({"status": "blocked", "scan": {"status": []}}, 1, {"status": "pass", "mode": "shadow"}, 0, 2),
    ({"status": "pass"}, 1, {"status": "pass", "mode": "shadow"}, 0, 1),
    ({"status": "pass"}, -9, {"status": "pass", "mode": "shadow"}, 0, 2),
    ("", 0, {"status": "pass", "mode": "shadow"}, 0, 2),
    ({"status": "pass"}, 0, "not-json", 0, 2),
    ({"status": "pass"}, 0, "[]", 0, 2),
    ({"status": "pass"}, 0, {}, 0, 2),
    ({"status": "new_unknown_state"}, 0, {"status": "pass", "mode": "shadow"}, 0, 2),
])
def test_non_success_never_becomes_exit_zero(
    monkeypatch, tmp_path, capsys, scan, scan_rc, consistency, consistency_rc, expected
):
    code, _ = invoke(monkeypatch, tmp_path, scan, consistency,
                     scan_rc=scan_rc, consistency_rc=consistency_rc)
    assert code == expected
    summary = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert summary["status"] == ("tool_error" if expected == 2 else "blocked")


@pytest.mark.parametrize("intent", ["create_repo", "configure_settings"])
def test_other_intents_do_not_receive_invalid_scan_base(monkeypatch, tmp_path, intent):
    _, calls = invoke(monkeypatch, tmp_path, {"status": "ready_after_confirmation"},
                      {"status": "not_configured", "mode": None}, args=("--intent", intent))
    assert "--base-ref" not in calls[0]
    assert "--consistency-base-ref" not in calls[0]


def test_not_configured_is_a_valid_upstream_success(monkeypatch, tmp_path):
    code, _ = invoke(monkeypatch, tmp_path, {"status": "ready_after_confirmation"},
                     {"status": "not_configured", "mode": None})
    assert code == 0
