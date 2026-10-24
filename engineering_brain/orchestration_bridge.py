"""既存の進行管理へ同じ作業を渡す。外部操作や承認生成は行わない。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


OWNER_SCRIPT = Path("shared/skills/pr-lifecycle-orchestrator/scripts/autopilot_state.py")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, timeout=30,
    )
    if result.returncode:
        raise ValueError("Git binding could not be verified")
    return result.stdout.strip()


def _repository(repo: Path) -> str:
    remote = _git(repo, "remote", "get-url", "origin")
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?",
        remote,
    )
    if not match:
        raise ValueError("A credential-free GitHub origin is required")
    return match.group(1)


def bind_lifecycle(
    repo: Path, goal: str, run_id: str, state_path: Path, owner_root: Path,
) -> dict[str, Any]:
    """既存 init/evaluate を呼び、証拠と承認を自動合格へ昇格させない。"""
    repo = repo.resolve()
    owner_root = owner_root.resolve()
    if not goal.strip() or not run_id.strip():
        raise ValueError("goal and run_id are required")
    if _repository(owner_root).split("/", 1)[1] != "Projects":
        raise ValueError("The registered Projects lifecycle owner is required")
    script = owner_root / OWNER_SCRIPT
    if script.is_symlink() or not script.is_file():
        raise ValueError("The lifecycle owner script is unavailable")
    committed = subprocess.run(
        ["git", "show", f"HEAD:{OWNER_SCRIPT.as_posix()}"], cwd=owner_root,
        capture_output=True, timeout=30,
    )
    if committed.returncode or committed.stdout != script.read_bytes():
        raise ValueError("The lifecycle owner script differs from its committed source")
    script_hash = hashlib.sha256(committed.stdout).hexdigest()
    binding = {
        "schema_version": "pr-autopilot/v1",
        "repository": _repository(repo),
        "goal": goal,
        "head_sha": _git(repo, "rev-parse", "HEAD"),
        "run_id": run_id,
    }
    if state_path.is_symlink():
        raise ValueError("A lifecycle state symlink is not accepted")
    state_path = state_path.resolve()
    resumed = state_path.exists()

    def invoke(*args: str) -> subprocess.CompletedProcess[str]:
        if hashlib.sha256(script.read_bytes()).hexdigest() != script_hash:
            raise ValueError("The lifecycle owner script changed during dispatch")
        result = subprocess.run(
            [sys.executable, str(script), *args], cwd=owner_root,
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise ValueError("The lifecycle owner did not complete the local handoff")
        return result

    with tempfile.TemporaryDirectory(prefix="engineering-lifecycle-") as temporary:
        candidate = Path(temporary) / "state.json"
        if resumed:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        else:
            invoke(
                "init", "--repo", binding["repository"], "--goal", goal,
                "--head-sha", binding["head_sha"], "--run-id", run_id,
                "--output", str(candidate),
            )
            state = json.loads(candidate.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or any(state.get(k) != v for k, v in binding.items()):
            raise ValueError("Lifecycle state binding does not match this repo/head/goal/run")
        if not resumed and (state.get("approvals") != [] or state.get("evidence") != {}):
            raise ValueError("A new lifecycle state must not invent evidence or approval")
        candidate.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        evaluation = json.loads(invoke("evaluate", "--packet", str(candidate)).stdout)
        if not isinstance(evaluation, dict) or evaluation.get("state") == "INVALID":
            raise ValueError("The lifecycle owner returned an invalid evaluation")
        if _git(repo, "rev-parse", "HEAD") != binding["head_sha"]:
            raise ValueError("Target head changed during lifecycle binding")
        if not resumed:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            with state_path.open("x", encoding="utf-8") as output:
                output.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return {
        "owner": "pr-lifecycle-orchestrator",
        "binding": binding,
        "owner_script_sha256": script_hash,
        "state_file": "<LOCAL_LIFECYCLE_STATE>",
        "resumed": resumed,
        "evaluation": evaluation,
        "external_actions_performed": False,
        "local_checks_auto_promoted": False,
        "completion_scope": "local_handoff_only",
    }
