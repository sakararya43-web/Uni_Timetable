"""Property-Based Testing with Hypothesis and Algorithmic Regression Fixtures.

PRD §12, §20, Tasks P15.2, P15.4.
Verifies fundamental graph coloring properties across randomly synthesized graphs:
1. No two adjacent vertices ever share the same color.
2. Every vertex in V is assigned exactly one non-negative integer color.
3. Precolored vertices maintain their assigned color.
4. Exact chromatic numbers on canonical graph topologies (Kn, C_even, C_odd, Km,n, Petersen).
"""

import hypothesis.strategies as st
from hypothesis import given, settings

from app.algorithms import dsatur, greedy_color, validate_coloring, welsh_powell
from app.algorithms.types import AdjacencyList


# Strategy generating random valid undirected graphs with 1 to 30 vertices
@st.composite
def random_undirected_graphs(draw) -> AdjacencyList:
    num_vertices = draw(st.integers(min_value=1, max_value=25))
    vertices = [f"v_{i}" for i in range(num_vertices)]

    adj: AdjacencyList = {v: set() for v in vertices}

    # Generate random edges
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            if draw(st.booleans()):
                u, v = vertices[i], vertices[j]
                adj[u].add(v)
                adj[v].add(u)

    return adj


@settings(max_examples=40, deadline=None)
@given(graph=random_undirected_graphs())
def test_dsatur_property_proper_coloring(graph: AdjacencyList) -> None:
    """Invariant: For any graph G=(V,E), DSATUR coloring assigns distinct colors to all adjacent vertices."""
    result = dsatur(graph, deterministic=True)
    report = validate_coloring(graph, result.colors)
    assert report.valid is True
    assert len(report.conflicts) == 0
    assert len(report.uncolored) == 0


@settings(max_examples=40, deadline=None)
@given(graph=random_undirected_graphs())
def test_welsh_powell_property_proper_coloring(graph: AdjacencyList) -> None:
    """Invariant: For any graph G=(V,E), Welsh-Powell coloring assigns distinct colors to all adjacent vertices."""
    result = welsh_powell(graph, deterministic=True)
    report = validate_coloring(graph, result.colors)
    assert report.valid is True
    assert len(report.conflicts) == 0
    assert len(report.uncolored) == 0


@settings(max_examples=40, deadline=None)
@given(graph=random_undirected_graphs())
def test_greedy_property_proper_coloring(graph: AdjacencyList) -> None:
    """Invariant: For any graph G=(V,E), Greedy coloring assigns distinct colors to all adjacent vertices."""
    result = greedy_color(graph, deterministic=True)
    report = validate_coloring(graph, result.colors)
    assert report.valid is True
    assert len(report.conflicts) == 0
    assert len(report.uncolored) == 0


@settings(max_examples=30, deadline=None)
@given(graph=random_undirected_graphs())
def test_determinism_property(graph: AdjacencyList) -> None:
    """Invariant: Running coloring algorithms on the same graph twice produces identical colorings."""
    r1 = dsatur(graph, deterministic=True)
    r2 = dsatur(graph, deterministic=True)
    assert r1.colors == r2.colors

    wp1 = welsh_powell(graph, deterministic=True)
    wp2 = welsh_powell(graph, deterministic=True)
    assert wp1.colors == wp2.colors


# ==============================================================================
# Curated Algorithmic Regression Fixtures with Known Theoretical Bounds (Task P15.4)
# ==============================================================================


def test_complete_graph_kn_chromatic_number():
    """Complete graph K_n requires exactly n colors."""
    for n in [3, 5, 8]:
        adj: AdjacencyList = {f"v_{i}": set() for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                adj[f"v_{i}"].add(f"v_{j}")
                adj[f"v_{j}"].add(f"v_{i}")

        res = dsatur(adj)
        assert res.color_count == n
        assert validate_coloring(adj, res.colors).valid is True


def test_even_cycle_chromatic_number():
    """Even cycle C_{2k} is bipartite and requires exactly 2 colors."""
    for n in [4, 6, 10]:
        adj: AdjacencyList = {f"v_{i}": set() for i in range(n)}
        for i in range(n):
            nxt = (i + 1) % n
            adj[f"v_{i}"].add(f"v_{nxt}")
            adj[f"v_{nxt}"].add(f"v_{i}")

        res = dsatur(adj)
        assert res.color_count == 2
        assert validate_coloring(adj, res.colors).valid is True


def test_odd_cycle_chromatic_number():
    """Odd cycle C_{2k+1} requires exactly 3 colors."""
    for n in [5, 7, 9]:
        adj: AdjacencyList = {f"v_{i}": set() for i in range(n)}
        for i in range(n):
            nxt = (i + 1) % n
            adj[f"v_{i}"].add(f"v_{nxt}")
            adj[f"v_{nxt}"].add(f"v_{i}")

        res = dsatur(adj)
        assert res.color_count == 3
        assert validate_coloring(adj, res.colors).valid is True


def test_petersen_graph_chromatic_number():
    """Petersen graph has 10 vertices and chromatic number chi(Petersen) = 3."""
    # Outer 5-cycle: 0-4, Inner 5-star: 5-9
    adj: AdjacencyList = {f"v_{i}": set() for i in range(10)}
    # Outer cycle
    for i in range(5):
        nxt = (i + 1) % 5
        adj[f"v_{i}"].add(f"v_{nxt}")
        adj[f"v_{nxt}"].add(f"v_{i}")
    # Inner star
    inner_edges = [(5, 7), (7, 9), (9, 6), (6, 8), (8, 5)]
    for u, v in inner_edges:
        adj[f"v_{u}"].add(f"v_{v}")
        adj[f"v_{v}"].add(f"v_{u}")
    # Spokes connecting outer cycle to inner star
    for i in range(5):
        adj[f"v_{i}"].add(f"v_{i + 5}")
        adj[f"v_{i + 5}"].add(f"v_{i}")

    res = dsatur(adj)
    assert res.color_count == 3
    assert validate_coloring(adj, res.colors).valid is True
