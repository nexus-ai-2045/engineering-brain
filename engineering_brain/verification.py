from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .registry import load_registry


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_PROFILES = PACKAGE_ROOT / "data" / "verification-profiles.yaml"
REPO_PROFILES = Path("registry") / "verification-profiles.yaml"

EVIDENCE_STATUSES = ("pass", "fail", "not_run", "not_applicable")
LAYERS = ("unit", "integration", "smoke", "e2e")
CHECK_KINDS = ("argv", "compile_tracked_python", "human", "json_status")
PROFILE_LOAD_MODES = ("extend", "replace")

RunCommand = Callable[[list[str]], dict[str, Any]]


@dataclass(frozen=True)
class VerificationCheck:
    id: str
    argv: tuple[str, ...]
    kind: str
    ok_statuses: tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationProfile:
    id: str
    layer: str
    status: str
    detect_any: tuple[str, ...]
    required: bool
    execute: bool
    selection: str
    checks: tuple[VerificationCheck, ...]
    insufficient_if: tuple[str, ...]


def _as_bool(value: Any, *, field: str, profile_id: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in {"true", "True", "yes", "1"}:
        return True
    if value in {"false", "False", "no", "0"}:
        return False
    raise ValueError(f"verification profile {profile_id} has invalid {field}: {value!r}")


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, str):
        return (value,)
    raise ValueError(f"expected string list, got {type(value).__name__}")


def validate_profile(raw: dict[str, Any]) -> None:
    required = {
        "id",
        "layer",
        "status",
        "detect_any",
        "required",
        "execute",
        "checks",
        "insufficient_if",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise ValueError(
            f"verification profile {raw.get('id', '<unknown>')} missing fields: {', '.join(missing)}"
        )
    if raw["status"] not in {"adopted", "candidate", "hold", "rejected"}:
        raise ValueError(f"verification profile {raw['id']} has invalid status: {raw['status']}")
    if raw["layer"] not in LAYERS:
        raise ValueError(f"verification profile {raw['id']} has invalid layer: {raw['layer']}")
    if not raw["checks"]:
        raise ValueError(f"verification profile {raw['id']} has empty checks")
    if not raw["insufficient_if"]:
        raise ValueError(f"verification profile {raw['id']} has empty insufficient_if")
    selection = raw.get("selection", "auto")
    if selection not in {"auto", "opt_in"}:
        raise ValueError(f"verification profile {raw['id']} has invalid selection: {selection}")


def _parse_check(raw: dict[str, Any], *, profile_id: str) -> VerificationCheck:
    check_id = str(raw.get("id") or "").strip()
    if not check_id:
        raise ValueError(f"verification profile {profile_id} has a check without id")
    kind = str(raw.get("kind") or "argv")
    argv = tuple(str(part) for part in _as_str_tuple(raw.get("argv")))
    ok_statuses = _as_str_tuple(raw.get("ok_statuses"))
    if kind in {"argv", "json_status"} and not argv:
        raise ValueError(f"verification profile {profile_id} check {check_id} needs argv")
    if kind not in CHECK_KINDS:
        raise ValueError(f"verification profile {profile_id} check {check_id} has invalid kind: {kind}")
    if kind == "json_status" and not ok_statuses:
        raise ValueError(
            f"verification profile {profile_id} check {check_id} needs ok_statuses"
        )
    return VerificationCheck(id=check_id, argv=argv, kind=kind, ok_statuses=ok_statuses)


def load_verification_profiles(path: Path | None = None) -> list[VerificationProfile]:
    resolved = path or DEFAULT_PROFILES
    raw_doc = load_registry(resolved)
    raw_profiles = raw_doc.get("profiles")
    if not isinstance(raw_profiles, list):
        raise ValueError(f"{resolved} must define a profiles list")
    profiles: list[VerificationProfile] = []
    for raw in raw_profiles:
        validate_profile(raw)
        profile_id = raw["id"]
        profiles.append(
            VerificationProfile(
                id=profile_id,
                layer=raw["layer"],
                status=raw["status"],
                detect_any=_as_str_tuple(raw.get("detect_any")),
                required=_as_bool(raw["required"], field="required", profile_id=profile_id),
                execute=_as_bool(raw["execute"], field="execute", profile_id=profile_id),
                selection=str(raw.get("selection") or "auto"),
                checks=tuple(_parse_check(item, profile_id=profile_id) for item in raw["checks"]),
                insufficient_if=_as_str_tuple(raw["insufficient_if"]),
            )
        )
    return profiles


def read_profile_load_mode(path: Path) -> str:
    raw_doc = load_registry(path)
    mode = str(raw_doc.get("profile_load_mode") or "extend")
    if mode not in PROFILE_LOAD_MODES:
        raise ValueError(
            f"{path} has invalid profile_load_mode: {mode!r} "
            f"(expected one of {', '.join(PROFILE_LOAD_MODES)})"
        )
    return mode


def merge_verification_profiles(
    packaged: list[VerificationProfile],
    overlay: list[VerificationProfile],
) -> list[VerificationProfile]:
    by_id = {profile.id: profile for profile in packaged}
    order = [profile.id for profile in packaged]
    for profile in overlay:
        if profile.id not in by_id:
            order.append(profile.id)
        by_id[profile.id] = profile
    return [by_id[profile_id] for profile_id in order]


def load_profiles_for_repo(repo: Path) -> tuple[list[VerificationProfile], str]:
    packaged = load_verification_profiles(DEFAULT_PROFILES)
    override = repo / REPO_PROFILES
    if not override.is_file():
        return packaged, "<PACKAGE>/data/verification-profiles.yaml"
    mode = read_profile_load_mode(override)
    overlay = load_verification_profiles(override)
    if mode == "replace":
        return overlay, "<REPO>/registry/verification-profiles.yaml (replace)"
    merged = merge_verification_profiles(packaged, overlay)
    return merged, "<PACKAGE>+<REPO>/registry/verification-profiles.yaml (extend)"


def detect_repo_signals(repo: Path, markers: Iterable[str] | None = None) -> set[str]:
    signals: set[str] = set()
    for marker in markers or ():
        if marker and (repo / marker).exists():
            signals.add(marker)
    return signals


def profile_is_applicable(
    profile: VerificationProfile,
    *,
    signals: set[str],
    requested_ids: set[str] | None,
) -> bool:
    if requested_ids is not None:
        return profile.id in requested_ids
    if profile.selection == "opt_in":
        return False
    if not profile.detect_any:
        return False
    return any(marker in signals for marker in profile.detect_any)


def _profile_exclusion_reason(
    profile: VerificationProfile,
    *,
    signals: set[str],
    requested_ids: set[str] | None,
) -> str | None:
    if requested_ids is not None:
        return None
    if profile.selection == "opt_in":
        return "opt_in without explicit --profile"
    if not profile.detect_any:
        return "no detect_any markers"
    if not any(marker in signals for marker in profile.detect_any):
        return "detect_any unmatched"
    return None


def select_verification_profiles(
    repo: Path,
    *,
    profile_ids: list[str] | None = None,
    include_candidates: bool = True,
    profiles_path: Path | None = None,
) -> dict[str, Any]:
    if profiles_path is not None:
        profiles = load_verification_profiles(profiles_path)
        profiles_label = (
            "<PACKAGE>/data/verification-profiles.yaml"
            if profiles_path == DEFAULT_PROFILES
            else str(profiles_path)
        )
    else:
        profiles, profiles_label = load_profiles_for_repo(repo)
    markers = {marker for profile in profiles for marker in profile.detect_any}
    signals = detect_repo_signals(repo, markers)
    requested = set(profile_ids) if profile_ids is not None else None
    selected: list[VerificationProfile] = []
    not_applicable: list[tuple[VerificationProfile, str]] = []
    considered_ids = {profile.id for profile in profiles}
    for profile in profiles:
        if profile.status == "candidate" and not include_candidates:
            if requested is None or profile.id not in requested:
                continue
        if profile.status in {"hold", "rejected"} and (
            requested is None or profile.id not in requested
        ):
            continue
        if profile_is_applicable(profile, signals=signals, requested_ids=requested):
            selected.append(profile)
            continue
        reason = _profile_exclusion_reason(
            profile, signals=signals, requested_ids=requested
        )
        if reason is not None:
            not_applicable.append((profile, reason))
    unknown_requested = sorted((requested or set()) - considered_ids)
    return {
        "profiles_path": profiles_label,
        "detected_signals": sorted(signals),
        "requested_profile_ids": sorted(requested) if requested is not None else [],
        "unknown_requested_profile_ids": unknown_requested,
        "selected": [serialize_profile(profile) for profile in selected],
        "selected_profiles": selected,
        "not_applicable": [
            {**serialize_profile(profile), "reason": reason}
            for profile, reason in not_applicable
        ],
        "not_applicable_profiles": not_applicable,
    }


def serialize_profile(profile: VerificationProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "layer": profile.layer,
        "status": profile.status,
        "detect_any": list(profile.detect_any),
        "required": profile.required,
        "execute": profile.execute,
        "selection": profile.selection,
        "checks": [
            {
                "id": check.id,
                "kind": check.kind,
                "argv": list(check.argv),
                "ok_statuses": list(check.ok_statuses),
            }
            for check in profile.checks
        ],
        "insufficient_if": list(profile.insufficient_if),
    }


def _require_known_profiles(selection: dict[str, Any]) -> None:
    if selection["unknown_requested_profile_ids"]:
        unknown = ", ".join(selection["unknown_requested_profile_ids"])
        raise ValueError(f"unknown verification profile id(s): {unknown}")


def _not_applicable_evidence(
    profile: VerificationProfile,
    *,
    reason: str,
) -> dict[str, Any]:
    return {
        "profile_id": profile.id,
        "layer": profile.layer,
        "check_id": "_profile",
        "status": "not_applicable",
        "required": False,
        "execute_planned": False,
        "command": "not applicable",
        "kind": "applicability",
        "reason": reason,
        "returncode": None,
        "stdout": "",
        "stderr": reason,
    }


def plan_verification(
    repo: Path,
    *,
    profile_ids: list[str] | None = None,
) -> dict[str, Any]:
    selection = select_verification_profiles(repo, profile_ids=profile_ids)
    _require_known_profiles(selection)
    evidence = []
    for profile in selection["selected_profiles"]:
        for check in profile.checks:
            evidence.append(
                {
                    "profile_id": profile.id,
                    "layer": profile.layer,
                    "check_id": check.id,
                    "status": "not_run",
                    "required": profile.required,
                    "execute_planned": profile.execute and check.kind != "human",
                    "command": _command_label(check),
                    "kind": check.kind,
                }
            )
    for profile, reason in selection["not_applicable_profiles"]:
        evidence.append(_not_applicable_evidence(profile, reason=reason))
    return {
        "schema_version": 2,
        "mode": "plan",
        "detected_signals": selection["detected_signals"],
        "profiles_path": selection["profiles_path"],
        "selected_profiles": selection["selected"],
        "not_applicable_profiles": selection["not_applicable"],
        "unknown_requested_profile_ids": selection["unknown_requested_profile_ids"],
        "evidence": evidence,
        "summary": _summarize(evidence),
    }


def build_closeout_verification(
    repo: Path,
    *,
    profile_ids: list[str] | None = None,
    execute: bool = True,
    run_command: RunCommand,
) -> dict[str, Any]:
    selection = select_verification_profiles(repo, profile_ids=profile_ids)
    _require_known_profiles(selection)

    evidence: list[dict[str, Any]] = []
    pytest_result: dict[str, Any] | None = None
    compile_result: dict[str, Any] | None = None

    for profile in selection["selected_profiles"]:
        for check in profile.checks:
            item = _run_check(
                repo,
                profile=profile,
                check=check,
                execute=execute and profile.execute,
                run_command=run_command,
            )
            evidence.append(item)
            if check.id == "pytest" or (
                check.kind == "argv" and check.argv[:3] == ("python", "-m", "pytest")
            ):
                pytest_result = _compat_command_result(item)
            if check.kind == "compile_tracked_python" or check.id == "compile_tracked_python":
                compile_result = _compat_command_result(item)

    for profile, reason in selection["not_applicable_profiles"]:
        evidence.append(_not_applicable_evidence(profile, reason=reason))

    summary = _summarize(evidence)
    blocked = any(
        item["required"] and item["status"] in {"fail", "not_run"} for item in evidence
    )
    payload: dict[str, Any] = {
        "status": "blocked" if blocked else "ok",
        "schema_version": 2,
        "mode": "execute" if execute else "plan",
        "detected_signals": selection["detected_signals"],
        "profiles_path": selection["profiles_path"],
        "selected_profiles": selection["selected"],
        "not_applicable_profiles": selection["not_applicable"],
        "evidence": evidence,
        "summary": summary,
    }
    if pytest_result is not None:
        payload["pytest"] = pytest_result
    if compile_result is not None:
        payload["compileall"] = compile_result
    return payload


def _run_check(
    repo: Path,
    *,
    profile: VerificationProfile,
    check: VerificationCheck,
    execute: bool,
    run_command: RunCommand,
) -> dict[str, Any]:
    base = {
        "profile_id": profile.id,
        "layer": profile.layer,
        "check_id": check.id,
        "required": profile.required,
        "execute_planned": profile.execute and check.kind != "human",
        "command": _command_label(check),
        "kind": check.kind,
    }
    if check.kind == "human":
        return {
            **base,
            "status": "not_run",
            "returncode": None,
            "stdout": "",
            "stderr": "human evidence required",
        }
    if not execute:
        return {
            **base,
            "status": "not_run",
            "returncode": None,
            "stdout": "",
            "stderr": "check planned but not executed",
        }

    if check.kind == "compile_tracked_python":
        tracked = run_command(["git", "ls-files", "*.py"])
        python_files = tracked["stdout"].splitlines() if tracked["returncode"] == 0 else []
        if not python_files:
            result = {
                "command": "git ls-files *.py",
                "returncode": 1,
                "stdout": tracked.get("stdout", ""),
                "stderr": tracked.get("stderr")
                or "tracked Python files could not be resolved",
            }
        else:
            result = run_command(["python", "-m", "py_compile", *python_files])
        return {
            **base,
            "status": "pass" if result["returncode"] == 0 else "fail",
            "returncode": result["returncode"],
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "command": result.get("command", base["command"]),
        }

    argv = list(check.argv)
    if argv[:3] == ["python", "-m", "pytest"]:
        with tempfile.TemporaryDirectory(prefix="engineering-brain-closeout-") as temp_dir:
            command = [*argv, "--basetemp", str(Path(temp_dir) / "pytest")]
            result = run_command(command)
        result = {
            **result,
            "command": " ".join([*argv, "--basetemp", "<TEMP>"]),
        }
    else:
        result = run_command(argv)

    status = "pass" if result["returncode"] == 0 else "fail"
    stderr = result.get("stderr", "")
    if check.kind == "json_status":
        status, stderr = _status_from_json_payload(
            result.get("stdout", ""),
            ok_statuses=check.ok_statuses,
            command_returncode=result.get("returncode"),
            stderr=stderr,
        )

    return {
        **base,
        "status": status,
        "returncode": result["returncode"],
        "stdout": result.get("stdout", ""),
        "stderr": stderr,
        "command": result.get("command", " ".join(argv)),
    }


def _status_from_json_payload(
    stdout: str,
    *,
    ok_statuses: tuple[str, ...],
    command_returncode: Any,
    stderr: str,
) -> tuple[str, str]:
    if command_returncode not in (0, None):
        return "fail", stderr or "command exited nonzero before JSON status parse"
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return "fail", stderr or "json_status check could not parse stdout JSON"
    if not isinstance(payload, dict):
        return "fail", stderr or "json_status payload must be an object"
    status_value = payload.get("status")
    if status_value in ok_statuses:
        return "pass", stderr
    detail = f"json status {status_value!r} not in {list(ok_statuses)}"
    return "fail", f"{stderr}\n{detail}".strip() if stderr else detail


def _command_label(check: VerificationCheck) -> str:
    if check.kind == "compile_tracked_python":
        return "python -m py_compile <tracked *.py>"
    if check.kind == "human":
        return "human review"
    return " ".join(check.argv)


def _compat_command_result(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "command": item.get("command", ""),
        "returncode": item.get("returncode"),
        "stdout": item.get("stdout", ""),
        "stderr": item.get("stderr", ""),
        "status": item.get("status"),
    }


def _summarize(evidence: list[dict[str, Any]]) -> dict[str, int]:
    summary = {status: 0 for status in EVIDENCE_STATUSES}
    for item in evidence:
        status = item.get("status")
        if status in summary:
            summary[status] += 1
    return summary
