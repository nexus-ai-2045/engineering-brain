from __future__ import annotations

import json
from pathlib import Path

import engineering_brain.review as review
from engineering_brain.cli import main
from engineering_brain.path_safety import redact_personal_paths
from engineering_brain.review import build_pr_packet, render_pr_body_ja


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "pr-packet.schema.json").read_text(encoding="utf-8"))


def test_pr_packet_shape_matches_schema(monkeypatch) -> None:
    jsonschema = __import__("jsonschema")

    monkeypatch.setattr(
        review,
        "closeout_repo",
        lambda repo: {"overall": "ok", "verification": {"status": "ok"}},
    )
    monkeypatch.setattr(review, "scan_personal_paths", lambda repo: [])
    monkeypatch.setattr(review, "detect_default_branch", lambda repo: "main")
    monkeypatch.setattr(
        review,
        "collect_visible_scope",
        lambda repo, *, base_branch: {
            "source": "diff:main...HEAD",
            "files": [{"status": "A", "path": "engineering_brain/review.py"}],
            "summary": "1 file changed",
            "file_count": 1,
        },
    )
    monkeypatch.setattr(review, "_current_branch", lambda repo: "cursor/pr-packet-generator-4d46")

    packet = build_pr_packet(
        repo=ROOT,
        purpose="PR packet generator を追加する",
        closeout=True,
        research_packet={
            "task": "PR packet",
            "decision": {"status": "extend", "rationale": "reuse closeout helpers"},
        },
    )

    jsonschema.validate(instance=packet, schema=SCHEMA)
    assert packet["packet_type"] == "engineering_brain_pr"
    assert packet["repo"] == "<REPO>"
    assert packet["status"] == "plan_only"
    assert packet["merge"]["status"] == "承認待ち"
    assert packet["merge"]["allowed"] is False
    assert packet["external_actions"]["performed"] is False
    assert "pr_create" in packet["human_stoplines"]
    assert packet["reinvention_check"]["decision"] == "extend"


def test_pr_body_contains_japanese_sections() -> None:
    packet = {
        "purpose": "日本語 PR body を生成する",
        "changes": [{"status": "A", "path": "engineering_brain/review.py"}],
        "reinvention_check": {"decision": "extend", "reason": "reuse closeout"},
        "checks": {
            "closeout": {"overall": "ok"},
            "public_path_redaction": {"status": "ok"},
        },
        "visible_scope": {
            "source": "diff:main...HEAD",
            "summary": "1 file changed",
            "file_count": 1,
        },
        "unknowns": ["research / reinvention evidence 未添付"],
        "human_stoplines": ["push", "pr_create", "merge"],
        "merge": {"status": "承認待ち"},
        "external_actions": {"performed": False},
    }

    body = render_pr_body_ja(packet)

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


def test_pr_packet_redacts_personal_paths(monkeypatch) -> None:
    personal = "/Users/" + "alice" + "/Projects/demo/file.py"
    monkeypatch.setattr(
        review,
        "closeout_repo",
        lambda repo: {"overall": "ok"},
    )
    monkeypatch.setattr(review, "scan_personal_paths", lambda repo: [])
    monkeypatch.setattr(review, "detect_default_branch", lambda repo: "main")
    monkeypatch.setattr(
        review,
        "collect_visible_scope",
        lambda repo, *, base_branch: {
            "source": "diff:main...HEAD",
            "files": [{"status": "M", "path": redact_personal_paths(personal)}],
            "summary": redact_personal_paths(f"modified {personal}"),
            "file_count": 1,
        },
    )
    monkeypatch.setattr(review, "_current_branch", lambda repo: "feature")

    packet = build_pr_packet(
        repo=ROOT,
        purpose=f"touch {personal}",
        closeout=True,
        run_packet={"task": f"edit {personal}", "repo": personal},
    )

    blob = json.dumps(packet, ensure_ascii=False)
    assert "/Users/" + "alice" not in blob
    assert "alice" not in blob
    assert packet["run_packet"]["repo"].startswith("<USER_HOME>")
    assert "<USER_HOME>" in packet["purpose"]


def test_cli_pr_is_plan_only_and_does_not_mutate_github(capsys, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path) -> dict:
        calls.append(command)
        joined = " ".join(command)
        if joined.startswith("git rev-parse --verify"):
            return {"command": joined, "returncode": 0 if "main" in joined else 1, "stdout": "abc", "stderr": ""}
        if joined == "git branch --show-current":
            return {"command": joined, "returncode": 0, "stdout": "feature", "stderr": ""}
        if "git diff" in joined or joined == "git status --short":
            return {"command": joined, "returncode": 0, "stdout": "A\tengineering_brain/review.py", "stderr": ""}
        return {"command": joined, "returncode": 0, "stdout": "", "stderr": ""}

    monkeypatch.setattr(review, "run", fake_run)
    monkeypatch.setattr(
        review,
        "closeout_repo",
        lambda repo: {"overall": "ok", "verification": {"status": "ok"}},
    )
    monkeypatch.setattr(review, "scan_personal_paths", lambda repo: [])

    code = main(["pr", "--repo", str(ROOT), "--purpose", "PR packet", "--json", "--no-closeout"])

    assert code == 0
    output = capsys.readouterr().out
    packet = json.loads(output)
    assert packet["external_actions"]["performed"] is False
    assert packet["external_actions"]["allowed"] is False
    assert packet["status"] == "plan_only"
    assert not any(cmd and cmd[0] in {"gh", "hub"} for cmd in calls)
    assert not any("push" in " ".join(cmd) for cmd in calls)
    assert "## 目的" in packet["pr_body_ja"]


def test_cli_pr_text_mode_prints_japanese_body(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        review,
        "build_pr_packet",
        lambda **_: {
            "pr_body_ja": "## 目的\n\nテスト\n",
            "external_actions": {"performed": False},
        },
    )

    code = main(["pr", "--repo", str(ROOT), "--no-closeout"])

    assert code == 0
    assert "## 目的" in capsys.readouterr().out


def test_redact_personal_paths_helper() -> None:
    raw = "see " + "/home/" + "bob" + "/work/repo"
    assert redact_personal_paths(raw) == "see <USER_HOME>/work/repo"


def test_parse_status_line_survives_stripped_leading_space() -> None:
    assert review._parse_status_line("M CHANGELOG.md") == ("M", "CHANGELOG.md")
    assert review._parse_status_line(" M README.md") == ("M", "README.md")
    assert review._parse_status_line("?? engineering_brain/review.py") == (
        "??",
        "engineering_brain/review.py",
    )
