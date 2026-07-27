from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .path_safety import scan_personal_paths
from .registry import AdoptionUnit, select_units


PUBLIC_TRIGGERS = {"public_release", "external_send", "github_visibility", "announcement", "publish", "push", "pr"}
PUBLIC_PATH_TRIGGERS = {"public_path", "path_redaction", "absolute_path", "personal_path"}


def route_task(task: str) -> dict[str, Any]:
    normalized_task = task.lower()
    words = {part.strip(".,:/\\").lower() for part in task.split()}
    inferred = {"reinvention_check"}
    if {"bug", "fix", "regression"}.intersection(words):
        inferred.add("bug_fix")
    if {"implement", "implementation", "code", "refactor", "実装"}.intersection(words):
        inferred.add("implementation")
    if {"security", "credential", "secret", "agent", "browser", "connector", "hook"}.intersection(words):
        inferred.add("security")
    if {"publish", "public", "release", "github", "push", "pr", "公開"}.intersection(words):
        inferred.add("public_release")
    if {"path", "paths", "absolute", "redaction", "personal", "user", "home", "絶対パス"}.intersection(words):
        inferred.add("public_path")
    if any(token in normalized_task for token in ("絶対パス", "個人ホーム", "ユーザー名", "personal path")):
        inferred.add("public_path")
    if not inferred:
        inferred.add("implementation")

    selected = select_units(sorted(inferred), include_candidates=True)
    blocked = sorted(PUBLIC_TRIGGERS.intersection(inferred))
    if "public_release" in inferred:
        blocked.extend(["push", "pr", "github_visibility"])

    return {
        "task": task,
        "mode": "implement" if "implementation" in inferred or "bug_fix" in inferred else "review",
        "scope": "local-first",
        "inferred_triggers": sorted(inferred),
        "selected_units": [unit.id for unit in selected],
        "blocked_actions": sorted(set(blocked)),
        "done_when": [
            "selected gates have pass/warn/block evidence",
            "implementation, verification, operation, and external_public are separated",
            "public/external actions remain blocked until explicit human approval",
        ],
    }


def evaluate_triggers(triggers: list[str]) -> dict[str, Any]:
    selected = select_units(triggers, include_candidates=True)
    requested_public_action = any(trigger in PUBLIC_TRIGGERS for trigger in triggers)
    return {
        "triggers": triggers,
        "overall": "blocked" if requested_public_action else "ok",
        "units": [serialize_unit(unit) for unit in selected],
    }


def serialize_unit(unit: AdoptionUnit) -> dict[str, Any]:
    return {
        "id": unit.id,
        "status": unit.status,
        "route": unit.route,
        "guarantee_tier": unit.guarantee_tier,
        "boundary": unit.boundary,
        "checks": list(unit.checks),
        "insufficient_if": list(unit.insufficient_if),
    }


def closeout_repo(repo: Path) -> dict[str, Any]:
    git_status = run(["git", "status", "--short", "--branch"], cwd=repo)
    pytest_result = run(["python", "-m", "pytest", "-q"], cwd=repo)
    tracked = run(["git", "ls-files", "*.py"], cwd=repo)
    python_files = tracked["stdout"].splitlines() if tracked["returncode"] == 0 else []
    compile_result = (
        run(["python", "-m", "py_compile", *python_files], cwd=repo)
        if python_files
        else {
            "command": "git ls-files *.py",
            "returncode": 1,
            "stdout": "",
            "stderr": "tracked Python files could not be resolved",
        }
    )
    personal_path_findings = scan_personal_paths(repo)

    verification_ok = pytest_result["returncode"] == 0 and compile_result["returncode"] == 0
    public_path_ok = not personal_path_findings
    git_ok = git_status["returncode"] == 0
    external_public = {
        "status": "blocked_until_human_approval",
        "actions_performed": False,
        "blocked_actions": ["github repo create", "remote add", "push", "PR create", "visibility public"],
    }

    return {
        "overall": "ok" if git_ok and verification_ok and public_path_ok else "blocked",
        "implementation": {
            "status": "present",
            "repo": "<REPO>",
            "git_status": git_status,
        },
        "verification": {
            "status": "ok" if verification_ok else "blocked",
            "pytest": pytest_result,
            "compileall": compile_result,
        },
        "operation": {
            "status": "ok" if verification_ok and public_path_ok else "blocked",
            "required_gates": [
                "fact_source_gate",
                "scope_write_boundary_gate",
                "tdd_regression_gate",
                "agent_containment_gate",
                "human_publication_review_gate",
                "public_path_redaction_gate",
            ],
            "public_path_redaction": {
                "status": "ok" if public_path_ok else "blocked",
                "findings": [
                    {"path": finding.path, "line": finding.line, "match": finding.match}
                    for finding in personal_path_findings
                ],
            },
        },
        "external_public": external_public,
    }


def run(command: list[str], *, cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        creationflags=(
            getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        ),
    )
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
