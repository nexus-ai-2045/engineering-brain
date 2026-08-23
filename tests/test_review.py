from __future__ import annotations

import json
from pathlib import Path

import engineering_brain.review as review
from engineering_brain.cli import main
from engineering_brain.path_safety import PERSONAL_PATH_PATTERN, redact_personal_paths
from engineering_brain.review import build_pr_packet, render_pr_body_ja


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "pr-packet.schema.json").read_text(encoding="utf-8"))


def _valid_research_packet(**overrides):
    packet = {
        "packet_type": "engineering_brain_research",
        "version": 2,
        "task": "PR packet",
        "repo": "<REPO>",
        "domain": "python",
        "candidates": [],
        "precedent_research": {
            "skill": "implementation-precedent-research",
            "source_owner": "nexus-ai-skills",
            "role": "consumer",
            "required_before": ["wrap", "extend", "adopt_oss", "build"],
            "decision_contract": ["adopt", "revise", "reject", "hold"],
            "outcome": "adopt",
            "evidence": ["engineering_brain/review.py"],
        },
        "decision": {
            "status": "extend",
            "rationale": "reuse closeout helpers",
            "rule": "catalog evidence remains candidate until adopted",
        },
        "human_stoplines": ["adopt", "push", "pr_create", "merge", "visibility_change"],
        "unknowns": [],
    }
    packet.update(overrides)
    return packet


def _valid_run_packet(**overrides):
    packet = {
        "packet_type": "engineering_autopilot_run",
        "version": 1,
        "task": "implement PR packet",
        "repo": "<REPO>",
        "status": "blocked_until_human_review",
        "route": {"mode": "implement"},
        "gates": {"overall": "ok"},
        "closeout": {"status": "skipped"},
        "human_stoplines": ["push", "pr_create", "merge"],
    }
    packet.update(overrides)
    return packet


def test_pr_packet_shape_matches_schema(monkeypatch) -> None:
    jsonschema = __import__("jsonschema")

    monkeypatch.setattr(
        review,
        "closeout_repo",
        lambda repo: {
            "overall": "ok",
            "verification": {
                "status": "ok",
                "pytest": {"command": "python -m pytest -q", "returncode": 0},
                "compileall": {
                    "command": "python -m py_compile engineering_brain/review.py",
                    "returncode": 0,
                },
            },
        },
    )
    monkeypatch.setattr(review, "scan_personal_paths", lambda repo: [])
    monkeypatch.setattr(review, "detect_default_branch", lambda repo: "origin/main")
    monkeypatch.setattr(
        review,
        "collect_visible_scope",
        lambda repo, *, base_branch: {
            "source": "diff:origin/main...HEAD",
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
        research_packet=_valid_research_packet(),
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
            "closeout": {
                "overall": "ok",
                "verification": {
                    "pytest": {"command": "python -m pytest -q", "returncode": 0},
                },
            },
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
    assert "`python -m pytest -q`" in body
    assert "compileall" not in body


def test_pr_packet_redacts_personal_paths(monkeypatch) -> None:
    personal = "/Users/" + "alice" + "/Projects/demo/file.py"
    monkeypatch.setattr(review, "closeout_repo", lambda repo: {"overall": "ok"})
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
        run_packet=_valid_run_packet(task=f"edit {personal}"),
    )

    blob = json.dumps(packet, ensure_ascii=False)
    assert "/Users/" + "alice" not in blob
    assert "alice" not in blob
    assert "<USER_HOME>" in packet["purpose"]


def test_pr_packet_scrubs_secret_like_content(monkeypatch) -> None:
    token = "ghp_" + ("a" * 36)
    monkeypatch.setattr(review, "closeout_repo", lambda repo: {"overall": "ok", "note": token})
    monkeypatch.setattr(review, "scan_personal_paths", lambda repo: [])
    monkeypatch.setattr(review, "detect_default_branch", lambda repo: "main")
    monkeypatch.setattr(
        review,
        "collect_visible_scope",
        lambda repo, *, base_branch: {
            "source": "diff:main...HEAD",
            "files": [],
            "summary": "",
            "file_count": 0,
        },
    )
    monkeypatch.setattr(review, "_current_branch", lambda repo: "feature")

    packet = build_pr_packet(
        repo=ROOT,
        purpose="secret scrub",
        closeout=True,
        research_packet=_valid_research_packet(
            decision={
                "status": "hold",
                "rationale": f"token {token}",
                "rule": "catalog evidence remains candidate until adopted",
            }
        ),
    )

    blob = json.dumps(packet, ensure_ascii=False)
    assert token not in blob
    assert "<REDACTED_SECRET>" in blob
    assert any("secret-like" in item for item in packet["unknowns"])


def test_invalid_research_packet_is_not_treated_as_evidence(monkeypatch) -> None:
    monkeypatch.setattr(review, "closeout_repo", lambda repo: {"overall": "ok"})
    monkeypatch.setattr(review, "scan_personal_paths", lambda repo: [])
    monkeypatch.setattr(review, "detect_default_branch", lambda repo: "main")
    monkeypatch.setattr(
        review,
        "collect_visible_scope",
        lambda repo, *, base_branch: {
            "source": "diff:main...HEAD",
            "files": [],
            "summary": "",
            "file_count": 0,
        },
    )
    monkeypatch.setattr(review, "_current_branch", lambda repo: "feature")

    packet = build_pr_packet(
        repo=ROOT,
        purpose="validate attachments",
        closeout=True,
        research_packet={"decision": {"status": "extend"}},
    )

    assert packet["research_packet"] is None
    assert packet["reinvention_check"]["decision"] == "hold"
    assert any("schema validation" in item for item in packet["unknowns"])


def test_research_unknowns_are_merged(monkeypatch) -> None:
    monkeypatch.setattr(review, "closeout_repo", lambda repo: {"overall": "ok"})
    monkeypatch.setattr(review, "scan_personal_paths", lambda repo: [])
    monkeypatch.setattr(review, "detect_default_branch", lambda repo: "main")
    monkeypatch.setattr(
        review,
        "collect_visible_scope",
        lambda repo, *, base_branch: {
            "source": "diff:main...HEAD",
            "files": [],
            "summary": "",
            "file_count": 0,
        },
    )
    monkeypatch.setattr(review, "_current_branch", lambda repo: "feature")

    packet = build_pr_packet(
        repo=ROOT,
        purpose="merge unknowns",
        closeout=True,
        research_packet=_valid_research_packet(
            decision={
                "status": "hold",
                "rationale": "",
                "rule": "catalog evidence remains candidate until adopted",
            },
            unknowns=["decision rationale is not recorded"],
        ),
    )

    assert "decision rationale is not recorded" in packet["unknowns"]
    assert "（なし）" not in packet["pr_body_ja"]


def test_detect_default_branch_uses_origin_head(monkeypatch) -> None:
    def fake_run(command: list[str], *, cwd: Path) -> dict:
        joined = " ".join(command)
        if joined == "git symbolic-ref --quiet refs/remotes/origin/HEAD":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "refs/remotes/origin/develop",
                "stderr": "",
            }
        raise AssertionError(joined)

    monkeypatch.setattr(review, "run", fake_run)
    assert review.detect_default_branch(Path(".")) == "origin/develop"


def test_detect_default_branch_falls_back_to_abbrev_ref(monkeypatch) -> None:
    def fake_run(command: list[str], *, cwd: Path) -> dict:
        joined = " ".join(command)
        if joined == "git symbolic-ref --quiet refs/remotes/origin/HEAD":
            return {"command": joined, "returncode": 1, "stdout": "", "stderr": ""}
        if joined == "git rev-parse --abbrev-ref origin/HEAD":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "origin/trunk",
                "stderr": "",
            }
        raise AssertionError(joined)

    monkeypatch.setattr(review, "run", fake_run)
    assert review.detect_default_branch(Path(".")) == "origin/trunk"


def test_parse_name_status_rename_and_copy() -> None:
    rename = review._parse_name_status_line("R100\told.py\tnew.py")
    assert rename == {
        "status": "R100",
        "old_path": "old.py",
        "new_path": "new.py",
        "path": "new.py",
    }
    copy = review._parse_name_status_line("C080\tsrc/a.py\tsrc/b.py")
    assert copy["old_path"] == "src/a.py"
    assert copy["new_path"] == "src/b.py"


def test_cli_pr_is_plan_only_and_does_not_mutate_github(capfd, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path) -> dict:
        calls.append(command)
        joined = " ".join(command)
        if joined == "git symbolic-ref --quiet refs/remotes/origin/HEAD":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "refs/remotes/origin/main",
                "stderr": "",
            }
        if joined == "git branch --show-current":
            return {"command": joined, "returncode": 0, "stdout": "feature", "stderr": ""}
        if "git diff" in joined or joined == "git status --short":
            return {
                "command": joined,
                "returncode": 0,
                "stdout": "A\tengineering_brain/review.py",
                "stderr": "",
            }
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
    output = capfd.readouterr().out
    packet = json.loads(output)
    assert packet["external_actions"]["performed"] is False
    assert packet["external_actions"]["allowed"] is False
    assert packet["status"] == "plan_only"
    assert not any(cmd and cmd[0] in {"gh", "hub"} for cmd in calls)
    assert not any("push" in " ".join(cmd) for cmd in calls)
    assert "## 目的" in packet["pr_body_ja"]
    assert "compileall" not in packet["pr_body_ja"]


def test_cli_pr_scrubs_secret_like_stdout(tmp_path: Path, capfd, monkeypatch) -> None:
    token = "ghp_" + ("b" * 36)
    research = {
        "packet_type": "engineering_brain_research",
        "version": 1,
        "task": "x",
        "repo": "<REPO>",
        "domain": "python",
        "candidates": [],
        "decision": {
            "status": "hold",
            "rationale": f"see {token}",
            "rule": "catalog evidence remains candidate until adopted",
        },
        "human_stoplines": ["adopt"],
        "unknowns": [],
    }
    path = tmp_path / "research.json"
    path.write_text(json.dumps(research), encoding="utf-8")

    monkeypatch.setattr(
        review,
        "build_pr_packet",
        lambda **kwargs: {
            "packet_type": "engineering_brain_pr",
            "pr_body_ja": f"## 目的\n\n{token}\n",
            "research_packet": kwargs.get("research_packet"),
            "external_actions": {"performed": False, "allowed": False},
            "status": "plan_only",
            "merge": {"status": "承認待ち", "allowed": False},
            "unknowns": [],
            "human_stoplines": [],
            "checks": {},
            "visible_scope": {"source": "x", "files": [], "summary": "", "file_count": 0},
            "changes": [],
            "reinvention_check": {"required": True, "decision": "hold", "reason": "x"},
            "purpose": "",
            "repo": "<REPO>",
            "version": 1,
            "base_branch": "main",
            "current_branch": "feature",
            "run_packet": None,
        },
    )
    import engineering_brain.cli as cli

    monkeypatch.setattr(cli, "build_pr_packet", review.build_pr_packet)

    code = main([
        "pr",
        "--repo",
        str(ROOT),
        "--research-packet",
        str(path),
        "--purpose",
        "safe purpose",
        "--no-closeout",
        "--json",
    ])
    assert code == 0
    out = capfd.readouterr().out
    assert token not in out
    assert "safe purpose" in out


def test_cli_pr_text_mode_prints_japanese_body(capfd, monkeypatch) -> None:
    monkeypatch.setattr(
        review,
        "build_pr_packet",
        lambda **_: {
            "pr_body_ja": "## 目的\n\nテスト\n",
            "external_actions": {"performed": False},
        },
    )
    import engineering_brain.cli as cli

    monkeypatch.setattr(cli, "build_pr_packet", review.build_pr_packet)

    code = main(["pr", "--repo", str(ROOT), "--no-closeout"])

    assert code == 0
    assert "## 目的" in capfd.readouterr().out


def test_cli_pr_accepts_explicit_base(monkeypatch, capfd) -> None:
    seen: dict[str, str | None] = {}

    def fake_build(**kwargs):
        seen["base"] = kwargs.get("base")
        return {
            "packet_type": "engineering_brain_pr",
            "pr_body_ja": "## 目的\n",
            "external_actions": {"performed": False},
        }

    monkeypatch.setattr(review, "build_pr_packet", fake_build)
    # cli imports build_pr_packet at module level
    import engineering_brain.cli as cli

    monkeypatch.setattr(cli, "build_pr_packet", fake_build)
    code = main(["pr", "--repo", str(ROOT), "--base", "origin/trunk", "--no-closeout", "--json"])
    assert code == 0
    assert seen["base"] == "origin/trunk"


def test_redact_personal_paths_helper() -> None:
    raw = "see " + "/home/" + "bob" + "/work/repo"
    assert redact_personal_paths(raw) == "see <USER_HOME>/work/repo"


def test_redact_skips_embedded_relative_home_segments() -> None:
    relative = "src/home/alice/page.py"
    assert redact_personal_paths(relative) == relative
    assert PERSONAL_PATH_PATTERN.search(relative) is None


def test_parse_status_line_survives_stripped_leading_space() -> None:
    assert review._parse_status_line("M CHANGELOG.md") == ("M", "CHANGELOG.md")
    assert review._parse_status_line(" M README.md") == ("M", "README.md")
    assert review._parse_status_line("?? engineering_brain/review.py") == (
        "??",
        "engineering_brain/review.py",
    )
