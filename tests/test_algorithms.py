import json
from pathlib import Path

import pytest

from engineering_brain.algorithms import (
    algorithm_catalog,
    compare_algorithms,
    infer_algorithm_inputs,
    select_algorithms,
    validate_algorithm,
)
from engineering_brain.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_catalog_covers_core_algorithm_families() -> None:
    algorithms = algorithm_catalog()
    families = {algorithm.family for algorithm in algorithms}

    assert {
        "探索",
        "整列",
        "グラフ",
        "動的計画法",
        "文字列",
        "集合照合",
        "信頼性",
        "ストリーム",
    }.issubset(families)
    assert len(algorithms) >= 24


def test_catalog_entries_have_decision_metadata() -> None:
    algorithm = next(item for item in algorithm_catalog() if item.id == "binary_search")

    assert algorithm.problem_signals == ("ordered_lookup", "sorted_input", "random_access")
    assert algorithm.preconditions
    assert algorithm.avoid_when
    assert algorithm.complexity["time"] == "O(log n)"
    assert algorithm.tradeoffs
    assert algorithm.verification
    assert algorithm.source_refs


def test_select_algorithms_is_deterministic_and_explains_scores() -> None:
    first = select_algorithms(
        signals=["ordered_lookup", "sorted_input", "random_access"],
        constraints=[],
        limit=3,
    )
    second = select_algorithms(
        signals=["random_access", "ordered_lookup", "sorted_input"],
        constraints=[],
        limit=3,
    )

    assert [item["id"] for item in first] == [item["id"] for item in second]
    assert first[0]["id"] == "binary_search"
    assert first[0]["matched_signals"] == ["ordered_lookup", "random_access", "sorted_input"]
    assert first[0]["score"] > first[1]["score"]


def test_select_algorithms_penalizes_avoid_conditions() -> None:
    selected = select_algorithms(
        signals=["shortest_path", "weighted_graph"],
        constraints=["negative_edge"],
        limit=5,
    )
    by_id = {item["id"]: item for item in selected}

    assert by_id["bellman_ford"]["score"] > by_id["dijkstra"]["score"]
    assert by_id["dijkstra"]["matched_avoid"] == ["negative_edge"]


def test_compare_algorithms_returns_same_fields_in_requested_order() -> None:
    comparison = compare_algorithms(["hash_index", "binary_search"])

    assert [item["id"] for item in comparison] == ["hash_index", "binary_search"]
    assert set(comparison[0]) == {
        "id",
        "title_ja",
        "family",
        "status",
        "preconditions",
        "avoid_when",
        "complexity",
        "tradeoffs",
        "verification",
        "source_refs",
    }


def test_validate_algorithm_rejects_unknown_status() -> None:
    raw = {
        "id": "broken",
        "title_ja": "壊れた候補",
        "family": "探索",
        "status": "unknown",
        "problem_signals": ["lookup"],
        "preconditions": ["none"],
        "avoid_when": ["none"],
        "complexity": {"time": "O(1)", "space": "O(1)"},
        "tradeoffs": ["none"],
        "verification": ["test"],
        "source_refs": ["reference"],
    }

    with pytest.raises(ValueError, match="invalid status"):
        validate_algorithm(raw)


def test_algorithm_schema_is_valid_json_and_requires_decision_fields() -> None:
    schema = json.loads((ROOT / "schemas" / "algorithm-entry.schema.json").read_text(encoding="utf-8"))

    assert schema["$schema"].startswith("https://json-schema.org/")
    assert {
        "problem_signals",
        "preconditions",
        "avoid_when",
        "complexity",
        "tradeoffs",
        "verification",
        "source_refs",
    }.issubset(schema["required"])


def test_cli_algorithms_select_and_compare_emit_json(capsys) -> None:
    code = main(
        [
            "algorithms",
            "select",
            "--signal",
            "ordered_lookup",
            "--signal",
            "sorted_input",
            "--signal",
            "random_access",
            "--json",
        ]
    )
    selected = json.loads(capsys.readouterr().out)

    assert code == 0
    assert selected["selection"][0]["id"] == "binary_search"

    code = main(
        [
            "algorithms",
            "compare",
            "--id",
            "binary_search",
            "--id",
            "hash_index",
            "--json",
        ]
    )
    compared = json.loads(capsys.readouterr().out)

    assert code == 0
    assert [item["id"] for item in compared["comparison"]] == ["binary_search", "hash_index"]


@pytest.mark.parametrize(
    ("task", "expected_signals", "expected_constraints", "excluded"),
    [
        (
            "unweighted graph shortest path",
            {"unweighted_graph", "shortest_path"},
            set(),
            {"weighted_graph"},
        ),
        ("unsorted input", set(), {"input_unsorted"}, {"sorted_input"}),
        (
            "non-negative edge weighted graph",
            {"non_negative_edge", "weighted_graph"},
            set(),
            {"negative_edge"},
        ),
    ],
)
def test_infer_algorithm_inputs_does_not_match_overlapping_aliases(
    task: str,
    expected_signals: set[str],
    expected_constraints: set[str],
    excluded: set[str],
) -> None:
    signals, constraints = infer_algorithm_inputs(task)

    assert expected_signals.issubset(signals)
    assert expected_constraints.issubset(constraints)
    assert excluded.isdisjoint(signals)
    assert excluded.isdisjoint(constraints)


def test_concurrency_limit_selects_bounded_concurrency_not_token_bucket() -> None:
    signals, constraints = infer_algorithm_inputs("同時実行の並行数を制限する")
    selected = select_algorithms(signals=signals, constraints=constraints)
    selected_ids = [item["id"] for item in selected]

    assert selected_ids[0] == "bounded_concurrency"
    assert "token_bucket" not in selected_ids


def test_stable_rescan_requires_independent_completeness_evidence() -> None:
    entry = next(item for item in algorithm_catalog() if item.id == "stable_rescan")
    verification = " ".join(entry.verification)

    assert "独立" in verification
    assert any(term in verification for term in ("総件数", "cursor", "shard", "ID集合"))
