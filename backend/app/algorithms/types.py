"""Pure Algorithmic Data Contracts.

PRD §11, §12, §20, §36:
This module contains standard domain and algorithm data structures.
It has zero dependencies on web frameworks, database ORMs, or external networking.
"""

from dataclasses import dataclass
from typing import Any

# Type Aliases for Graph Operations
Vertex = str
AdjacencyList = dict[Vertex, set[Vertex]]
EdgeWeights = dict[tuple[Vertex, Vertex], int]


@dataclass
class ConflictGraph:
    """Pure in-memory conflict graph representation G = (V, E) (ADR-006, Task P6.1)."""

    vertices: set[Vertex]
    adjacency: AdjacencyList
    edge_weights: EdgeWeights
    vertex_metadata: dict[Vertex, dict[str, Any]]


@dataclass
class GraphValidationReport:
    """Report produced by independent graph validator (PRD §11.6, Task P6.4)."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    vertex_count_checked: int
    edge_count_checked: int



@dataclass
class GraphMetrics:
    """Statistical summary of a conflict graph G=(V, E)."""

    vertex_count: int
    edge_count: int
    density: float
    avg_degree: float
    max_degree: int
    min_degree: int
    isolated_vertices: list[Vertex]
    connected_components_count: int
    largest_component_size: int
    degree_histogram: dict[int, int]
    chromatic_lower_bound: int
    enrollment_snapshot_hash: str


@dataclass
class TraceStep:
    """Educational step-by-step trace of DSATUR or coloring heuristic."""

    step: int
    selected_vertex: Vertex
    degree: int
    saturation_degree: int
    forbidden_colors: list[int]
    assigned_color: int
    neighbor_saturations_updated: list[Vertex]


@dataclass
class ColoringResult:
    """Result of executing a graph coloring algorithm."""

    colors: dict[Vertex, int]
    color_count: int
    execution_time_ms: float
    vertex_visits: int
    color_checks: int
    valid: bool
    algorithm: str
    algorithm_version: str
    config: dict[str, Any]
    trace: list[TraceStep] | None = None
    graph_fingerprint: str = ""


@dataclass
class ValidationResult:
    """Independent verification report of a vertex coloring."""

    valid: bool
    uncolored: list[Vertex]
    conflicts: list[tuple[Vertex, Vertex, int]]  # (u, v, shared_color)
    total_vertices: int
    total_edges_checked: int
    error_message: str | None = None
