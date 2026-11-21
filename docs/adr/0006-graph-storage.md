# ADR-006: Conflict Graph Storage

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, Database Team
- **Context:** PRD §11, §17.11, §17.12, Appendix C Item 6

---

## Context and Problem Statement

The conflict graph $G = (V, E)$ consists of hundreds of vertices and potentially thousands of weighted edges. The system must support:
- Rapid loading of graph topologies for visualization in React Flow.
- Fast execution of graph coloring algorithms without database overhead.
- Auditable point-in-time snapshots for schedule generation and regression testing.
- Individual queryability of edge weights and drill-down into shared student identities for authorized staff.

## Decision

We adopt a **hybrid storage architecture**:
1. **`conflict_graph_snapshots` Table:**
   - Stores snapshot-level metadata: `id`, `scheduling_cycle_id`, `version`, `vertex_count`, `edge_count`, `density`, `avg_degree`, `max_degree`, `chromatic_lower_bound`, `enrollment_snapshot_hash`, `created_at`.
   - Stores `graph_data_json`: A complete, self-contained JSON snapshot containing the full adjacency list and vertex degrees. This allows the graph visualization API and coloring algorithms to load the entire graph structure in a single fast read without thousands of individual row joins.
2. **`conflict_edges` Table:**
   - Stores relational, normalized edge records: `(id, graph_snapshot_id, exam_id_a, exam_id_b, shared_student_count)`.
   - Enforces canonical ordering constraint:
     $$\text{CHECK}(\text{exam\_id\_a} < \text{exam\_id\_b})$$
   - Enforces unique constraint:
     $$\text{UNIQUE}(\text{graph\_snapshot\_id}, \text{exam\_id\_a}, \text{exam\_id\_b})$$
   - Enables fast relational queries, such as retrieving all conflict partners for a specific exam or finding the shared student identities for an edge.
3. **Snapshot Immutability:** Graph snapshots are strictly immutable once created. Any change in enrollments generates a new versioned snapshot, leaving prior snapshots untouched for historical reproducibility.

## Consequences

### Positive
- Instantaneous graph loading for both UI visualization and Python coloring algorithms via the JSON document.
- Relational integrity, foreign keys, and indexes on edges for deep analytics and drill-downs.
- Immutability guarantees that schedule runs can cite their source snapshot indefinitely.

### Negative
- Minor data duplication between `graph_data_json` and `conflict_edges` rows, managed entirely within transactional creation boundaries.
