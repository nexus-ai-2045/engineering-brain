from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import engineering_brain.review as review
from engineering_brain.cli import main
from engineering_brain.path_safety import redact_personal_paths
from engineering_brain.review import build_pr_packet, render_pr_body_ja


ROOT = Path(__file__).resolve().parents[1]


def _fake_closeout(_repo: Path) -> dict[str, Any]:
    return {
        "overall": "ok",
        "implementation": {"status": "present", "repo": "<REPO>"},
        "verification": {
            "status": "ok",
            "pytest": {"command": "python -m pytest -q", "returncode": 0, "stdout": "", "stderr": ""},
            "compileall": {"command": "python -m py_compile", "returncode": 0, "stdout": "", "stderr": ""},
        },
        "operation": {
            "status": "ok",
            "public_path_redaction": {"status": "ok", "findings": []},
        },
        "external_public": {
            "status": "blocked_until_human_approval",
            "actions_performed": False,
            "blocked_actions": ["push", "PR create"],
        },
    }


def test_build_pr_packet_shape_and_japanese_sections(monkeypatch) -> None:
    monkeypatch.setattr(review, "closeout_repo", _fake_closeout)

    def fake_run(command: list[str], *, cwd: Path) -> dict[str, Any]:
        joined = " ".join(command)
        if joined == "git status --short --branch":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "## feature/pr-packet...origin/feature/pr-packet",
                "stderr": "",
            }
        if joined == "git symbolic-ref refs/remotes/origin/HEAD":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "refs/remotes/origin/main",
                "stderr": "",
            }
        if joined == "git rev-parse --verify origin/main":
            return {"command": joined, "returncode": 0, "stdout": "abc", "stderr": ""}
        if joined.startswith("git diff --name-only "):
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "engineering_brain/review.py\nREADME.md",
                "stderr": "",
            }
        if joined.startswith("git diff --name-status "):
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "A\tengineering_brain/review.py\nM\tREADME.md",
                "stderr": "",
            }
        if joined.startswith("git diff --stat "):
            return {"command": joined, "returncode": 0, "stdout": " 2 files changed", "stderr": ""}
        if joined == "git diff --name-status":
            return {"command": joined, "returncode": 0, "stdout": "", "stderr": ""}
        if joined == "git diff --cached --name-status":
            return {"command": joined, "returncode": 0, "stdout": "", "stderr": ""}
        if joined == "git ls-files --others --exclude-standard":
            return {"command": joined, "returncode": 0, "stdout": "", "stderr": ""}
        raise AssertionError(f"unexpected command: {joined}")

    monkeypatch.setattr(review, "run", fake_run)

    packet = build_pr_packet(
        repo=ROOT,
        purpose="PR packet generator を追加する",
        closeout=True,
    )

    assert packet["packet_type"] == "engineering_brain_pr"
    assert packet["version"] == 1
    assert packet["repo"] == "<REPO>"
    assert packet["mode"] == "plan_only"
    assert packet["merge_status"] == "承認待ち"
    assert packet["external_actions"]["allowed"] is False
    assert packet["external_actions"]["actions_performed"] is False
    assert "pr_create" in packet["human_stoplines"]
    assert packet["checks"]["pytest"] == "ok"
    assert "engineering_brain/review.py" in packet["visible_scope"]["changed_files"]

    body = packet["pr_body_ja"]
    for heading in (
        "## 目的",
        "## 変更内容",
        "## Research / reinvention check",
        "## TDD / 検証",
        "## Security / operation",
        "## Visible scope",
        "## 未確認と残リスク",
        "## Human stoplines",
        "## Merge",
    ):
        assert heading in body
    assert "承認待ち" in body


def test_pr_packet_redacts_personal_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(review, "closeout_repo", _fake_closeout)
    personal = "/Users/" + "alice" + "/Projects/demo"

    def fake_run(command: list[str], *, cwd: Path) -> dict[str, Any]:
        joined = " ".join(command)
        if joined == "git status --short --branch":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": f"## main\n M {personal}/README.md",
                "stderr": "",
            }
        if "symbolic-ref" in joined or "rev-parse" in joined:
            return {"command": joined, "returncode": 1, "stdout": "", "stderr": ""}
        if joined in {
            "git diff --name-status",
            "git diff --cached --name-status",
            "git ls-files --others --exclude-standard",
        }:
            return {"command": joined, "returncode": 0, "stdout": "", "stderr": ""}
        raise AssertionError(f"unexpected command: {joined}")

    monkeypatch.setattr(review, "run", fake_run)

    packet = build_pr_packet(repo=tmp_path, purpose="redaction check", closeout=False)
    dumped = json.dumps(packet, ensure_ascii=False)

    assert "alice" not in dumped
    assert "/Users/" not in dumped
    assert "<USER_HOME>" in dumped or "uncommitted" in dumped.lower() or packet["unknowns"]


def test_redact_personal_paths_helper_replaces_home_and_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    sample = f"cwd={repo} home=" + "/home/" + "bob" + "/work"
    redacted = redact_personal_paths(sample, repo=repo)
    assert str(repo) not in redacted or "<REPO>" in redacted
    assert "bob" not in redacted
    assert "<USER_HOME>" in redacted


def test_cli_pr_emits_json_without_github_mutation(capsys, monkeypatch) -> None:
    calls: list[str] = []

    def fake_build(**kwargs):
        calls.append("build")
        return {
            "packet_type": "engineering_brain_pr",
            "version": 1,
            "repo": "<REPO>",
            "mode": "plan_only",
            "status": "awaiting_human_approval",
            "merge_status": "承認待ち",
            "purpose": "x",
            "changes": [],
            "visible_scope": {},
            "checks": {},
            "unknowns": [],
            "human_stoplines": ["pr_create"],
            "external_actions": {
                "allowed": False,
                "actions_performed": False,
                "blocked_actions": ["github pr create"],
            },
            "pr_body_ja": "## 目的\n\nx\n",
        }

    monkeypatch.setattr("engineering_brain.cli.build_pr_packet", fake_build)

    code = main(["pr", "--repo", str(ROOT), "--json"])

    assert code == 0
    assert calls == ["build"]
    output = capsys.readouterr().out
    packet = json.loads(output)
    assert packet["packet_type"] == "engineering_brain_pr"
    assert packet["external_actions"]["actions_performed"] is False
    # CLI must not invoke gh / remote mutation helpers
    assert "gh " not in output


def test_cli_pr_body_only(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        "engineering_brain.cli.build_pr_packet",
        lambda **_: {
            "pr_body_ja": "## 目的\n\nbody only\n\n## Merge\n\n- 状態: **承認待ち**\n",
            "external_actions": {"allowed": False, "actions_performed": False},
        },
    )

    code = main(["pr", "--body-only"])

    assert code == 0
    out = capsys.readouterr().out
    assert "## 目的" in out
    assert "承認待ち" in out
    assert '"packet_type"' not in out


def test_pr_schema_matches_packet_contract() -> None:
    schema = json.loads((ROOT / "schemas" / "pr-packet.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["packet_type"]["const"] == "engineering_brain_pr"
    assert schema["properties"]["mode"]["const"] == "plan_only"
    assert schema["properties"]["merge_status"]["const"] == "承認待ち"
    assert schema["properties"]["external_actions"]["properties"]["allowed"]["const"] is False


def test_render_pr_body_includes_required_japanese_headings() -> None:
    body = render_pr_body_ja(
        {
            "purpose": "デモ",
            "changes": ["A\tfile.py"],
            "reinvention_check": {"decision": "reuse", "reason": "既存 closeout を再利用"},
            "checks": {
                "closeout_overall": "ok",
                "pytest": "ok",
                "compile": "ok",
                "public_path_redaction": "ok",
            },
            "visible_scope": {"base": "main", "head": "feature", "changed_files": ["file.py"]},
            "unknowns": ["research 未添付"],
            "human_stoplines": ["merge"],
            "merge_status": "承認待ち",
        }
    )
    assert "## Visible scope" in body
    assert "research 未添付" in body
