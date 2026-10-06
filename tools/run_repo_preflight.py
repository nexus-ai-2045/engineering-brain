#!/usr/bin/env python3
"""Run upstream repo-preflight without copying its inspection logic.

Clones/updates nexus-ai-2045/repo-preflight into .tools/repo-preflight (gitignored)
and executes readiness_scan.py + consistency_gate.py against this repository.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


UPSTREAM = "https://github.com/nexus-ai-2045/repo-preflight.git"
DEFAULT_CACHE = Path(".tools") / "repo-preflight"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Invoke upstream repo-preflight against this repo.")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument(
        "--intent", default="open_pr",
        help="Read-only upstream gate intent (default: open_pr; does not create a PR).",
    )
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    cache = (repo / args.cache).resolve() if not args.cache.is_absolute() else args.cache.resolve()
    ensure_checkout(cache)

    scan_cmd = [sys.executable, str(cache / "scripts" / "readiness_scan.py"), "--repo", str(repo)]
    scan_cmd.extend(["--intent", args.intent])
    if args.intent in {"push", "open_pr", "merge"}:
        scan_cmd.extend(["--base-ref", args.base_ref])
    elif args.intent in {"publish", "release"}:
        scan_cmd.extend(["--consistency-base-ref", args.base_ref])
    consistency_cmd = [
        sys.executable,
        str(cache / "scripts" / "consistency_gate.py"),
        "--repo",
        str(repo),
        "--base-ref",
        args.base_ref,
        "--json",
    ]

    print("==> repo-preflight readiness_scan")
    scan = subprocess.run(scan_cmd, cwd=repo, text=True, capture_output=True)
    print(scan.stdout)
    if scan.stderr:
        print(scan.stderr, file=sys.stderr)

    print("==> repo-preflight consistency_gate")
    consistency = subprocess.run(consistency_cmd, cwd=repo, text=True, capture_output=True)
    print(consistency.stdout)
    if consistency.stderr:
        print(consistency.stderr, file=sys.stderr)

    # Read the complete upstream JSON documents, not the final line of pretty JSON.
    scan_payload, scan_code = result_status(scan, kind="readiness")
    consistency_payload, consistency_code = result_status(consistency, kind="consistency")
    exit_code = max(scan_code, consistency_code)
    mode = consistency_payload.get("mode")
    status = {0: "pass", 1: "blocked", 2: "tool_error"}[exit_code]
    print(
        f"==> repo-preflight wrapper done "
        f"(readiness_rc={scan.returncode}, consistency_rc={consistency.returncode}, "
        f"mode={mode!r}; not a merge approval)"
    )
    print(json.dumps({
        "schema": "repo-preflight.wrapper/v1",
        "status": status,
        "exit_code": exit_code,
        "readiness_status": scan_payload.get("status"),
        "consistency_status": consistency_payload.get("status"),
        "mode": mode,
        "publication_decision": "blocked_human_review_required",
    }))
    return exit_code


def result_status(
    result: subprocess.CompletedProcess[str], *, kind: str,
) -> tuple[dict, int]:
    """Preserve upstream holds and distinguish execution/JSON contract errors."""
    try:
        payload = json.loads(result.stdout)
    except (ValueError, TypeError):
        return {"status": "tool_error"}, 2
    if not isinstance(payload, dict):
        return {"status": "tool_error"}, 2
    success = (
        {"pass", "ready_after_confirmation"}
        if kind == "readiness" else {"pass", "not_configured"}
    )
    holds = {"blocked", "needs_human_input"} if kind == "readiness" else {"blocked", "shadow_findings", "fail"}
    status = payload.get("status")
    if not isinstance(status, str) or status not in success | holds:
        return payload, 2
    if result.returncode not in {0, 1}:
        return payload, 2
    # Dialogue mode wraps scan errors as top-level blocked with exit code 1.
    scan = payload.get("scan")
    if scan is not None:
        if (
            not isinstance(scan, dict)
            or not isinstance(scan.get("status"), str)
            or scan["status"] not in {"pass", "blocked"}
        ):
            return payload, 2
        if scan["status"] == "blocked":
            return payload, 1
    return payload, 1 if result.returncode or status in holds else 0


def ensure_checkout(cache: Path) -> None:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if (cache / "scripts" / "readiness_scan.py").is_file():
        subprocess.run(["git", "-C", str(cache), "fetch", "--depth", "1", "origin"], check=False)
        subprocess.run(["git", "-C", str(cache), "checkout", "FETCH_HEAD"], check=False)
        return
    subprocess.run(["git", "clone", "--depth", "1", UPSTREAM, str(cache)], check=True)


if __name__ == "__main__":
    raise SystemExit(main())
