"""Greedy Vertex Coloring Algorithm (Algorithm A).

PRD §12.3, Tasks P7.6, P7.7, P7.8:
Assigns the smallest available non-negative color to each vertex in the
specified or default ordering.

Complexity:
- Time Complexity: O(V + E) neighbor scanning with set lookups; color search bounded by Delta + 1.
- Space Complexity: O(V + E) for adjacency list, colors dict, and forbidden color sets.
"""

import time
from typing import Any

from app.algorithms.guards import compute_graph_fingerprint, validate_graph_input
from app.algorithms.types import (
    GREEDY_VERSION,
    AdjacencyList,
    ColoringException,
    ColoringResult,
    Vertex,
    stable_key,
)
from app.algorithms.validators import validate_coloring


def greedy_color(
    adj: AdjacencyList,
    order: list[Vertex] | str | None = None,
    precolored: dict[Vertex, int] | None = None,
    deterministic: bool = True,
) -> ColoringResult:
    """
    Executes greedy vertex coloring on graph G = (V, E) (Tasks P7.6, P7.7).

    Args:
        adj: Undirected adjacency list representation.
        order: Ordering strategy ("by_id", "by_degree_desc", "as_given") or custom list of vertices.
        precolored: Optional pre-assigned {vertex: color} mapping.
        deterministic: If True, uses stable sorting on tie-breaks.

    Returns:
        ColoringResult containing colors, metrics, performance instrumentation, and validation.
    """
    # 1. Input guards (P7.2)
    validate_graph_input(adj, precolored)

    start_time = time.perf_counter()
    fingerprint = compute_graph_fingerprint(adj)
    all_vertices = set(adj.keys())

    # 2. Determine vertex ordering (P7.7)
    order_name = "by_id"
    if order is None or order == "by_id":
        order_list = sorted(all_vertices, key=stable_key) if deterministic else list(all_vertices)
        order_name = "by_id"
    elif order == "by_degree_desc":
        order_list = (
            sorted(all_vertices, key=lambda v: (-len(adj[v]), stable_key(v)))
            if deterministic
            else sorted(all_vertices, key=lambda v: -len(adj[v]))
        )
        order_name = "by_degree_desc"
    elif order == "as_given":
        order_list = list(adj.keys())
        order_name = "as_given"
    elif isinstance(order, list):
        if set(order) != all_vertices or len(order) != len(all_vertices):
            raise ColoringException(
                code="INVALID_ORDERING",
                message="Custom order list must be a permutation of all graph vertices.",
            )
        order_list = list(order)
        order_name = "custom"
    else:
        raise ColoringException(
            code="INVALID_ORDERING",
            message=f"Unknown ordering strategy '{order}'. Allowed: 'by_id', 'by_degree_desc', 'as_given', or list.",
        )

    # 3. Initialize colors and apply precolors (P7.16)
    colors: dict[Vertex, int] = dict(precolored) if precolored else {}
    vertex_visits = 0
    color_checks = 0

    # 4. Coloring loop
    for v in order_list:
        if v in colors:
            continue  # Precolored vertices are preserved and never recolored

        vertex_visits += 1
        # Collect colors of colored neighbors
        forbidden: set[int] = set()
        neighbors = sorted(adj[v], key=stable_key) if deterministic else adj[v]
        for nbr in neighbors:
            if nbr in colors:
                forbidden.add(colors[nbr])

        # Assign the smallest available non-negative integer color
        assigned_color = 0
        while True:
            color_checks += 1
            if assigned_color not in forbidden:
                break
            assigned_color += 1

        colors[v] = assigned_color

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # 5. Independent validation check (P7.13, P7.14)
    val = validate_coloring(adj, colors)
    if not val.valid:
        raise ColoringException(
            code="INVALID_COLORING",
            message=f"Greedy coloring failed independent verification: {val.error_message}",
        )

    config: dict[str, Any] = {
        "order": order_name,
        "deterministic": deterministic,
        "precolored_count": len(precolored) if precolored else 0,
    }

    return ColoringResult(
        colors=colors,
        color_count=len(set(colors.values())) if colors else 0,
        execution_time_ms=round(elapsed_ms, 3),
        vertex_visits=vertex_visits,
        color_checks=color_checks,
        valid=val.valid,
        algorithm="greedy",
        algorithm_version=GREEDY_VERSION,
        config=config,
        trace=None,
        graph_fingerprint=fingerprint,
    )
