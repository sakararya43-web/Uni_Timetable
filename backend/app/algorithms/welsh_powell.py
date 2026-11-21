"""Welsh-Powell Vertex Coloring Algorithm (Algorithm B).

PRD §12.3, Tasks P7.9, P7.10:
Sorts vertices by descending degree with deterministic stable-key tie-breaking,
then executes greedy sequential coloring.

Complexity:
- Time Complexity: O(V log V + E) due to the initial sort by degree followed by linear neighbor scans.
- Space Complexity: O(V + E) for adjacency list, colors dict, and forbidden color sets.
"""

from typing import Any

from app.algorithms.greedy import greedy_color
from app.algorithms.guards import compute_graph_fingerprint, validate_graph_input
from app.algorithms.types import (
    WELSH_POWELL_VERSION,
    AdjacencyList,
    ColoringResult,
    Vertex,
    stable_key,
)


def welsh_powell(
    adj: AdjacencyList,
    precolored: dict[Vertex, int] | None = None,
    deterministic: bool = True,
) -> ColoringResult:
    """
    Executes Welsh-Powell vertex coloring on graph G = (V, E) (Tasks P7.9, P7.10).

    Args:
        adj: Undirected adjacency list representation.
        precolored: Optional pre-assigned {vertex: color} mapping.
        deterministic: If True, uses stable sorting on tie-breaks.

    Returns:
        ColoringResult containing colors, metrics, performance instrumentation, and validation.
    """
    # 1. Input guards (P7.2)
    validate_graph_input(adj, precolored)

    # 2. Sort vertices by descending degree, ties broken by stable ID (P7.9)
    all_vertices = set(adj.keys())
    if deterministic:
        sorted_order = sorted(all_vertices, key=lambda v: (-len(adj[v]), stable_key(v)))
    else:
        sorted_order = sorted(all_vertices, key=lambda v: -len(adj[v]))

    # 3. Delegate to greedy_color using the Welsh-Powell ordering
    result = greedy_color(
        adj=adj,
        order=sorted_order,
        precolored=precolored,
        deterministic=deterministic,
    )

    # 4. Re-tag with Welsh-Powell algorithm identity and version
    config: dict[str, Any] = {
        "order": "welsh_powell_degree_desc",
        "deterministic": deterministic,
        "precolored_count": len(precolored) if precolored else 0,
    }

    return ColoringResult(
        colors=result.colors,
        color_count=result.color_count,
        execution_time_ms=result.execution_time_ms,
        vertex_visits=result.vertex_visits,
        color_checks=result.color_checks,
        valid=result.valid,
        algorithm="welsh_powell",
        algorithm_version=WELSH_POWELL_VERSION,
        config=config,
        trace=None,
        graph_fingerprint=compute_graph_fingerprint(adj),
    )
