# ADR-003: Enrollment Scoping Tied to Scheduling Cycle

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, Database Team
- **Context:** PRD §17.7, Appendix C Item 1

---

## Context and Problem Statement

PRD §17.7 mentions that enrollments link to "academic_year_id or cycle_id".
In higher education, course enrollment can change between regular terms, supplementary exam sessions, and summer terms within the same academic year. If enrollments were scoped solely to an academic year, a student who takes an exam in June and a supplementary exam in August would collide, or supplementary exams would inherit stale enrollment lists.

## Decision

We decide that **every `Enrollment` record is explicitly scoped to a `SchedulingCycle`**:
1. The `enrollments` table schema includes `(student_id, subject_id, cycle_id)`.
2. A database uniqueness constraint enforces:
   $$\text{UNIQUE}(\text{student\_id}, \text{subject\_id}, \text{cycle\_id}) \quad \text{WHERE status = 'active'}$$
3. The associated `academic_year_id` and `semester_id` are derived properties navigated through the `scheduling_cycles` relationship.
4. Active enrollments determine graph edges; withdrawing an enrollment updates `status = 'withdrawn'` rather than physically deleting rows, preserving academic history and audit trails.

## Consequences

### Positive
- Clear and unambiguous scoping: building a graph for Cycle $X$ queries `WHERE cycle_id = :cycle_id AND status = 'active'`.
- Supports regular, mid-term, backlog, and supplementary examination cycles without data collisions.
- Simplifies staleness tracking: mutations in enrollments for cycle $C$ directly increment cycle $C$'s `data_version` counter.

### Negative
- Importing enrollments requires an active scheduling cycle target.
