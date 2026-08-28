from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from .path_safety import scan_personal_paths
from .registry import AdoptionUnit, select_units
from .assurance import evaluate_async_orchestration, evaluate_structured_model
from .verification import build_closeout_verification


PUBLIC_TRIGGERS = {"public_release", "external_send", "github_visibility", "announcement", "publish", "push", "pr"}
PUBLIC_PATH_TRIGGERS = {"public_path", "path_redaction", "absolute_path", "personal_path"}


def _contains_signal(text: str, signal: str) -> bool:
    if signal.isascii() and all(character.isalnum() or character == "_" for character in signal):
        return re.search(rf"(?<![a-z0-9_]){re.escape(signal)}(?![a-z0-9_])", text) is not None
    return signal in text


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
    orchestration_tokens = (
        "gcp", "gcloud", "google cloud", "vertex", "cloud run", "cloud workflow",
        "workflow", "ワークフロー", "cloud build", "custom job", "gce", "gke", "gpu", "wif",
    )
    model_tokens = (
        "ocr", "帳票", "document ai", "structured output", "構造化出力", "distillation",
        "蒸留", "quantization", "quantized", "量子化", "schema", "teacher",
    )
    if any(_contains_signal(normalized_task, token) for token in orchestration_tokens):
        inferred.add("orchestration")
    if any(_contains_signal(normalized_task, token) for token in model_tokens):
        inferred.add("model_eval")
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


def evaluate_triggers(
    triggers: list[str],
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = select_units(triggers, include_candidates=True)
    requested_public_action = any(trigger in PUBLIC_TRIGGERS for trigger in triggers)
    assurance: dict[str, Any] = {}
    selected_ids = {unit.id for unit in selected}
    if "async_orchestration_evidence_gate" in selected_ids:
        assurance["async_orchestration"] = evaluate_async_orchestration(
            (evidence or {}).get("async_orchestration", {})
        )
    if "structured_model_evaluation_gate" in selected_ids:
        assurance["structured_model"] = evaluate_structured_model(
            (evidence or {}).get("structured_model", {})
        )
    assurance_blocked = any(result["status"] != "pass" for result in assurance.values())
    return {
        "triggers": triggers,
        "overall": "blocked" if requested_public_action or assurance_blocked else "ok",
        "units": [serialize_unit(unit) for unit in selected],
        "assurance": assurance,
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


def closeout_repo(
    repo: Path,
    *,
    profile_ids: list[str] | None = None,
    execute: bool = True,
) -> dict[str, Any]:
    git_status = run(["git", "status", "--short", "--branch"], cwd=repo)

    def run_command(command: list[str]) -> dict[str, Any]:
        return run(command, cwd=repo)

    verification = build_closeout_verification(
        repo,
        profile_ids=profile_ids,
        execute=execute,
        run_command=run_command,
    )
    personal_path_findings = scan_personal_paths(repo)

    verification_ok = verification["status"] == "ok"
    public_path_ok = not personal_path_findings
    git_ok = git_status["returncode"] == 0
    external_public = {
        "status": "blocked_until_human_approval",
        "actions_performed": False,
        "blocked_actions": ["github repo create", "remote add", "push", "PR create", "visibility public"],
    }

    return {
        "overall": "ok" if git_ok and verification_ok and public_path_ok else "blocked",
        "schema_version": 2,
        "implementation": {
            "status": "present",
            "repo": "<REPO>",
            "git_status": git_status,
        },
        "verification": verification,
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
