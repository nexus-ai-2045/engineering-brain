from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .finish import apply_local_cleanup, finish_plan, install_hooks
from .feedback import build_next_plan_context, load_feedback_packet, validate_feedback_packet
from .gates import closeout_repo, evaluate_triggers, route_task
from .registry import adoption_units, select_technology_sources
from .research import DECISIONS, build_research_packet
from .run_packet import build_run_packet
from .skill_sync import compare_skill, default_runtime_root, sync_skill
from .versioning import version_packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devbrain", description="Local-first development assurance gates.")
    sub = parser.add_subparsers(dest="command", required=True)

    route_parser = sub.add_parser("route", help="Route a task to development gates.")
    route_parser.add_argument("--task", required=True)
    route_parser.add_argument("--json", action="store_true")

    gate_parser = sub.add_parser("gate", help="Evaluate gates for triggers.")
    gate_parser.add_argument("--trigger", action="append", default=[])
    gate_parser.add_argument("--json", action="store_true")

    closeout_parser = sub.add_parser("closeout", help="Run local closeout checks.")
    closeout_parser.add_argument("--repo", default=".")
    closeout_parser.add_argument("--json", action="store_true")

    list_parser = sub.add_parser("list", help="List adoption units.")
    list_parser.add_argument("--json", action="store_true")

    catalog_parser = sub.add_parser("catalog", help="List technology best-practice sources.")
    catalog_parser.add_argument("--domain")
    catalog_parser.add_argument("--json", action="store_true")

    skill_sync_parser = sub.add_parser("skill-sync", help="Check or sync the engineering-autopilot runtime skill.")
    skill_sync_parser.add_argument("--source", default="skills/engineering-autopilot")
    skill_sync_parser.add_argument("--runtime-root")
    skill_sync_parser.add_argument("--apply", action="store_true")
    skill_sync_parser.add_argument("--json", action="store_true")

    run_parser = sub.add_parser("run", help="Build an engineering-autopilot run packet.")
    run_parser.add_argument("--task", required=True)
    run_parser.add_argument("--repo", default=".")
    run_parser.add_argument("--domain")
    run_parser.add_argument("--closeout", action="store_true")
    run_parser.add_argument("--json", action="store_true")

    research_parser = sub.add_parser("research", help="Build a candidate research and decision packet.")
    research_parser.add_argument("--task", required=True)
    research_parser.add_argument("--domain", required=True)
    research_parser.add_argument("--decision", choices=DECISIONS, default="hold")
    research_parser.add_argument("--rationale", default="")
    research_parser.add_argument("--json", action="store_true")

    version_parser = sub.add_parser("version", help="Show version surfaces and release policy.")
    version_parser.add_argument("--repo", default=".")
    version_parser.add_argument("--json", action="store_true")

    feedback_parser = sub.add_parser(
        "feedback", help="Validate an FDE feedback packet and build next-Plan context."
    )
    feedback_parser.add_argument("--input", required=True)
    feedback_parser.add_argument("--json", action="store_true")

    finish_parser = sub.add_parser("finish", help="Plan or apply post-merge branch cleanup.")
    finish_parser.add_argument("--repo", default=".")
    finish_parser.add_argument("--apply-local", action="store_true")
    finish_parser.add_argument("--json", action="store_true")

    hooks_parser = sub.add_parser("hooks", help="Install repo-provided local Git hooks.")
    hooks_sub = hooks_parser.add_subparsers(dest="hooks_command", required=True)
    hooks_install = hooks_sub.add_parser("install", help="Install opt-in local Git hooks.")
    hooks_install.add_argument("--repo", default=".")
    hooks_install.add_argument("--force", action="store_true")
    hooks_install.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "route":
        return emit(route_task(args.task), as_json=args.json)
    if args.command == "gate":
        triggers = args.trigger or ["implementation"]
        return emit(evaluate_triggers(triggers), as_json=args.json)
    if args.command == "closeout":
        return emit(closeout_repo(Path(args.repo).resolve()), as_json=args.json)
    if args.command == "list":
        return emit({"units": [unit.id for unit in adoption_units()]}, as_json=args.json)
    if args.command == "catalog":
        return emit({"sources": [serialize_source(source) for source in select_technology_sources(args.domain)]}, as_json=args.json)
    if args.command == "skill-sync":
        runtime_root = Path(args.runtime_root).resolve() if args.runtime_root else default_runtime_root()
        source = Path(args.source).resolve()
        payload = sync_skill(source_dir=source, runtime_root=runtime_root, apply=True) if args.apply else compare_skill(source_dir=source, runtime_root=runtime_root)
        payload["mode"] = "apply" if args.apply else "dry-run"
        return emit(payload, as_json=args.json)
    if args.command == "run":
        return emit(
            build_run_packet(
                task=args.task,
                repo=Path(args.repo).resolve(),
                domain=args.domain,
                closeout=args.closeout,
            ),
            as_json=args.json,
        )
    if args.command == "research":
        return emit(
            build_research_packet(
                task=args.task,
                domain=args.domain,
                decision=args.decision,
                rationale=args.rationale,
            ),
            as_json=args.json,
        )
    if args.command == "version":
        return emit(version_packet(Path(args.repo).resolve()), as_json=args.json)
    if args.command == "feedback":
        try:
            packet = load_feedback_packet(Path(args.input).resolve())
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            return emit_feedback_error(error, as_json=args.json)
        errors = validate_feedback_packet(packet)
        safe_identifiers = not any(
            "secret-like content" in error or "Unicode surrogate" in error
            for error in errors
        )
        payload = {
            "overall": "ok" if not errors else "error",
            "schema_version": packet.get("schema_version"),
            "feedback_id": packet.get("feedback_id") if safe_identifiers else None,
            "errors": errors,
            "next_plan": build_next_plan_context(packet) if not errors else None,
            "external_actions_performed": False,
        }
        emit(payload, as_json=args.json)
        return 0 if not errors else 1
    if args.command == "finish":
        repo = Path(args.repo).resolve()
        payload = apply_local_cleanup(repo) if args.apply_local else finish_plan(repo)
        return emit(payload, as_json=args.json)
    if args.command == "hooks":
        if args.hooks_command == "install":
            return emit(install_hooks(Path(args.repo).resolve(), force=args.force), as_json=args.json)
    parser.error("unknown command")
    return 2


def emit(payload: dict[str, Any], *, as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(render_text(payload))
    return 0


def emit_feedback_error(error: Exception, *, as_json: bool) -> int:
    payload = {
        "overall": "error",
        "schema_version": None,
        "feedback_id": None,
        "errors": [f"{type(error).__name__}: invalid feedback input"],
        "next_plan": None,
        "external_actions_performed": False,
    }
    emit(payload, as_json=as_json)
    return 1


def render_text(payload: dict[str, Any]) -> str:
    if "units" in payload and isinstance(payload["units"], list):
        return "\n".join(str(unit) for unit in payload["units"])
    return json.dumps(payload, ensure_ascii=True, indent=2)


def serialize_source(source: Any) -> dict[str, Any]:
    return {
        "id": source.id,
        "domain": source.domain,
        "status": source.status,
        "source_refs": list(source.source_refs),
        "use_when": list(source.use_when),
        "adoption_route": source.adoption_route,
        "gate_hint": source.gate_hint,
        "insufficient_if": list(source.insufficient_if),
    }


if __name__ == "__main__":
    raise SystemExit(main())
