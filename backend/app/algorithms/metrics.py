"""Coloring Quality Metrics and Imbalance Analyzer.

PRD §12.5, Task P7.15:
Computes color class distributions, imbalance scores, standard deviation,
and grouping by color class for downstream slot mapping and reporting.
"""

import math
from typing import Any

from app.algorithms.types import Vertex, stable_key


def compute_coloring_metrics(colors: dict[Vertex, int]) -> dict[str, Any]:
    """
    Analyzes a proper vertex coloring to extract distribution and imbalance statistics.
    """
    if not colors:
        return {
            "color_count": 0,
            "groups_by_color": {},
            "class_sizes": {},
            "max_class_size": 0,
            "min_class_size": 0,
            "size_ratio": 1.0,
            "std_dev": 0.0,
            "imbalance_score": 0,
        }

    # Group vertices by assigned color class
    groups: dict[int, list[Vertex]] = {}
    for v, c in colors.items():
        groups.setdefault(c, []).append(v)

    # Sort vertices in each group for determinism
    for c in groups:
        groups[c].sort(key=stable_key)

    class_sizes = {c: len(verts) for c, verts in groups.items()}
    sizes = list(class_sizes.values())
    color_count = len(sizes)

    max_size = max(sizes)
    min_size = min(sizes)
    size_ratio = round(max_size / min_size, 4) if min_size > 0 else 1.0
    imbalance = max_size - min_size

    mean_size = sum(sizes) / color_count
    variance = sum((s - mean_size) ** 2 for s in sizes) / color_count
    std_dev = round(math.sqrt(variance), 4)

    return {
        "color_count": color_count,
        "groups_by_color": groups,
        "class_sizes": class_sizes,
        "max_class_size": max_size,
        "min_class_size": min_size,
        "size_ratio": size_ratio,
        "std_dev": std_dev,
        "imbalance_score": imbalance,
    }
