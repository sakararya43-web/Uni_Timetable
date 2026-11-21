"""Graph Input Guards and Defensive Integrity Checks.

PRD §12.2, §15.3, Tasks P7.2, P7.3, P7.17:
Verifies structural invariants before any coloring algorithm runs:
- No self-loops
- Symmetric undirected adjacency
- Valid neighbor references
- Precolor feasibility and conflict detection (LOCKED_CONFLICT)
"""

import hashlib

from app.algorithms.types import AdjacencyList, ColoringException, Vertex, stable_key


def compute_graph_fingerprint(adj: AdjacencyList) -> str:
    """Computes a canonical SHA-256 fingerprint of the graph adjacency structure."""
    canonical_items: list[str] = []
    for u in sorted(adj.keys(), key=stable_key):
        nbrs_str = ",".join(sorted(adj[u], key=stable_key))
        canonical_items.append(f"{u}->{nbrs_str}")
    return hashlib.sha256(";".join(canonical_items).encode("utf-8")).hexdigest()


def validate_graph_input(
    adj: AdjacencyList,
    precolored: dict[Vertex, int] | None = None,
) -> None:
    """
    Validates input graph and precolored vertices against domain rules (Tasks P7.2, P7.17).
    Raises typed ColoringException on any violation.
    """
    all_vertices = set(adj.keys())

    # 1. Structural checks on adjacency
    for u, neighbors in adj.items():
        # Check self-loops
        if u in neighbors:
            raise ColoringException(
                code="SELF_LOOP_DETECTED",
                message=f"Self-loop detected on vertex '{u}'. Graphs with self-loops cannot be colored.",
            )

        # Check unknown neighbors & symmetry
        for v in neighbors:
            if v not in all_vertices:
                raise ColoringException(
                    code="UNKNOWN_NEIGHBOR",
                    message=f"Vertex '{u}' references neighbor '{v}' which does not exist in graph vertices.",
                )
            if u not in adj[v]:
                raise ColoringException(
                    code="ASYMMETRIC_GRAPH",
                    message=f"Asymmetric adjacency detected: edge ({u}, {v}) exists but reverse ({v}, {u}) is missing.",
                )

    # 2. Precolored validation
    if precolored:
        for v, color in precolored.items():
            if v not in all_vertices:
                raise ColoringException(
                    code="UNKNOWN_PRECOLORED_VERTEX",
                    message=f"Precolored vertex '{v}' does not exist in graph vertices.",
                )
            if not isinstance(color, int) or color < 0:
                raise ColoringException(
                    code="INVALID_PRECOLOR",
                    message=f"Precolored vertex '{v}' assigned invalid color '{color}'. Must be non-negative integer.",
                )

        # 3. Check for conflicting precolors on adjacent vertices (LOCKED_CONFLICT, Task P7.17)
        for u, color_u in precolored.items():
            for v in adj.get(u, set()):
                if v in precolored and precolored[v] == color_u:
                    u_str, v_str = sorted([str(u), str(v)])
                    raise ColoringException(
                        code="LOCKED_CONFLICT",
                        message=(
                            f"Conflicting precolored adjacent vertices: '{u_str}' and '{v_str}' "
                            f"are connected by an edge and both locked to color {color_u}."
                        ),
                    )
