from __future__ import annotations

import filecmp
import shutil
from pathlib import Path
from typing import Any


SKILL_NAME = "engineering-autopilot"
RUNTIME_PLACEHOLDER = "<RUNTIME_SKILLS>"
RUNTIME_TARGETS = ("codex", "claude-code")


def default_runtime_root(runtime: str = "codex", *, home: Path | None = None) -> Path:
    base = home or Path.home()
    if runtime == "codex":
        return base / ".codex" / "skills"
    if runtime == "claude-code":
        return base / ".claude" / "skills"
    raise ValueError(f"unsupported runtime: {runtime}")


def default_skill_source() -> Path:
    return Path(__file__).resolve().parents[1] / "skills" / SKILL_NAME


def compare_skill(
    *,
    source_dir: Path,
    runtime_root: Path,
    runtime: str | None = None,
) -> dict[str, Any]:
    source = source_dir.resolve()
    target = (runtime_root / source.name).resolve()
    missing = _required_files(source)
    if missing:
        return _result(
            status="source_missing",
            runtime=runtime,
            source=source,
            runtime_root=runtime_root,
            target=target,
            changed_files=missing,
            missing_files=missing,
            apply_required=False,
        )

    if not target.exists():
        return _result(
            status="missing",
            runtime=runtime,
            source=source,
            runtime_root=runtime_root,
            target=target,
            changed_files=[],
            missing_files=[],
            apply_required=True,
        )

    changed = _changed_files(source, target)
    status = "drift" if changed else "ok"
    return _result(
        status=status,
        runtime=runtime,
        source=source,
        runtime_root=runtime_root,
        target=target,
        changed_files=changed,
        missing_files=[],
        apply_required=bool(changed),
    )


def compare_skill_targets(
    *,
    source_dir: Path,
    runtimes: tuple[str, ...] = RUNTIME_TARGETS,
) -> dict[str, Any]:
    targets = [
        compare_skill(
            source_dir=source_dir,
            runtime_root=default_runtime_root(runtime),
            runtime=runtime,
        )
        for runtime in runtimes
    ]
    return _targets_result(targets=targets, mode="dry-run")


def sync_skill(
    *,
    source_dir: Path,
    runtime_root: Path,
    apply: bool,
    runtime: str | None = None,
) -> dict[str, Any]:
    before = compare_skill(source_dir=source_dir, runtime_root=runtime_root, runtime=runtime)
    before["mode"] = "apply" if apply else "dry-run"
    if not apply or before["status"] == "source_missing":
        return before

    source = source_dir.resolve()
    target = (runtime_root / source.name).resolve()
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    after = compare_skill(source_dir=source, runtime_root=runtime_root, runtime=runtime)
    after["mode"] = "apply"
    after["status"] = "synced" if after["status"] == "ok" else after["status"]
    return after


def _targets_result(*, targets: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    ready_statuses = {"ok", "synced"}
    return {
        "skill": SKILL_NAME,
        "status": (
            "ok"
            if targets and all(item["status"] in ready_statuses for item in targets)
            else "action_required"
        ),
        "mode": mode,
        "targets": targets,
    }


def _required_files(source: Path) -> list[str]:
    required = [
        "SKILL.md",
        "manifest.yaml",
        "runtime/agents/openai.yaml",
        "references/lifecycle.md",
        "references/roadmap.md",
    ]
    return [path for path in required if not (source / path).is_file()]


def _changed_files(source: Path, target: Path) -> list[str]:
    changed: list[str] = []
    source_files = _relative_files(source)
    target_files = _relative_files(target)
    for rel in sorted(source_files | target_files):
        source_file = source / rel
        target_file = target / rel
        if not source_file.exists() or not target_file.exists():
            changed.append(rel)
        elif not filecmp.cmp(source_file, target_file, shallow=False):
            changed.append(rel)
    return changed


def _relative_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def _result(
    *,
    status: str,
    runtime: str | None,
    source: Path,
    runtime_root: Path,
    target: Path,
    changed_files: list[str],
    missing_files: list[str],
    apply_required: bool,
) -> dict[str, Any]:
    result = {
        "skill": SKILL_NAME,
        "status": status,
        "source": _display_path(source),
        "runtime_root": RUNTIME_PLACEHOLDER,
        "target": f"{RUNTIME_PLACEHOLDER}/{target.name}",
        "changed_files": changed_files,
        "missing_files": missing_files,
        "apply_required": apply_required,
        "stopline": "home runtime write requires --apply and current-turn approval",
        "runtime_root_exists": runtime_root.exists(),
    }
    if runtime:
        result["runtime"] = runtime
    if runtime == "claude-code":
        result["invocation"] = {
            "command": f"/{SKILL_NAME}",
            "verified_mode": "normal",
            "unsupported_modes": ["--bare"],
            "reason": "Claude Code 2.1.220 live smoke returned Unknown command for the personal skill projection in --bare mode",
        }
    return result


def _display_path(path: Path) -> str:
    parts = path.parts
    if "skills" in parts:
        index = parts.index("skills")
        return Path(*parts[index:]).as_posix()
    return path.name
