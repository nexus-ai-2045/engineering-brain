from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .gates import closeout_repo, evaluate_triggers, route_task
from .registry import adoption_units, select_technology_sources


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
