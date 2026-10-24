from __future__ import annotations

import json

from engineering_brain.review import public_stdout_packet


def _slash() -> str:
    return chr(47)


def _public_packet(**overrides):
    packet = {
        "packet_type": "engineering_brain_pr",
        "version": 1,
        "repo": "<REPO>",
        "status": "plan_only",
        "purpose": "inferred purpose",
        "base_branch": "main",
        "current_branch": "feature",
        "visible_scope": {"source": "worktree", "files": [], "summary": "", "file_count": 0},
        "changes": [],
        "checks": {
            "closeout": {"overall": "ok"},
            "public_path_redaction": {"status": "ok"},
            "attachment_validation": {
                "run_packet": "missing",
                "research_packet": "ok",
                "run_errors": [],
                "research_errors": [],
            },
        },
        "run_packet": None,
        "research_packet": {
            "packet_type": "engineering_brain_research",
            "decision": {"status": "hold"},
        },
        "reinvention_check": {"required": True, "decision": "hold", "reason": "research packet attached"},
        "unknowns": [],
        "human_stoplines": ["merge"],
        "merge": {"status": "承認待ち", "allowed": False},
        "external_actions": {"allowed": False, "performed": False},
        "pr_body_ja": "",
    }
    packet.update(overrides)
    return packet


def test_public_stdout_preserves_verification_profiles_and_summary() -> None:
    public = public_stdout_packet(
        _public_packet(
            checks={
                "closeout": {
                    "overall": "ok",
                    "verification": {
                        "status": "ok",
                        "schema_version": 2,
                        "summary": {
                            "pass": 2,
                            "fail": 0,
                            "not_run": 0,
                            "not_applicable": 3,
                        },
                        "selected_profiles": [
                            {"id": "python_unit", "layer": "unit", "status": "adopted"},
                            {"id": "python_smoke_cli", "layer": "smoke"},
                        ],
                        "pytest": {
                            "command": "python -m pytest -q --basetemp <TEMP>",
                            "returncode": 0,
                            "stdout": "secret-should-not-leak",
                        },
                        "compileall": {
                            "command": "python -m py_compile <tracked *.py>",
                            "returncode": 0,
                        },
                    },
                },
                "public_path_redaction": {"status": "ok"},
                "attachment_validation": {
                    "run_packet": "missing",
                    "research_packet": "ok",
                    "run_errors": [],
                    "research_errors": [],
                },
            }
        )
    )

    verification = public["checks"]["closeout"]["verification"]
    assert verification["summary"]["not_applicable"] == 3
    assert [item["id"] for item in verification["selected_profiles"]] == [
        "python_unit",
        "python_smoke_cli",
    ]
    assert "stdout" not in (verification.get("pytest") or {})
    body = public["pr_body_ja"]
    assert "evidence summary: pass=2, fail=0, not_run=0, not_applicable=3" in body
    assert "verification profiles: `python_unit, python_smoke_cli`" in body

    public = public_stdout_packet(
        _public_packet(
            unknowns=[
                "decision rationale is not recorded",
                "license is unclear",
            ]
        )
    )

    assert "decision rationale is not recorded" in public["unknowns"]
    assert "license is unclear" in public["unknowns"]
    assert "license is unclear" in public["pr_body_ja"]
    assert "（なし）" not in public["pr_body_ja"]


def test_public_stdout_scrubs_secret_like_unknowns() -> None:
    token = "ghp_" + ("d" * 36)
    public = public_stdout_packet(_public_packet(unknowns=[f"research leftover {token}"]))

    blob = json.dumps(public, ensure_ascii=False)
    assert token not in blob
    assert "<REDACTED_SECRET>" in blob
    assert any("research leftover" in item for item in public["unknowns"])


def test_public_stdout_keeps_inferred_purpose_when_override_blank() -> None:
    packet = _public_packet(purpose="inferred <USER_HOME> task")

    assert public_stdout_packet(packet)["purpose"] == "inferred <USER_HOME> task"
    assert public_stdout_packet(packet, purpose_override="")["purpose"] == (
        "inferred <USER_HOME> task"
    )
    assert "inferred <USER_HOME> task" in public_stdout_packet(
        packet, purpose_override=""
    )["pr_body_ja"]


def test_public_stdout_redacts_purpose_override() -> None:
    personal = _slash() + "Users" + _slash() + "alice" + _slash() + "secret-work"
    token = "ghp_" + ("e" * 36)
    public = public_stdout_packet(
        _public_packet(purpose="safe"),
        purpose_override=f"touch {personal} with {token}",
    )

    blob = json.dumps(public, ensure_ascii=False)
    assert "alice" not in blob
    assert token not in blob
    assert "<USER_HOME>" in public["purpose"]
    assert "<REDACTED_SECRET>" in public["purpose"]
