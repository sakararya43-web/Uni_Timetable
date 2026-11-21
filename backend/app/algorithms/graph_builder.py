"""Pure Conflict Graph Construction, Validation, Statistics, and Hashing Engine.

PRD §11 (FR-07), ADR-006, Tasks P6.1, P6.2, P6.3, P6.4, P6.5, P6.6:
This module contains 100% pure algorithmic operations with zero dependencies on
web frameworks, database ORMs, or external networking.
"""

import hashlib
from collections import deque
from typing import Any

from app.algorithms.types import ConflictGraph, GraphMetrics, GraphValidationReport, Vertex


def compute_enrollment_hash(exam_ids: list[str], enrollments: list[tuple[str, str]]) -> str:
    """
    Computes a deterministic SHA-256 hash over canonical sorted serialization
    of in-scope exam IDs and active (student_id, exam_id) pairs (Task P6.6).
    """
    sorted_exams = sorted(set(exam_ids))
    valid_exam_set = set(sorted_exams)
    # Deduplicate and sort (student_id, exam_id) pairs
    sorted_enr = sorted({(str(s), str(e)) for s, e in enrollments if str(e) in valid_exam_set})

    exam_part = ",".join(sorted_exams)
    enr_part = ";".join(f"{s}:{e}" for s, e in sorted_enr)
    raw_payload = f"EXAMS:{exam_part};ENR:{enr_part}"

    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


def greedy_clique_lower_bound(vertices: set[Vertex], adjacency: dict[Vertex, set[Vertex]]) -> int:
    """
    Computes a greedy lower bound for the chromatic number via maximal clique search (Task P6.5).
    Since chi(G) >= omega(G) (clique number), any clique size is a valid chromatic lower bound.
    """
    if not vertices:
        return 0

    sorted_v = sorted(
        vertices,
        key=lambda v: (len(adjacency.get(v, set())), v),
        reverse=True,
    )

    # Seed greedy search from top candidates by degree
    seeds = sorted_v[: min(10, len(sorted_v))]
    best_clique_size = 1

    for seed in seeds:
        clique = [seed]
        for candidate in sorted_v:
            if candidate == seed:
                continue
            cand_adj = adjacency.get(candidate, set())
            if all(member in cand_adj for member in clique):
                clique.append(candidate)
        if len(clique) > best_clique_size:
            best_clique_size = len(clique)

    return best_clique_size


def build_conflict_graph(
    exam_ids: list[str],
    enrollments: list[tuple[str, str]],
    vertex_metadata: dict[str, dict[str, Any]] | None = None,
) -> ConflictGraph:
    """
    Builds the conflict graph G = (V, E) in O(sum k(k-1)/2) streaming fashion (Tasks P6.2, P6.3).

    Steps:
    1. Every in-scope exam becomes a vertex V, including isolated vertices.
    2. Enrollments are grouped by student: student_id -> set(exam_id).
    3. Pairwise combinations (u, v) with u < v increment the shared student count.
    4. Adjacency sets are created symmetrically.
    5. Invariants enforced: no self-loops, normalized pairs (u < v), symmetric adjacency.
    """
    vertices: set[Vertex] = set(exam_ids)
    adjacency: dict[Vertex, set[Vertex]] = {v: set() for v in vertices}
    edge_weights: dict[tuple[Vertex, Vertex], int] = {}

    # Deduplicate raw enrollments to ensure no double-counting
    student_exams: dict[str, set[str]] = {}
    for student_id, exam_id in enrollments:
        if exam_id in vertices:
            student_exams.setdefault(student_id, set()).add(exam_id)

    # Stepwise pairwise edge generation with u < v ordering
    for _student_id, exams in student_exams.items():
        if len(exams) < 2:
            continue
        sorted_exams = sorted(exams)
        n = len(sorted_exams)
        for i in range(n):
            u = sorted_exams[i]
            for j in range(i + 1, n):
                v = sorted_exams[j]
                pair = (u, v)
                edge_weights[pair] = edge_weights.get(pair, 0) + 1

    # Symmetric adjacency population
    for (u, v), _w in edge_weights.items():
        adjacency[u].add(v)
        adjacency[v].add(u)

    metadata = vertex_metadata or {}
    return ConflictGraph(
        vertices=vertices,
        adjacency=adjacency,
        edge_weights=edge_weights,
        vertex_metadata=metadata,
    )


def validate_graph(
    graph: ConflictGraph,
    exam_ids: list[str],
    enrollments: list[tuple[str, str]],
) -> GraphValidationReport:
    """
    Independent graph validator (PRD §11.6, Task P6.4).
    Re-verifies all graph invariants and re-computes edge weights directly from raw enrollments.
    Never raises an exception; returns a structured report.
    """
    errors: list[str] = []
    warnings: list[str] = []
    expected_vertices = set(exam_ids)

    # 1. Exact vertex set check
    if graph.vertices != expected_vertices:
        missing = expected_vertices - graph.vertices
        extra = graph.vertices - expected_vertices
        if missing:
            errors.append(f"Graph is missing {len(missing)} expected exam vertices: {sorted(missing)[:5]}")
        if extra:
            errors.append(f"Graph has {len(extra)} unexpected exam vertices: {sorted(extra)[:5]}")

    # 2. Invariants: no self-loops, valid vertices in adjacency
    for v in graph.vertices:
        adj = graph.adjacency.get(v, set())
        if v in adj:
            errors.append(f"Self-loop detected on vertex '{v}'.")
        for nbr in adj:
            if nbr not in graph.vertices:
                errors.append(f"Vertex '{v}' has neighbor '{nbr}' not in vertex set.")

    # 3. Normalized edge keys and positive weights
    for (u, v), w in graph.edge_weights.items():
        if u == v:
            errors.append(f"Self-loop edge key found in edge_weights: ({u}, {v}).")
        if u >= v:
            errors.append(f"Edge key is not normalized in strict ascending order (u < v): ({u}, {v}).")
        if w < 1:
            errors.append(f"Edge ({u}, {v}) has non-positive shared student count: {w}.")

    # 4. Adjacency symmetry and edge_weights consistency
    for u, neighbors in graph.adjacency.items():
        for v in neighbors:
            if u not in graph.adjacency.get(v, set()):
                errors.append(f"Asymmetric adjacency detected: '{v}' in adj['{u}'] but not vice-versa.")
            pair = (min(u, v), max(u, v))
            if pair not in graph.edge_weights:
                errors.append(f"Adjacency neighbor pair {pair} missing from edge_weights.")

    for (u, v) in graph.edge_weights:
        if v not in graph.adjacency.get(u, set()) or u not in graph.adjacency.get(v, set()):
            errors.append(f"Edge ({u}, {v}) in edge_weights is missing from adjacency list.")

    # 5. Independent edge recomputation from raw enrollments
    # Group by student
    student_exams: dict[str, set[str]] = {}
    for s_id, e_id in enrollments:
        if e_id in expected_vertices:
            student_exams.setdefault(s_id, set()).add(e_id)

    expected_weights: dict[tuple[str, str], int] = {}
    for _s_id, exams in student_exams.items():
        if len(exams) < 2:
            continue
        sorted_exams = sorted(exams)
        n = len(sorted_exams)
        for i in range(n):
            u_node = sorted_exams[i]
            for j in range(i + 1, n):
                v_node = sorted_exams[j]
                pair = (u_node, v_node)
                expected_weights[pair] = expected_weights.get(pair, 0) + 1

    # Compare recomputed edges with graph.edge_weights
    if set(graph.edge_weights.keys()) != set(expected_weights.keys()):
        missing_edges = set(expected_weights.keys()) - set(graph.edge_weights.keys())
        extra_edges = set(graph.edge_weights.keys()) - set(expected_weights.keys())
        if missing_edges:
            errors.append(f"{len(missing_edges)} conflict edges from enrollments missing in graph: {list(missing_edges)[:5]}")
        if extra_edges:
            errors.append(f"{len(extra_edges)} spurious conflict edges present in graph: {list(extra_edges)[:5]}")
    else:
        # Check weight equality
        for pair, exp_w in expected_weights.items():
            act_w = graph.edge_weights.get(pair)
            if act_w != exp_w:
                errors.append(f"Edge {pair} weight mismatch: expected {exp_w}, got {act_w}.")

    return GraphValidationReport(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        vertex_count_checked=len(graph.vertices),
        edge_count_checked=len(graph.edge_weights),
    )


def compute_stats(graph: ConflictGraph, enrollment_snapshot_hash: str = "") -> GraphMetrics:
    """
    Computes graph statistical metrics (Task P6.5):
    - |V|, |E|
    - avg, max, min degree; degree histogram
    - connected components count and largest component size using iterative BFS
    - isolated vertices list/count
    - density D = 2|E| / (|V|(|V|-1)) (0 if |V| < 2)
    - chromatic lower bound via greedy maximal clique
    """
    v_count = len(graph.vertices)
    e_count = len(graph.edge_weights)

    if v_count == 0:
        return GraphMetrics(
            vertex_count=0,
            edge_count=0,
            density=0.0,
            avg_degree=0.0,
            max_degree=0,
            min_degree=0,
            isolated_vertices=[],
            connected_components_count=0,
            largest_component_size=0,
            degree_histogram={},
            chromatic_lower_bound=0,
            enrollment_snapshot_hash=enrollment_snapshot_hash,
        )

    degrees: dict[Vertex, int] = {v: len(graph.adjacency.get(v, set())) for v in graph.vertices}
    max_deg = max(degrees.values())
    min_deg = min(degrees.values())
    avg_deg = round(sum(degrees.values()) / v_count, 4)

    density = round((2.0 * e_count) / (v_count * (v_count - 1)), 6) if v_count >= 2 else 0.0
    isolated = sorted([v for v, deg in degrees.items() if deg == 0])

    deg_hist: dict[int, int] = {}
    for d in degrees.values():
        deg_hist[d] = deg_hist.get(d, 0) + 1

    # Iterative BFS for connected components (no recursion)
    visited: set[Vertex] = set()
    components_count = 0
    largest_component_size = 0

    for v in sorted(graph.vertices):
        if v not in visited:
            components_count += 1
            queue: deque[Vertex] = deque([v])
            visited.add(v)
            comp_size = 0
            while queue:
                curr = queue.popleft()
                comp_size += 1
                for nbr in sorted(graph.adjacency.get(curr, set())):
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
            if comp_size > largest_component_size:
                largest_component_size = comp_size

    clique_bound = greedy_clique_lower_bound(graph.vertices, graph.adjacency)

    return GraphMetrics(
        vertex_count=v_count,
        edge_count=e_count,
        density=density,
        avg_degree=avg_deg,
        max_degree=max_deg,
        min_degree=min_deg,
        isolated_vertices=isolated,
        connected_components_count=components_count,
        largest_component_size=largest_component_size,
        degree_histogram=deg_hist,
        chromatic_lower_bound=clique_bound,
        enrollment_snapshot_hash=enrollment_snapshot_hash,
    )
