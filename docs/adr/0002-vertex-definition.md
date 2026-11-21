# ADR-002: Vertex Definition in the Conflict Graph

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, Algorithm Team
- **Context:** PRD §8, §11.1, §17.8, Appendix C Item 2

---

## Context and Problem Statement

In graph coloring for university exam scheduling, we must define what constitutes a single vertex $v \in V$.
A subject may be offered across multiple semesters, or a subject may have multiple components (e.g., lecture theory exam vs practical lab exam). Furthermore, subjects exist globally in an institution's catalog across several years.

If a vertex represented a subject directly, exam schedules would become ambiguous across academic years or multiple exam cycles.

## Decision

We define:
1. **One Vertex = Exactly One `Exam` entity belonging to a specific `SchedulingCycle`.**
2. Each `Exam` has a one-to-one link to a `Subject` within that cycle, with a database uniqueness constraint:
   $$\text{UNIQUE}(\text{scheduling\_cycle\_id}, \text{subject\_id})$$
3. In graph algorithms, vertex identifiers are formatted as stable strings: `exam_{exam_id}` or the unique subject code within that cycle (e.g., `CS301`).
4. Vertex metadata (such as duration, student enrollment count, priority, preferred dates, and restricted dates) is carried in vertex attributes passed to the scheduling engine, keeping the core graph coloring algorithms pure and decoupled from database models.

## Consequences

### Positive
- Prevents graph cross-contamination between different exam periods or historical cycles.
- Allows the same academic subject to be scheduled with different parameters (e.g., different duration or dates) in different semesters or cycles without mutating historical data.
- Ensures a clear mathematical invariant: $|V|$ equals the exact number of exams scheduled in that cycle.

### Negative
- Requires an explicit synchronization step (`POST /cycles/{id}/exams/sync`) when new subjects are added to a department or cycle scope.
