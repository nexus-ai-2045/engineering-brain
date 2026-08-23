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
    parser.add_argument("--intent", default=None)
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    cache = (repo / args.cache).resolve() if not args.cache.is_absolute() else args.cache.resolve()
    ensure_checkout(cache)

    scan_cmd = [sys.executable, str(cache / "scripts" / "readiness_scan.py"), "--repo", str(repo)]
    if args.intent:
        scan_cmd.extend(["--intent", args.intent, "--base-ref", args.base_ref])
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

    # Shadow consistency must run; readiness findings are materials for humans.
    # Exit non-zero only when the upstream tools themselves crash.
    if scan.returncode not in {0, 1} or consistency.returncode not in {0, 1}:
        return 1
    try:
        payload = json.loads(consistency.stdout.strip().splitlines()[-1]) if consistency.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    mode = payload.get("mode")
    print(f"==> repo-preflight wrapper done (consistency mode={mode!r}; not a merge approval)")
    return 0


def ensure_checkout(cache: Path) -> None:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if (cache / "scripts" / "readiness_scan.py").is_file():
        subprocess.run(["git", "-C", str(cache), "fetch", "--depth", "1", "origin"], check=False)
        subprocess.run(["git", "-C", str(cache), "checkout", "FETCH_HEAD"], check=False)
        return
    subprocess.run(["git", "clone", "--depth", "1", UPSTREAM, str(cache)], check=True)


if __name__ == "__main__":
    raise SystemExit(main())
