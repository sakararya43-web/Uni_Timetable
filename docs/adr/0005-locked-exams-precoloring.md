# ADR-005: Precoloring Mechanism for Locked Examinations

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, Algorithm Team
- **Context:** PRD §12.4, §15.3, FR-16, FR-17, Appendix C Item 4

---

## Context and Problem Statement

Administrators need the ability to "lock" specific exams to fixed calendar time slots (e.g., locking a university-wide common core exam to Monday Morning).
When a schedule is regenerated, locked exams must stay in their assigned time slots without creating conflicts, while unlocked exams are reshuffled around them.

Because graph coloring operates on abstract integers ($0, 1, \dots, k-1$) and time slots are concrete entities with database IDs and timestamps, we must define the mapping bridging locked slots and coloring colors.

## Decision

We implement a **precoloring reservation strategy**:
1. **Slot Grouping:** Before calling the coloring algorithm, inspect all locked assignments in the target schedule.
2. Group locked exams by their assigned `time_slot_id`.
3. **Reserved Color Allocation:** Assign each distinct locked time slot a dedicated, unique integer color index $c_{\text{slot}}$.
   - If exam $A$ is locked to Slot 1 and exam $B$ is locked to Slot 1, both are precolored with $c_{\text{slot1}}$.
   - If exam $C$ is locked to Slot 2, it is precolored with $c_{\text{slot2}}$.
4. **Feasibility Validation:** Before running the algorithm, assert that no two locked exams in the same slot share an edge in $G$. If a clash is detected, immediately abort with `LOCKED_CONFLICT` and report the clashing pair.
5. **Algorithmic Enforcement:** Pass the precolor dictionary `precolored: dict[str, int]` into the coloring algorithms (Greedy, Welsh–Powell, DSATUR).
   - In Greedy and Welsh–Powell: precolored vertices skip color selection; their colors immediately populate neighbors' forbidden sets.
   - In DSATUR: precolored vertices are initialized at step 0, updating all neighboring saturation sets before any uncolored vertex is chosen.
6. **Slot Mapping Binding:** When mapping colors to slots, precolored color IDs are pre-bound to their locked time slots, and the remaining uncolored classes are matched to remaining unallocated slots.

## Consequences

### Positive
- Mathematically rigorous: precoloring is a recognized formulation of graph coloring with fixed vertices.
- Provably prevents locked exams from moving during regeneration.
- Detects mutually conflicting locks prior to running expensive heuristics.

### Negative
- Precoloring reduces the degrees of freedom for heuristics, which can increase the overall chromatic number or cause infeasibility if slots are tight. Infeasibility diagnostics clearly identify this condition.
