"""Independent Graph Coloring Validator.

PRD §12.5, Tasks P7.13, P7.14:
Written without calling any algorithm code. Independently verifies:
1. Every vertex in the graph is colored exactly once.
2. Every color is a non-negative integer.
3. No two adjacent vertices share the same color.
4. No spurious vertices are colored.
"""

from app.algorithms.types import AdjacencyList, ValidationResult, Vertex


def validate_coloring(adj: AdjacencyList, colors: dict[Vertex, int]) -> ValidationResult:
    """
    Independently verifies that `colors` is a valid proper vertex coloring of G = (V, E).
    Returns a structured ValidationResult report. Never raises an exception on invalid data.
    """
    all_vertices = set(adj.keys())
    colored_vertices = set(colors.keys())

    # 1. Check completeness
    uncolored = sorted(all_vertices - colored_vertices)
    extra = sorted(colored_vertices - all_vertices)

    errors: list[str] = []
    if uncolored:
        errors.append(f"{len(uncolored)} vertices remain uncolored: {uncolored[:5]}")
    if extra:
        errors.append(f"{len(extra)} unknown extra vertices colored: {extra[:5]}")

    # 2. Check non-negative integer colors
    invalid_colors: list[tuple[Vertex, int]] = []
    for v, c in colors.items():
        if not isinstance(c, int) or c < 0:
            invalid_colors.append((v, c))
    if invalid_colors:
        errors.append(f"{len(invalid_colors)} vertices assigned invalid colors (must be int >= 0): {invalid_colors[:5]}")

    # 3. Check conflicts on edges (u, v) where u < v
    conflicts: list[tuple[Vertex, Vertex, int]] = []
    total_edges = 0

    for u, neighbors in adj.items():
        for v in neighbors:
            if u < v:  # Count and check each undirected edge exactly once
                total_edges += 1
                color_u = colors.get(u)
                color_v = colors.get(v)
                if color_u is not None and color_v is not None and color_u == color_v:
                    conflicts.append((u, v, color_u))

    if conflicts:
        errors.append(f"{len(conflicts)} monochromatic edge conflicts detected: {conflicts[:5]}")

    is_valid = (
        len(uncolored) == 0
        and len(extra) == 0
        and len(invalid_colors) == 0
        and len(conflicts) == 0
    )

    err_msg = "; ".join(errors) if errors else None

    return ValidationResult(
        valid=is_valid,
        uncolored=uncolored,
        conflicts=conflicts,
        total_vertices=len(all_vertices),
        total_edges_checked=total_edges,
        error_message=err_msg,
    )
