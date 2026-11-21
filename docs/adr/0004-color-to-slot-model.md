# ADR-004: Color-to-Slot Model

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, Algorithm Team
- **Context:** PRD §11, §13, FR-11, Appendix C Item 3

---

## Context and Problem Statement

Graph coloring assigns an integer color $c \in \{0, 1, \dots, k-1\}$ to each vertex such that no adjacent vertices share a color.
When converting abstract colors into real time slots, two architectural models exist:
1. **One-to-One Model:** Each color class is mapped to **exactly one** calendar time slot.
2. **One-to-Many / Fractional Model:** Exams sharing a color class may be scattered across multiple time slots if capacity or room limits require it.

## Decision

We adopt the **strict One-to-One Model for MVP**:
1. **One color class = Exactly one time slot.**
2. All examinations assigned to color $c$ are scheduled in the single time slot assigned to color $c$.
3. Because all vertices within a color class form an independent set in $G$ (no shared enrollments), scheduling them in the same time slot is mathematically guaranteed to create zero student conflicts.
4. If a color class exceeds session capacity (`class_size > max_exams_per_session`), the scheduling engine flags this during the mapping phase and reports the specific capacity violation. An explicit fallback allows splitting the class across distinct non-overlapping sessions on the same calendar day, subject to a complete re-run of the independent schedule validator.

## Consequences

### Positive
- Guarantees mathematical clarity and transparency: color classes directly explain time-slot groups.
- Keeps mapping time complexity low and deterministic via maximum bipartite matching.
- Simplifies UI visualization: colors in the conflict graph map 1:1 to slot labels in the legend.

### Negative
- Requires sufficient distinct time slots in the cycle equal to or greater than the chromatic number $\chi(G)$ of the conflict graph.
