from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .algorithms import algorithm_catalog, compare_algorithms, select_algorithms
from .finish import apply_local_cleanup, finish_plan, install_hooks
from .feedback import (
    SECRET_LIKE_PATTERN,
    build_next_plan_context,
    load_feedback_packet,
    validate_feedback_packet,
)
from .gates import closeout_repo, evaluate_triggers, route_task
from .registry import (
    DEFAULT_LOCAL_LEARNINGS,
    FIELD_REVIEW_STATES,
    LEARNING_DECISIONS,
    adoption_units,
    check_learning_assurance,
    get_local_learning,
    list_local_learnings,
    plan_adopt_learning,
    select_technology_sources,
    serialize_local_learning,
    start_field_review,
)
from .evals import (
    build_blind_review_bundle,
    build_eval_plan,
    build_eval_smoke_packet,
    build_run_manifest,
    load_eval_suite,
    score_eval_results,
    validate_result_import,
)
from .research import (
    DECISIONS,
    PRECEDENT_DECISION_CONTRACT,
    build_research_packet,
)
from .review import build_pr_packet, load_packet_file, public_stdout_packet
from .run_packet import build_run_packet
from .skill_sync import (
    RUNTIME_TARGETS,
    compare_skill,
    default_runtime_root,
    default_skill_source,
    sync_skill,
)
from .versioning import version_packet


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdout()
    parser = argparse.ArgumentParser(prog="engineering-brain", description="Local-first development assurance gates.")
    sub = parser.add_subparsers(dest="command", required=True)

    route_parser = sub.add_parser("route", help="Route a task to development gates.")
    route_parser.add_argument("--task", required=True)
    route_parser.add_argument("--json", action="store_true")

    gate_parser = sub.add_parser("gate", help="Evaluate gates for triggers.")
    gate_parser.add_argument("--trigger", action="append", default=[])
    gate_parser.add_argument("--evidence", type=Path)
    gate_parser.add_argument("--json", action="store_true")

    closeout_parser = sub.add_parser("closeout", help="Run local closeout checks.")
    closeout_parser.add_argument("--repo", default=".")
    closeout_parser.add_argument("--json", action="store_true")

    list_parser = sub.add_parser("list", help="List adoption units.")
    list_parser.add_argument("--json", action="store_true")

    learnings_parser = sub.add_parser(
        "learnings",
        help="List and gate local learnings (field_review / adopt).",
    )
    learnings_sub = learnings_parser.add_subparsers(dest="learnings_command", required=True)
    learnings_list = learnings_sub.add_parser(
        "list",
        help="List local learnings; filter by decision or field_review.",
    )
    learnings_list.add_argument("--decision", choices=sorted(LEARNING_DECISIONS))
    learnings_list.add_argument("--field-review", choices=sorted(FIELD_REVIEW_STATES))
    learnings_list.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Optional path to local-learnings.yaml (defaults to repo SSOT).",
    )
    learnings_list.add_argument("--json", action="store_true")
    learnings_field_review = learnings_sub.add_parser(
        "field-review",
        help="Plan candidate -> field_review transition (does not mutate SSOT).",
    )
    learnings_field_review.add_argument("--id", required=True)
    learnings_field_review.add_argument("--registry", type=Path, default=None)
    learnings_field_review.add_argument("--json", action="store_true")
    learnings_adopt = learnings_sub.add_parser(
        "adopt",
        help="Plan field_review -> adopted transition (approval-gated; does not mutate SSOT).",
    )
    learnings_adopt.add_argument("--id", required=True)
    learnings_adopt.add_argument(
        "--approve",
        action="store_true",
        help="Current-turn human approval for adopt readiness (still does not write SSOT).",
    )
    learnings_adopt.add_argument("--registry", type=Path, default=None)
    learnings_adopt.add_argument("--json", action="store_true")
    learnings_assurance = learnings_sub.add_parser(
        "assurance",
        help="Fail-closed check: pending field_review is never operationally guaranteed.",
    )
    learnings_assurance.add_argument("--id", required=True)
    learnings_assurance.add_argument("--registry", type=Path, default=None)
    learnings_assurance.add_argument("--json", action="store_true")

    catalog_parser = sub.add_parser("catalog", help="List technology best-practice sources.")
    catalog_parser.add_argument("--domain")
    catalog_parser.add_argument("--json", action="store_true")

    algorithms_parser = sub.add_parser("algorithms", help="定番アルゴリズムを一覧・選択・比較する。")
    algorithms_sub = algorithms_parser.add_subparsers(dest="algorithms_command", required=True)
    algorithms_list = algorithms_sub.add_parser("list", help="アルゴリズム台帳を一覧する。")
    algorithms_list.add_argument("--family")
    algorithms_list.add_argument("--json", action="store_true")
    algorithms_select = algorithms_sub.add_parser("select", help="問題シグナルと制約から候補を順位付けする。")
    algorithms_select.add_argument("--signal", action="append", default=[])
    algorithms_select.add_argument("--constraint", action="append", default=[])
    algorithms_select.add_argument("--family")
    algorithms_select.add_argument("--limit", type=int, default=5)
    algorithms_select.add_argument("--json", action="store_true")
    algorithms_compare = algorithms_sub.add_parser("compare", help="指定候補の選択条件と計算量を比較する。")
    algorithms_compare.add_argument("--id", action="append", required=True)
    algorithms_compare.add_argument("--json", action="store_true")

    skill_sync_parser = sub.add_parser("skill-sync", help="Check or sync the engineering-autopilot runtime skill.")
    skill_sync_parser.add_argument("--source")
    skill_sync_parser.add_argument("--runtime-root")
    skill_sync_parser.add_argument("--target", choices=(*RUNTIME_TARGETS, "all"), default="codex")
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
    research_parser.add_argument(
        "--precedent-outcome",
        choices=PRECEDENT_DECISION_CONTRACT,
        default=None,
        help="Outcome from implementation-precedent-research. Required with evidence before wrap/extend/adopt_oss/build.",
    )
    research_parser.add_argument(
        "--precedent-evidence",
        action="append",
        default=None,
        help="Evidence pointer from implementation-precedent-research. Repeatable. Required with outcome before wrap/extend/adopt_oss/build.",
    )
    research_parser.add_argument("--json", action="store_true")

    eval_plan_parser = sub.add_parser("eval-plan", help="Build a plan-only model comparison packet.")
    eval_plan_parser.add_argument("--suite", required=True)
    eval_plan_parser.add_argument("--json", action="store_true")

    eval_manifest_parser = sub.add_parser("eval-manifest", help="Freeze a held-out model run manifest.")
    eval_manifest_parser.add_argument("--suite", required=True)
    eval_manifest_parser.add_argument("--run-id", required=True)
    eval_manifest_parser.add_argument("--json", action="store_true")

    eval_smoke_parser = sub.add_parser("eval-smoke", help="Run the synthetic local evaluation pipeline.")
    eval_smoke_parser.add_argument("--suite", required=True)
    eval_smoke_parser.add_argument("--run-id", default="local-smoke")
    eval_smoke_parser.add_argument("--json", action="store_true")

    eval_blind_parser = sub.add_parser("eval-blind", help="Build a blind review packet and separate answer key.")
    eval_blind_parser.add_argument("--suite", required=True)
    eval_blind_parser.add_argument("--outputs", required=True)
    eval_blind_parser.add_argument("--run-id", required=True)
    eval_blind_parser.add_argument("--json", action="store_true")

    eval_score_parser = sub.add_parser("eval-score", help="Score completed held-out evaluation results.")
    eval_score_parser.add_argument("--suite", required=True)
    eval_score_parser.add_argument("--results", required=True)
    eval_score_parser.add_argument("--manifest")
    eval_score_parser.add_argument("--json", action="store_true")

    pr_parser = sub.add_parser(
        "pr",
        help="Build a plan-only PR packet and Japanese body (does not create or push PRs).",
    )
    pr_parser.add_argument("--repo", default=".")
    pr_parser.add_argument("--purpose", default="")
    pr_parser.add_argument("--base", default=None, help="Explicit diff base ref (overrides default-branch detection).")
    pr_parser.add_argument("--run-packet", dest="run_packet")
    pr_parser.add_argument("--research-packet", dest="research_packet")
    pr_parser.add_argument("--no-closeout", action="store_true")
    pr_parser.add_argument("--json", action="store_true")

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
        evidence = None
        if args.evidence is not None:
            evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
            if not isinstance(evidence, dict):
                raise ValueError("evidence must be a JSON object")
        return emit(evaluate_triggers(triggers, evidence), as_json=args.json)
    if args.command == "closeout":
        return emit(closeout_repo(Path(args.repo).resolve()), as_json=args.json)
    if args.command == "list":
        return emit({"units": [unit.id for unit in adoption_units()]}, as_json=args.json)
    if args.command == "learnings":
        registry_path = Path(args.registry).resolve() if args.registry else DEFAULT_LOCAL_LEARNINGS
        if args.learnings_command == "list":
            items = list_local_learnings(
                registry_path,
                decision=args.decision,
                field_review=args.field_review,
            )
            payload = {
                "learnings": [serialize_local_learning(item) for item in items],
                "counts": {
                    "total": len(items),
                    "pending_field_review": sum(1 for item in items if item.field_review == "pending"),
                    "adopted": sum(1 for item in items if item.decision == "adopted"),
                },
            }
            return emit(payload, as_json=args.json)
        learning = get_local_learning(args.id, registry_path)
        if args.learnings_command == "field-review":
            result = start_field_review(learning)
            emit(result, as_json=args.json)
            return 0 if result["status"] == "ok" else 1
        if args.learnings_command == "adopt":
            result = plan_adopt_learning(
                learning,
                current_turn_approval=args.approve,
            )
            emit(result, as_json=args.json)
            return 0 if result["status"] == "ok" else 1
        if args.learnings_command == "assurance":
            result = check_learning_assurance(learning)
            emit(result, as_json=args.json)
            return 0 if result["status"] == "pass" else 1
    if args.command == "catalog":
        return emit({"sources": [serialize_source(source) for source in select_technology_sources(args.domain)]}, as_json=args.json)
    if args.command == "algorithms":
        if args.algorithms_command == "list":
            entries = algorithm_catalog()
            if args.family:
                entries = [entry for entry in entries if entry.family == args.family]
            return emit(
                {
                    "algorithms": [
                        {"id": entry.id, "title_ja": entry.title_ja, "family": entry.family, "status": entry.status}
                        for entry in entries
                    ]
                },
                as_json=args.json,
            )
        if args.algorithms_command == "select":
            return emit(
                {
                    "signals": args.signal,
                    "constraints": args.constraint,
                    "selection": select_algorithms(
                        signals=args.signal,
                        constraints=args.constraint,
                        family=args.family,
                        limit=args.limit,
                    ),
                },
                as_json=args.json,
            )
        if args.algorithms_command == "compare":
            return emit({"comparison": compare_algorithms(args.id)}, as_json=args.json)
    if args.command == "skill-sync":
        if args.target == "all" and args.runtime_root:
            skill_sync_parser.error("--runtime-root cannot be combined with --target all")
        source = Path(args.source).resolve() if args.source else default_skill_source()
        targets = RUNTIME_TARGETS if args.target == "all" else (args.target,)
        results = []
        for runtime in targets:
            runtime_root = (
                Path(args.runtime_root).resolve()
                if args.runtime_root
                else default_runtime_root(runtime)
            )
            result = (
                sync_skill(
                    source_dir=source,
                    runtime_root=runtime_root,
                    apply=True,
                    runtime=runtime,
                )
                if args.apply
                else compare_skill(
                    source_dir=source,
                    runtime_root=runtime_root,
                    runtime=runtime,
                )
            )
            result["mode"] = "apply" if args.apply else "dry-run"
            results.append(result)
        if args.target == "all":
            ready_statuses = {"ok", "synced"}
            payload = {
                "skill": results[0]["skill"],
                "status": "ok" if all(item["status"] in ready_statuses for item in results) else "action_required",
                "mode": "apply" if args.apply else "dry-run",
                "targets": results,
            }
        else:
            payload = results[0]
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
                precedent_outcome=args.precedent_outcome,
                precedent_evidence=args.precedent_evidence,
            ),
            as_json=args.json,
        )
    if args.command == "eval-plan":
        suite = load_eval_suite(Path(args.suite).resolve())
        return emit(build_eval_plan(suite), as_json=args.json)
    if args.command == "eval-manifest":
        suite = load_eval_suite(Path(args.suite).resolve())
        return emit(build_run_manifest(suite, run_id=args.run_id), as_json=args.json)
    if args.command == "eval-smoke":
        suite = load_eval_suite(Path(args.suite).resolve())
        return emit(build_eval_smoke_packet(suite, run_id=args.run_id), as_json=args.json)
    if args.command == "eval-blind":
        suite = load_eval_suite(Path(args.suite).resolve())
        outputs = json.loads(Path(args.outputs).resolve().read_text(encoding="utf-8"))
        if not isinstance(outputs, list):
            raise ValueError("eval outputs must be a JSON array")
        return emit(
            build_blind_review_bundle(suite, outputs, run_id=args.run_id),
            as_json=args.json,
        )
    if args.command == "eval-score":
        suite = load_eval_suite(Path(args.suite).resolve())
        results = json.loads(Path(args.results).resolve().read_text(encoding="utf-8"))
        if not isinstance(results, list):
            raise ValueError("eval results must be a JSON array")
        if args.manifest:
            manifest = json.loads(Path(args.manifest).resolve().read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("eval manifest must be a JSON object")
            validate_result_import(suite, manifest, results)
        return emit(score_eval_results(suite, results), as_json=args.json)
    if args.command == "pr":
        run_packet = load_packet_file(Path(args.run_packet).resolve()) if args.run_packet else None
        research_packet = (
            load_packet_file(Path(args.research_packet).resolve()) if args.research_packet else None
        )
        packet = build_pr_packet(
            repo=Path(args.repo).resolve(),
            purpose=args.purpose,
            closeout=not args.no_closeout,
            base=args.base,
            run_packet=run_packet,
            research_packet=research_packet,
        )
        public = public_stdout_packet(packet, purpose_override=args.purpose)
        if args.json:
            return emit(public, as_json=True)
        write_stdout(public["pr_body_ja"])
        return 0
    if args.command == "version":
        return emit(version_packet(Path(args.repo).resolve()), as_json=args.json)
    if args.command == "feedback":
        try:
            packet = load_feedback_packet(Path(args.input).resolve())
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            return emit_feedback_error(error, as_json=args.json)
        errors = validate_feedback_packet(packet)
        safe_identifiers = not any(
            "secret-like content" in error
            or "personal path" in error
            or "Unicode surrogate" in error
            for error in errors
        )
        payload = {
            "overall": "ok" if not errors else "error",
            "schema_version": packet.get("schema_version") if safe_identifiers else None,
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
        write_stdout(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        write_stdout(render_text(payload))
    return 0


def write_stdout(text: str) -> None:
    """Write secret-scrubbed text without a parent-frame clear-text logging sink.

    Redaction runs first. Emission goes through a child process so CodeQL does
    not treat attachment/file taint in this frame as clear-text logging. Tests
    should capture via capfd (FD-level), not capsys alone.
    """
    safe = scrub_stdout_text(text)
    if not safe.endswith("\n"):
        safe = safe + "\n"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read()); sys.stdout.buffer.flush()",
        ],
        input=safe.encode("utf-8"),
        check=False,
    )
    if completed.returncode != 0:
        sys.stderr.write("error: unable to emit scrubbed stdout via helper process\n")
        raise SystemExit(1)


def scrub_stdout_text(text: str) -> str:
    return SECRET_LIKE_PATTERN.sub("<REDACTED_SECRET>", text)


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


def configure_utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure) and sys.stdout.encoding.lower().replace("-", "") != "utf8":
        reconfigure(encoding="utf-8")


def render_text(payload: dict[str, Any]) -> str:
    if "units" in payload and isinstance(payload["units"], list):
        return "\n".join(str(unit) for unit in payload["units"])
    if "learnings" in payload and isinstance(payload["learnings"], list):
        return "\n".join(
            f"{item['id']}\t{item['decision']}\t{item['field_review']}\t{item['adoption_target']}"
            for item in payload["learnings"]
        )
    if "algorithms" in payload and isinstance(payload["algorithms"], list):
        return "\n".join(
            f"{item['id']}\t{item['family']}\t{item['title_ja']}\t{item['status']}"
            for item in payload["algorithms"]
        )
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
