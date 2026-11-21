# ADR-010: Schedule Versioning Lifecycle and Immutability of Published Timetables

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, Scheduling Team
- **Context:** PRD §15, §17.14, FR-15, FR-19, Appendix C Item 9, Item 14

---

## Context and Problem Statement

Examination timetables progress through stages: automated generation, coordinator review, manual adjustments, and official publication.
Once a timetable is published, students and faculty plan their travel, study periods, and invigilation.
We must define:
1. What mutation semantics apply to draft schedules during manual editing.
2. The strict immutability rules governing published schedules.
3. How revisions to published schedules must be handled.

## Decision

1. **Schedule Version Lifecycle States:**
   - `Candidate`: A draft schedule produced by an algorithm run or cloned from an earlier version. Open to manual edits, slot swaps, and regeneration.
   - `Reviewed`: A candidate schedule that has successfully passed 100% of hard constraints and has been formally marked by an administrator as reviewed. Any subsequent manual edit reverts the state back to `Candidate`.
   - `Published`: The officially approved, public timetable for a scheduling cycle.
   - `Archived`: Superseded or historical schedule versions.
2. **In-Place Mutation for Candidates with Full Audit Trail:**
   - While in `Candidate` or `Reviewed` state, manual slot changes and exam locks update the version in-place, recording an audit entry and updating an `updated_at` / `row_version` counter for optimistic locking.
3. **Absolute Immutability of Published Schedules:**
   - A schedule version marked `Published` **can never be edited, moved, locked, unlocked, or overwritten in-place**.
   - Enforced by both service-layer authorization checks and a database trigger / guarded repository layer.
   - Exactly **one** schedule version may be `Published` per cycle at any given time:
     $$\text{UNIQUE}(\text{scheduling\_cycle\_id}) \quad \text{WHERE status = 'Published'}$$
4. **Publishing New Revisions:**
   - If changes are required after publication, an administrator must **clone** the published version into a new `Candidate` version (`POST /schedules/{id}/clone`), make the validated edits, run full validation, and publish the new candidate.
   - Publishing the new version atomically transitions the previously published version to `Archived` while preserving its entire historical record.

## Consequences

### Positive
- Strict integrity guarantee: students will never experience silent, unannounced in-place timetable shifts.
- Full auditability and historical reconstruction of every timetable iteration.
- Clear, well-defined finite state machine.

### Negative
- Post-publication modifications require an explicit clone-edit-publish workflow, which is an intentional, protective design choice.
