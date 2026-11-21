"""Comprehensive Tests for Graph Coloring Algorithms Suite.

PRD §12, §20, §26.3, Implementation.md Phase 7:
Tests Greedy, Welsh-Powell, DSATUR (linear & heap), input guards,
independent validator, precolors, locked conflict detection,
order sensitivity, determinism, metrics, trace generation,
and benchmark harness.
"""

import random

import pytest

from app.algorithms import (
    ColoringException,
    compute_coloring_metrics,
    dsatur,
    greedy_color,
    validate_coloring,
    welsh_powell,
)
from app.algorithms.guards import validate_graph_input
from app.algorithms.types import AdjacencyList
from app.scripts.benchmark_algorithms import (
    benchmark_suite,
    generate_bipartite_graph,
    generate_complete_graph,
    generate_cycle_graph,
    generate_erdos_renyi_graph,
)


# ==============================================================================
# 1. Standard Graph Families (PRD §26.3)
# ==============================================================================
def test_empty_graph():
    """Empty graph produces 0 colors, valid=True."""
    adj: AdjacencyList = {}
    r_greedy = greedy_color(adj)
    r_wp = welsh_powell(adj)
    r_dsatur = dsatur(adj)

    for r in [r_greedy, r_wp, r_dsatur]:
        assert r.color_count == 0
        assert len(r.colors) == 0
        assert r.valid is True


def test_single_vertex():
    """Single isolated vertex produces 1 color (color 0)."""
    adj: AdjacencyList = {"v1": set()}
    for algo_fn in [greedy_color, welsh_powell, dsatur]:
        r = algo_fn(adj)
        assert r.color_count == 1
        assert r.colors["v1"] == 0
        assert r.valid is True


def test_no_edges_graph():
    """Graph with 10 vertices and no edges needs only 1 color (all color 0)."""
    adj: AdjacencyList = {f"v{i}": set() for i in range(10)}
    for algo_fn in [greedy_color, welsh_powell, dsatur]:
        r = algo_fn(adj)
        assert r.color_count == 1
        assert all(c == 0 for c in r.colors.values())
        assert r.valid is True


def test_complete_graph_kn():
    """Complete graph K_n requires exactly n colors."""
    n = 6
    adj = generate_complete_graph(n)
    for algo_fn in [greedy_color, welsh_powell, dsatur]:
        r = algo_fn(adj)
        assert r.color_count == n
        assert len(set(r.colors.values())) == n
        assert r.valid is True


def test_bipartite_graph():
    """Bipartite graph has chromatic number 2."""
    adj = generate_bipartite_graph(10, p=0.4, seed=123)
    # DSATUR always colors bipartite graphs in <= 2 colors
    r_dsatur = dsatur(adj)
    assert r_dsatur.color_count <= 2
    assert r_dsatur.valid is True

    r_wp = welsh_powell(adj)
    assert r_wp.valid is True


def test_cycles_even_and_odd():
    """Even cycle has chromatic number 2; odd cycle has chromatic number 3."""
    # Even cycle C4 -> 2 colors
    c4 = generate_cycle_graph(4)
    assert dsatur(c4).color_count == 2
    assert welsh_powell(c4).color_count == 2

    # Odd cycle C5 -> 3 colors
    c5 = generate_cycle_graph(5)
    assert dsatur(c5).color_count == 3
    assert welsh_powell(c5).color_count == 3


def test_disconnected_cliques():
    """Two disconnected triangles K3 + K3 require 3 colors."""
    adj: AdjacencyList = {
        # First triangle
        "a1": {"a2", "a3"},
        "a2": {"a1", "a3"},
        "a3": {"a1", "a2"},
        # Second triangle
        "b1": {"b2", "b3"},
        "b2": {"b1", "b3"},
        "b3": {"b1", "b2"},
    }
    for algo_fn in [greedy_color, welsh_powell, dsatur]:
        r = algo_fn(adj)
        assert r.color_count == 3
        assert r.valid is True


def test_crown_graph_order_sensitivity():
    """
    Crown graph (K_3,3 minus a matching):
    Adversarial ordering causes Greedy to use 3 colors while Welsh-Powell / DSATUR use 2 colors.
    Demonstrates why DSATUR and Welsh-Powell improve upon naive Greedy.
    """
    # Crown graph of order 6: vertices {a1, a2, a3, b1, b2, b3}
    # Edges between a_i and b_j for i != j
    adj: AdjacencyList = {
        "a1": {"b2", "b3"},
        "a2": {"b1", "b3"},
        "a3": {"b1", "b2"},
        "b1": {"a2", "a3"},
        "b2": {"a1", "a3"},
        "b3": {"a1", "a2"},
    }
    # Adversarial ordering: a1, b1, a2, b2, a3, b3
    adv_order = ["a1", "b1", "a2", "b2", "a3", "b3"]
    r_greedy_adv = greedy_color(adj, order=adv_order)
    assert r_greedy_adv.color_count == 3  # Suboptimal 3 colors

    # DSATUR handles crown graph with optimal 2 colors
    r_dsatur = dsatur(adj)
    assert r_dsatur.color_count == 2
    assert r_dsatur.valid is True


# ==============================================================================
# 2. Input Guards and Conflict Rejections (P7.2, P7.17)
# ==============================================================================
def test_guard_rejects_self_loop():
    """Graph with self-loop raises SELF_LOOP_DETECTED."""
    adj: AdjacencyList = {"v1": {"v1"}}
    with pytest.raises(ColoringException) as exc_info:
        greedy_color(adj)
    assert exc_info.value.code == "SELF_LOOP_DETECTED"


def test_guard_rejects_asymmetric_adjacency():
    """Graph with asymmetric edge raises ASYMMETRIC_GRAPH."""
    adj: AdjacencyList = {"v1": {"v2"}, "v2": set()}
    with pytest.raises(ColoringException) as exc_info:
        welsh_powell(adj)
    assert exc_info.value.code == "ASYMMETRIC_GRAPH"


def test_guard_rejects_unknown_neighbor():
    """Graph with missing vertex in adj dict raises UNKNOWN_NEIGHBOR."""
    adj: AdjacencyList = {"v1": {"v_missing"}}
    with pytest.raises(ColoringException) as exc_info:
        validate_graph_input(adj)
    assert exc_info.value.code == "UNKNOWN_NEIGHBOR"


def test_guard_rejects_locked_conflict():
    """Adjacent vertices precolored with the same color raises LOCKED_CONFLICT (P7.17)."""
    adj: AdjacencyList = {"e1": {"e2"}, "e2": {"e1"}}
    precolored = {"e1": 0, "e2": 0}  # Conflict! Both locked to slot 0

    with pytest.raises(ColoringException) as exc_info:
        dsatur(adj, precolored=precolored)
    assert exc_info.value.code == "LOCKED_CONFLICT"
    assert "e1" in exc_info.value.message and "e2" in exc_info.value.message


# ==============================================================================
# 3. Precolored Support and Determinism (P7.3, P7.16)
# ==============================================================================
def test_precolored_vertices_preserved_and_respected():
    """Precolored vertices are preserved, never recolored, and forbid their color to neighbors."""
    adj: AdjacencyList = {
        "v1": {"v2", "v3"},
        "v2": {"v1"},
        "v3": {"v1"},
    }
    precolored = {"v1": 5}  # Lock v1 to color 5

    for algo_fn in [greedy_color, welsh_powell, dsatur]:
        r = algo_fn(adj, precolored=precolored)
        assert r.colors["v1"] == 5
        # v2 and v3 cannot have color 5
        assert r.colors["v2"] != 5
        assert r.colors["v3"] != 5
        assert r.valid is True


def test_deterministic_output_stability():
    """Running algorithm twice or with shuffled dict order produces identical colors."""
    n = 20
    adj = generate_erdos_renyi_graph(n, p=0.25, seed=99)

    r1 = dsatur(adj, deterministic=True)
    r2 = dsatur(adj, deterministic=True)
    assert r1.colors == r2.colors
    assert r1.execution_time_ms >= 0

    # Shuffled input dict keys
    keys = list(adj.keys())
    random.Random(42).shuffle(keys)
    shuffled_adj = {k: adj[k] for k in keys}

    r3 = dsatur(shuffled_adj, deterministic=True)
    assert r1.colors == r3.colors


# ==============================================================================
# 4. DSATUR Linear Scan vs Heap Equivalence (P7.11)
# ==============================================================================
def test_dsatur_linear_vs_heap_equivalence():
    """DSATUR linear scan and heap-based variants produce 100% identical outputs."""
    for n in [15, 30, 50]:
        adj = generate_erdos_renyi_graph(n, p=0.2, seed=n)
        r_linear = dsatur(adj, deterministic=True, use_heap=False)
        r_heap = dsatur(adj, deterministic=True, use_heap=True)

        assert r_linear.color_count == r_heap.color_count
        assert r_linear.colors == r_heap.colors
        assert r_heap.valid is True


# ==============================================================================
# 5. Independent Validator Verification (P7.13, P7.14)
# ==============================================================================
def test_independent_validator_catches_invalid_coloring():
    """Validator catches uncolored vertices, conflicts, and negative colors."""
    adj: AdjacencyList = {"a": {"b"}, "b": {"a"}}

    # Valid
    assert validate_coloring(adj, {"a": 0, "b": 1}).valid is True

    # 1. Monochromatic conflict
    val_conflict = validate_coloring(adj, {"a": 0, "b": 0})
    assert val_conflict.valid is False
    assert len(val_conflict.conflicts) == 1

    # 2. Uncolored vertex
    val_uncolored = validate_coloring(adj, {"a": 0})
    assert val_uncolored.valid is False
    assert "b" in val_uncolored.uncolored

    # 3. Negative color
    val_neg = validate_coloring(adj, {"a": -1, "b": 1})
    assert val_neg.valid is False


# ==============================================================================
# 6. Quality Metrics & Educational Trace (P7.12, P7.15)
# ==============================================================================
def test_coloring_metrics():
    """compute_coloring_metrics accurately reports class sizes, ratio, and imbalance."""
    colors = {"v1": 0, "v2": 0, "v3": 1, "v4": 2}
    metrics = compute_coloring_metrics(colors)
    assert metrics["color_count"] == 3
    assert metrics["class_sizes"] == {0: 2, 1: 1, 2: 1}
    assert metrics["max_class_size"] == 2
    assert metrics["min_class_size"] == 1
    assert metrics["imbalance_score"] == 1
    assert metrics["groups_by_color"][0] == ["v1", "v2"]


def test_dsatur_educational_trace():
    """DSATUR with trace=True produces step-by-step trace with expected details."""
    adj: AdjacencyList = {
        "a": {"b", "c"},
        "b": {"a", "c"},
        "c": {"a", "b"},
    }
    r = dsatur(adj, trace=True)
    assert r.trace is not None
    assert len(r.trace) == 3

    # Step 1
    s1 = r.trace[0]
    assert s1.step == 1
    assert s1.degree == 2
    assert s1.saturation_degree == 0
    assert s1.assigned_color == 0

    # Step 2: saturation of remaining vertices was updated
    s2 = r.trace[1]
    assert s2.step == 2
    assert s2.saturation_degree == 1  # Neighbor color 0 assigned in step 1
    assert s2.assigned_color == 1


# ==============================================================================
# 7. Benchmarking Suite Execution (P7.18)
# ==============================================================================
def test_benchmark_suite_executes():
    """Verifies that the benchmark harness runs and returns non-empty results."""
    results = benchmark_suite(sizes=[10, 20])
    assert len(results) > 0
    first = results[0]
    assert "graph_name" in first
    assert "algorithm" in first
    assert "colors" in first
    assert first["valid"] is True


def test_guards_additional_exception_branches():
    """Covers precolored validation failure branches in guards.py."""
    adj = {"A": {"B"}, "B": {"A"}}

    # Unknown precolored vertex
    with pytest.raises(ColoringException) as exc1:
        validate_graph_input(adj, precolored={"NON_EXISTENT": 0})
    assert exc1.value.code == "UNKNOWN_PRECOLORED_VERTEX"

    # Negative precolor
    with pytest.raises(ColoringException) as exc2:
        validate_graph_input(adj, precolored={"A": -1})
    assert exc2.value.code == "INVALID_PRECOLOR"

    # Non-integer precolor
    with pytest.raises(ColoringException) as exc3:
        validate_graph_input(adj, precolored={"A": "zero"})  # type: ignore[arg-type]
    assert exc3.value.code == "INVALID_PRECOLOR"


def test_welsh_powell_non_deterministic():
    """Covers non-deterministic Welsh-Powell sort branch."""
    adj = {"A": {"B", "C"}, "B": {"A"}, "C": {"A"}}
    res = welsh_powell(adj, deterministic=False)
    assert res.color_count == 2


def test_greedy_ordering_branches():
    """Covers alternative vertex ordering branches in greedy_color."""
    adj = {"A": {"B"}, "B": {"A", "C"}, "C": {"B"}}

    # by_degree_desc with deterministic=True and deterministic=False
    res1 = greedy_color(adj, order="by_degree_desc", deterministic=True)
    assert res1.color_count == 2

    res2 = greedy_color(adj, order="by_degree_desc", deterministic=False)
    assert res2.color_count == 2

    # as_given
    res3 = greedy_color(adj, order="as_given")
    assert res3.color_count == 2

    # custom order permutation with missing/extra vertex
    with pytest.raises(ColoringException) as exc1:
        greedy_color(adj, order=["A", "B"])
    assert exc1.value.code == "INVALID_ORDERING"

    # unknown ordering string
    with pytest.raises(ColoringException) as exc2:
        greedy_color(adj, order="random_invalid_ordering")
    assert exc2.value.code == "INVALID_ORDERING"


def test_dsatur_heap_trace_and_stale_update():
    """Covers heap-based DSATUR with tracing, stale updates, and non-deterministic linear."""
    # Complete graph K_4 forces multiple saturation degree increments
    adj_k4 = {
        "1": {"2", "3", "4"},
        "2": {"1", "3", "4"},
        "3": {"1", "2", "4"},
        "4": {"1", "2", "3"},
    }
    # Trace with heap variant
    res_heap = dsatur(adj_k4, use_heap=True, trace=True)
    assert res_heap.color_count == 4
    assert len(res_heap.trace) == 4

    # Non-deterministic linear variant
    res_lin_nondet = dsatur(adj_k4, use_heap=False, deterministic=False)
    assert res_lin_nondet.color_count == 4
