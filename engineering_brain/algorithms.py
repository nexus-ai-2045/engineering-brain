from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_CATALOG = PACKAGE_ROOT / "data" / "algorithms.json"
VALID_STATUSES = {"adopted", "candidate", "hold", "rejected"}


@dataclass(frozen=True)
class AlgorithmEntry:
    id: str
    title_ja: str
    family: str
    status: str
    problem_signals: tuple[str, ...]
    preconditions: tuple[str, ...]
    avoid_when: tuple[str, ...]
    complexity: dict[str, str]
    tradeoffs: tuple[str, ...]
    verification: tuple[str, ...]
    source_refs: tuple[str, ...]


def algorithm_catalog(path: Path = DEFAULT_CATALOG) -> list[AlgorithmEntry]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries: list[AlgorithmEntry] = []
    seen: set[str] = set()
    for raw in payload["algorithms"]:
        validate_algorithm(raw)
        if raw["id"] in seen:
            raise ValueError(f"duplicate algorithm id: {raw['id']}")
        seen.add(raw["id"])
        entries.append(_build_entry(raw))
    return entries


def validate_algorithm(raw: dict[str, Any]) -> None:
    required = {
        "id",
        "title_ja",
        "family",
        "status",
        "problem_signals",
        "preconditions",
        "avoid_when",
        "complexity",
        "tradeoffs",
        "verification",
        "source_refs",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise ValueError(f"algorithm {raw.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if raw["status"] not in VALID_STATUSES:
        raise ValueError(f"algorithm {raw['id']} has invalid status: {raw['status']}")
    for key in (
        "problem_signals",
        "preconditions",
        "avoid_when",
        "tradeoffs",
        "verification",
        "source_refs",
    ):
        if not isinstance(raw[key], list) or not raw[key]:
            raise ValueError(f"algorithm {raw['id']} has invalid {key}")
    if set(raw["complexity"]) != {"time", "space"}:
        raise ValueError(f"algorithm {raw['id']} complexity must contain time and space")


def select_algorithms(
    *,
    signals: Iterable[str],
    constraints: Iterable[str] = (),
    limit: int = 5,
    family: str | None = None,
    path: Path = DEFAULT_CATALOG,
) -> list[dict[str, Any]]:
    normalized_signals = {_normalize(item) for item in signals if item}
    normalized_constraints = {_normalize(item) for item in constraints if item}
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for entry in algorithm_catalog(path):
        if entry.status not in {"adopted", "candidate"}:
            continue
        if family and _normalize(entry.family) != _normalize(family):
            continue
        entry_signals = {_normalize(item) for item in entry.problem_signals}
        avoid = {_normalize(item) for item in entry.avoid_when}
        matched_signals = sorted(normalized_signals.intersection(entry_signals))
        matched_avoid = sorted((normalized_signals | normalized_constraints).intersection(avoid))
        score = len(matched_signals) * 10 - len(matched_avoid) * 12
        if entry.status == "candidate":
            score -= 1
        ranked.append(
            (
                score,
                entry.id,
                {
                    "id": entry.id,
                    "title_ja": entry.title_ja,
                    "family": entry.family,
                    "status": entry.status,
                    "score": score,
                    "matched_signals": matched_signals,
                    "matched_avoid": matched_avoid,
                    "preconditions": list(entry.preconditions),
                    "complexity": dict(entry.complexity),
                    "tradeoffs": list(entry.tradeoffs),
                    "verification": list(entry.verification),
                },
            )
        )
    ranked.sort(key=lambda item: (-item[0], item[1]))
    useful = [item[2] for item in ranked if item[0] > 0]
    return useful[: max(0, limit)]


def compare_algorithms(ids: Iterable[str], path: Path = DEFAULT_CATALOG) -> list[dict[str, Any]]:
    by_id = {entry.id: entry for entry in algorithm_catalog(path)}
    result = []
    for algorithm_id in ids:
        if algorithm_id not in by_id:
            raise ValueError(f"unknown algorithm id: {algorithm_id}")
        entry = by_id[algorithm_id]
        result.append(
            {
                "id": entry.id,
                "title_ja": entry.title_ja,
                "family": entry.family,
                "status": entry.status,
                "preconditions": list(entry.preconditions),
                "avoid_when": list(entry.avoid_when),
                "complexity": dict(entry.complexity),
                "tradeoffs": list(entry.tradeoffs),
                "verification": list(entry.verification),
                "source_refs": list(entry.source_refs),
            }
        )
    return result


def infer_algorithm_inputs(task: str) -> tuple[list[str], list[str]]:
    normalized = task.lower()
    signal_aliases = {
        "ordered_lookup": ("二分探索", "ordered lookup", "sorted lookup"),
        "sorted_input": ("ソート済み", "sorted"),
        "random_access": ("random access", "配列"),
        "unweighted_graph": ("重みなし", "unweighted"),
        "weighted_graph": ("重み付き", "weighted"),
        "non_negative_edge": ("非負辺", "non-negative edge", "non negative edge"),
        "shortest_path": ("最短経路", "shortest path"),
        "dependency_order": ("依存順", "dependency order", "topological"),
        "optimal_substructure": ("最適部分構造", "dynamic programming", "dp"),
        "prefix_match": ("prefix", "前方一致"),
        "substring_search": ("部分文字列", "substring"),
        "set_equality": ("集合一致", "set equality", "完全性"),
        "stable_snapshot": ("安定走査", "stable snapshot", "再走査"),
        "transient_failure": ("retry", "再試行", "一時障害"),
        "incremental_sync": ("差分同期", "incremental sync"),
        "stream_membership": ("重複排除", "dedup", "stream membership"),
        "top_k": ("上位", "top k"),
        "range_query": ("範囲検索", "range query"),
        "concurrent_limit": ("並行数", "concurrency limit"),
    }
    constraint_aliases = {
        "negative_edge": ("負辺", "negative edge"),
        "memory_tight": ("メモリ制約", "memory tight", "low memory"),
        "input_unsorted": ("未整列", "unsorted"),
        "exact_required": ("厳密", "exact required", "完全一致"),
    }
    signals = [
        signal
        for signal, aliases in signal_aliases.items()
        if any(_contains_alias(normalized, alias) for alias in aliases)
    ]
    constraints = [
        constraint
        for constraint, aliases in constraint_aliases.items()
        if any(_contains_alias(normalized, alias) for alias in aliases)
        and not (
            constraint == "negative_edge"
            and any(
                _contains_alias(normalized, alias)
                for alias in signal_aliases["non_negative_edge"]
            )
        )
    ]
    return signals, constraints


def _build_entry(raw: dict[str, Any]) -> AlgorithmEntry:
    return AlgorithmEntry(
        id=raw["id"],
        title_ja=raw["title_ja"],
        family=raw["family"],
        status=raw["status"],
        problem_signals=tuple(raw["problem_signals"]),
        preconditions=tuple(raw["preconditions"]),
        avoid_when=tuple(raw["avoid_when"]),
        complexity=dict(raw["complexity"]),
        tradeoffs=tuple(raw["tradeoffs"]),
        verification=tuple(raw["verification"]),
        source_refs=tuple(raw["source_refs"]),
    )


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _contains_alias(text: str, alias: str) -> bool:
    if all(ord(character) < 128 for character in alias):
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])"
        return re.search(pattern, text) is not None
    return alias in text
