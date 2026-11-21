"""DSATUR (Degree of Saturation) Vertex Coloring Algorithm (Algorithm C - Primary).

PRD §12.3, Tasks P7.11, P7.12:
Implements Daniel Brélaz's DSATUR heuristic:
1. Dynamically selects the uncolored vertex with highest saturation degree (distinct colors in neighborhood).
2. Breaks ties using vertex degree in graph, then deterministic stable ID.
3. Provides an educational trace generator and an optional heap-accelerated variant.

Complexity:
- Linear scan selection: O(V^2 + E) time, O(V + E) space.
- Heap-based variant: O((V + E) log V) time, O(V + E) space.
"""

import heapq
import time
from typing import Any

from app.algorithms.guards import compute_graph_fingerprint, validate_graph_input
from app.algorithms.types import (
    DSATUR_VERSION,
    AdjacencyList,
    ColoringException,
    ColoringResult,
    TraceStep,
    Vertex,
    stable_key,
)
from app.algorithms.validators import validate_coloring


def dsatur(
    adj: AdjacencyList,
    precolored: dict[Vertex, int] | None = None,
    deterministic: bool = True,
    trace: bool = False,
    use_heap: bool = False,
    max_trace_steps: int = 500,
) -> ColoringResult:
    """
    Executes DSATUR vertex coloring on graph G = (V, E) (Tasks P7.11, P7.12).

    Args:
        adj: Undirected adjacency list representation.
        precolored: Optional pre-assigned {vertex: color} mapping.
        deterministic: If True, uses stable sorting on tie-breaks.
        trace: If True, produces step-by-step educational trace records.
        use_heap: If True, uses lazy-deletion priority queue for O((V+E) log V) selection.
        max_trace_steps: Maximum educational trace steps recorded.

    Returns:
        ColoringResult containing colors, metrics, performance instrumentation, and trace.
    """
    # 1. Input guards (P7.2, P7.17)
    validate_graph_input(adj, precolored)

    start_time = time.perf_counter()
    fingerprint = compute_graph_fingerprint(adj)
    all_vertices = set(adj.keys())

    # 2. Maintain neighbor colors sets for degree of saturation (P7.11)
    neighbor_colors: dict[Vertex, set[int]] = {v: set() for v in all_vertices}
    colors: dict[Vertex, int] = dict(precolored) if precolored else {}

    # Initial saturation from precolored vertices
    for u, col in colors.items():
        for nbr in adj.get(u, set()):
            neighbor_colors[nbr].add(col)

    uncolored = set(all_vertices) - set(colors.keys())
    vertex_visits = 0
    color_checks = 0
    trace_steps: list[TraceStep] = []

    # 3. Algorithm execution
    if use_heap:
        # Heap-based variant with lazy deletion
        heap: list[tuple[int, int, str, Vertex]] = []
        for v in uncolored:
            sat = len(neighbor_colors[v])
            deg = len(adj[v])
            key_v = stable_key(v) if deterministic else str(v)
            heapq.heappush(heap, (-sat, -deg, key_v, v))

        while uncolored:
            # Pop maximal candidate: highest sat (-sat min), highest deg (-deg min), stable_key
            best_v: Vertex | None = None
            while heap:
                neg_sat, neg_deg, key_v, cand_v = heapq.heappop(heap)
                if cand_v not in uncolored:
                    continue
                # Verify saturation hasn't changed since pushed
                actual_sat = len(neighbor_colors[cand_v])
                if -neg_sat != actual_sat:
                    heapq.heappush(heap, (-actual_sat, neg_deg, key_v, cand_v))
                    continue
                best_v = cand_v
                break

            if best_v is None:
                break

            uncolored.remove(best_v)
            vertex_visits += 1

            # Assign smallest available non-negative color
            forbidden = neighbor_colors[best_v]
            assigned_color = 0
            while True:
                color_checks += 1
                if assigned_color not in forbidden:
                    break
                assigned_color += 1

            colors[best_v] = assigned_color

            # Update neighbors' saturation and push updated entries into heap
            updated_nbrs: list[Vertex] = []
            neighbors = sorted(adj[best_v], key=stable_key) if deterministic else adj[best_v]
            for nbr in neighbors:
                if nbr in uncolored:
                    if assigned_color not in neighbor_colors[nbr]:
                        neighbor_colors[nbr].add(assigned_color)
                        updated_nbrs.append(nbr)
                        new_sat = len(neighbor_colors[nbr])
                        deg_nbr = len(adj[nbr])
                        k_nbr = stable_key(nbr) if deterministic else str(nbr)
                        heapq.heappush(heap, (-new_sat, -deg_nbr, k_nbr, nbr))

            if trace and len(trace_steps) < max_trace_steps:
                trace_steps.append(
                    TraceStep(
                        step=len(trace_steps) + 1,
                        selected_vertex=best_v,
                        degree=len(adj[best_v]),
                        saturation_degree=len(forbidden),
                        forbidden_colors=sorted(forbidden),
                        assigned_color=assigned_color,
                        neighbor_saturations_updated=sorted(updated_nbrs, key=stable_key)
                        if deterministic
                        else updated_nbrs,
                    )
                )

    else:
        # Linear scan variant (O(V^2 + E))
        while uncolored:
            vertex_visits += 1
            # Selection rule: maximize saturation, then degree, then stable_key
            if deterministic:
                best_v = min(
                    uncolored,
                    key=lambda v: (
                        -len(neighbor_colors[v]),
                        -len(adj[v]),
                        stable_key(v),
                    ),
                )
            else:
                best_v = min(
                    uncolored,
                    key=lambda v: (-len(neighbor_colors[v]), -len(adj[v])),
                )

            uncolored.remove(best_v)

            # Assign smallest available non-negative color
            forbidden = neighbor_colors[best_v]
            assigned_color = 0
            while True:
                color_checks += 1
                if assigned_color not in forbidden:
                    break
                assigned_color += 1

            colors[best_v] = assigned_color

            # Update neighbors' saturation
            updated_nbrs = []
            neighbors = sorted(adj[best_v], key=stable_key) if deterministic else adj[best_v]
            for nbr in neighbors:
                if nbr in uncolored:
                    if assigned_color not in neighbor_colors[nbr]:
                        neighbor_colors[nbr].add(assigned_color)
                        updated_nbrs.append(nbr)

            if trace and len(trace_steps) < max_trace_steps:
                trace_steps.append(
                    TraceStep(
                        step=len(trace_steps) + 1,
                        selected_vertex=best_v,
                        degree=len(adj[best_v]),
                        saturation_degree=len(forbidden),
                        forbidden_colors=sorted(forbidden),
                        assigned_color=assigned_color,
                        neighbor_saturations_updated=sorted(updated_nbrs, key=stable_key)
                        if deterministic
                        else updated_nbrs,
                    )
                )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # 4. Independent validation check (P7.13, P7.14)
    val = validate_coloring(adj, colors)
    if not val.valid:
        raise ColoringException(
            code="INVALID_COLORING",
            message=f"DSATUR coloring failed independent verification: {val.error_message}",
        )

    config: dict[str, Any] = {
        "variant": "heap" if use_heap else "linear_scan",
        "deterministic": deterministic,
        "trace": trace,
        "precolored_count": len(precolored) if precolored else 0,
    }

    return ColoringResult(
        colors=colors,
        color_count=len(set(colors.values())) if colors else 0,
        execution_time_ms=round(elapsed_ms, 3),
        vertex_visits=vertex_visits,
        color_checks=color_checks,
        valid=val.valid,
        algorithm="dsatur",
        algorithm_version=DSATUR_VERSION,
        config=config,
        trace=trace_steps if trace else None,
        graph_fingerprint=fingerprint,
    )
