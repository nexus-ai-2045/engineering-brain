from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .gates import closeout_repo, evaluate_triggers, route_task
from .registry import adoption_units, select_technology_sources
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

    version_parser = sub.add_parser("version", help="Show version surfaces and release policy.")
    version_parser.add_argument("--repo", default=".")
    version_parser.add_argument("--json", action="store_true")

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
    if args.command == "version":
        return emit(version_packet(Path(args.repo).resolve()), as_json=args.json)
    parser.error("unknown command")
    return 2


def emit(payload: dict[str, Any], *, as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0


def render_text(payload: dict[str, Any]) -> str:
    if "units" in payload and isinstance(payload["units"], list):
        return "\n".join(str(unit) for unit in payload["units"])
    return json.dumps(payload, ensure_ascii=False, indent=2)


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
