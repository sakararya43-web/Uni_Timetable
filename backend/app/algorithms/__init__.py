"""Pure Graph Coloring & Scheduling Algorithms Package.

STRICT RULE (PRD §20, §36):
This package has zero dependencies on web frameworks, ORMs, or databases.
It operates purely on native Python types and dataclasses.
"""

from app.algorithms.dsatur import dsatur
from app.algorithms.graph_builder import (
    build_conflict_graph,
    compute_enrollment_hash,
    compute_stats,
    greedy_clique_lower_bound,
    validate_graph,
)
from app.algorithms.greedy import greedy_color
from app.algorithms.guards import compute_graph_fingerprint, validate_graph_input
from app.algorithms.metrics import compute_coloring_metrics
from app.algorithms.types import (
    DSATUR_VERSION,
    GREEDY_VERSION,
    WELSH_POWELL_VERSION,
    AdjacencyList,
    ColoringException,
    ColoringResult,
    ConflictGraph,
    EdgeWeights,
    GraphMetrics,
    GraphValidationReport,
    TraceStep,
    ValidationResult,
    Vertex,
    stable_key,
)
from app.algorithms.validators import validate_coloring
from app.algorithms.welsh_powell import welsh_powell

__all__ = [
    "DSATUR_VERSION",
    "GREEDY_VERSION",
    "WELSH_POWELL_VERSION",
    "AdjacencyList",
    "ColoringException",
    "ColoringResult",
    "ConflictGraph",
    "EdgeWeights",
    "GraphMetrics",
    "GraphValidationReport",
    "TraceStep",
    "ValidationResult",
    "Vertex",
    "build_conflict_graph",
    "compute_coloring_metrics",
    "compute_enrollment_hash",
    "compute_graph_fingerprint",
    "compute_stats",
    "dsatur",
    "greedy_color",
    "greedy_clique_lower_bound",
    "stable_key",
    "validate_coloring",
    "validate_graph",
    "validate_graph_input",
    "welsh_powell",
]
