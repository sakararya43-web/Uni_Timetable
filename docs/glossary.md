# Domain Glossary & Naming Conventions

**Project:** University Examination Timetable Scheduling System  
**Document Version:** 1.0.0  
**Date:** 2026-11-21  
**Source Baseline:** PRD.md §8  
**Phase:** Phase 0 (Task P0.3)

---

## 1. Domain Terminology & Code Names

To maintain total consistency across the database schema, backend services, algorithmic modules, API endpoints, and frontend components, all developers and agents must adhere to the definitions and standard code identifiers below.

| Term | Domain Definition | Backend Code Name | DB Column / Entity | Frontend Code Name |
|---|---|---|---|---|
| **Scheduling Cycle** | A bounded exam scheduling exercise (e.g., "Fall 2026 End-Term Exams") spanning a date range with configured sessions and holiday constraints. | `SchedulingCycle` | `scheduling_cycles` | `SchedulingCycle` |
| **Exam** | An assessment event for a specific subject within an active scheduling cycle. Forms a vertex in the conflict graph. | `Exam` | `exams` | `Exam` |
| **Subject / Course** | An academic course unit (e.g., "CS301 Data Structures") with a unique code, name, department, semester, and standard exam duration. | `Subject` | `subjects` | `Subject` |
| **Student** | An enrolled student identified by an immutable `student_number` (e.g., `STU1001`), name, department, and semester. | `Student` | `students` | `Student` |
| **Enrollment** | An active academic registration linking a student to a subject for a specific scheduling cycle. | `Enrollment` | `enrollments` | `Enrollment` |
| **Vertex** | A graph node representing a single examination event ($v \in V$). | `vertex_id` (`str`) | `exams.id` | `nodeId` / `vertexId` |
| **Edge** | A bidirectional conflict relation ($u, v \in E$) indicating that at least one student is concurrently enrolled in both exams $u$ and $v$. | `ConflictEdge` | `conflict_edges` | `ConflictEdge` |
| **Edge Weight** | The exact number of distinct students enrolled in both exams ($w(u, v) \ge 1$). | `shared_student_count` / `weight` | `conflict_edges.shared_student_count` | `weight` / `sharedCount` |
| **Conflict Graph** | The undirected weighted graph $G = (V, E)$ representing all exams and their conflict relationships. | `ConflictGraph` | `conflict_graph_snapshots` | `ConflictGraph` |
| **Degree** | The number of neighboring exams in $G$ with which a given exam conflicts: $\text{deg}(v) = \|N(v)\|$. | `degree` (`int`) | `conflict_graph_snapshots.avg/max_degree` | `degree` |
| **Saturation Degree** | The number of distinct colors assigned to already-colored neighbors of vertex $v$: $\rho(v) = \|\{c(u) : u \in N(v), u \text{ is colored}\}\|$. Key heuristic in DSATUR. | `saturation` (`int`) | `saturation_degree` | `saturation` |
| **Color** | An abstract, zero-based non-negative integer class identifier ($c \in \{0, 1, \dots, k-1\}$) assigned by a graph coloring algorithm. | `color_id` (`int`) | `exam_assignments.color_id` | `colorId` |
| **Color Class** | The independent set of all vertices assigned the identical color $c$: $V_c = \{v \in V \mid c(v) = c\}$. | `color_class` (`list[str]`) | Grouped assignments | `colorClass` |
| **Time Slot** | A concrete calendar window on a specific date with a defined start time, end time, session label, and duration minutes. | `TimeSlot` | `time_slots` | `TimeSlot` |
| **Session** | A recurring daily exam window (e.g., Morning 09:00–12:00, Afternoon 14:00–17:00). | `SessionConfig` | `time_slots.session_label` | `Session` |
| **Chromatic Number** | The theoretical minimum number of colors needed to properly color graph $G$, denoted $\chi(G)$. | `chromatic_number` | `chromatic_lower_bound` | `chromaticBound` |
| **Proper Coloring** | A vertex coloring where no two adjacent vertices share the same color: $\forall (u, v) \in E, c(u) \neq c(v)$. | `is_valid` / `valid` | `is_valid` | `isValid` |
| **Locked Exam** | An examination whose assigned time slot is locked by an administrator and must not move during subsequent schedule regeneration. | `is_locked` (`bool`) | `exam_assignments.locked` | `isLocked` |
| **Precolored Vertex** | A vertex whose color is predetermined prior to running a coloring heuristic, representing a locked exam. | `precolored` (`dict[str, int]`) | Pre-mapped state | `precolored` |
| **Hard Constraint** | An absolute invariant that must never be violated in a published timetable (e.g., no student has 2 exams in the same slot). | `HardConstraint` | Validation error code | `HardViolation` |
| **Soft Constraint** | An operational preference to be minimized (e.g., avoiding 2 exams in one day for a student, avoiding consecutive exam sessions). | `SoftConstraint` | `soft_penalty_score` | `softPenalty` |
| **Schedule Run** | An audited execution record of an algorithm on a specific graph snapshot, recording runtime, colors used, validity, and parameters. | `ScheduleRun` | `schedule_runs` | `ScheduleRun` |
| **Schedule Version** | A persisted timetable version with a lifecycle state (`Candidate`, `Reviewed`, `Published`, `Archived`). | `ScheduleVersion` | `schedule_versions` | `ScheduleVersion` |
| **Exam Assignment** | A concrete placement of an exam into a specific time slot within a schedule version. | `ExamAssignment` | `exam_assignments` | `ExamAssignment` |
| **Audit Log** | An append-only chronological record of administrative actions, edits, generation runs, and security events. | `AuditLog` | `audit_logs` | `AuditLog` |
| **Data Staleness** | A state indicating that enrollments or cycle parameters were modified after a graph snapshot or schedule was generated. | `is_stale` (`bool`) | `data_version` comparison | `isStale` |

---

## 2. Hard Constraints Catalogue (§12, §14.1)

All code references must use these exact constant names and identifiers:

1. `HARD_NO_STUDENT_CLASH`: No student has two exams assigned to the same time slot or overlapping time periods.
2. `HARD_COMPLETENESS`: Every in-scope examination in the cycle has exactly one scheduled assignment.
3. `HARD_NO_DUPLICATE_ASSIGNMENT`: No examination is assigned more than once within the same schedule version.
4. `HARD_DURATION_FIT`: The exam duration must not exceed the scheduled time slot duration (`exam.duration_minutes <= slot.duration_minutes`).
5. `HARD_NO_HOLIDAY_EXAM`: No exam may be scheduled on a designated university holiday or excluded calendar date.
6. `HARD_NO_DISABLED_SLOT`: No exam may be scheduled in a disabled or non-operational time slot.
7. `HARD_LOCKED_EXAM_PRESERVED`: Every locked examination must remain in its specifically locked time slot during regeneration.
8. `HARD_EXAM_DATE_RESTRICTIONS`: Examinations must not be scheduled on dates explicitly listed in the subject's restricted dates.
9. `HARD_SESSION_CAPACITY`: The number of concurrent exams scheduled in a single session must not exceed `max_exams_per_session` if configured.
10. `HARD_VALID_REFERENCES`: Assigned exams and time slots must belong strictly to the target scheduling cycle.

---

## 3. Soft Constraints Catalogue (§14.2)

Standard default penalty weights:

| Constraint Code | Description | Default Weight | Formula / Unit |
|---|---|---|---|
| `SOFT_STUDENT_SAME_DAY` | A student has two or more exams scheduled on the same calendar date. | 10 | Per student per extra exam on date |
| `SOFT_STUDENT_CONSECUTIVE` | A student has exams in back-to-back sessions on the same calendar day (e.g., Morning + Afternoon). | 5 | Per student per consecutive occurrence |
| `SOFT_SESSION_LOAD_IMBALANCE` | Uneven distribution of total exams across sessions within a single day. | 3 | Standard deviation of session sizes |
| `SOFT_PREFERRED_DATE_MISSED` | An exam is scheduled on a date outside its configured preferred dates list. | 2 | Per missed preferred exam |
| `SOFT_MOVED_UNLOCKED_EXAM` | An unlocked exam is relocated to a different slot during regeneration (disruption). | 1 | Per moved unlocked exam |

---

## 4. Algorithmic Module Separation (PRD §20, §36)

To protect architectural boundaries:
- The `algorithms/` package contains **only pure mathematical and algorithmic code**.
- **No imports** of FastAPI, SQLAlchemy, database connections, repositories, or services are allowed inside `algorithms/`.
- Inputs to `algorithms/` are plain Python types: `dict[str, set[str]]`, `dict[str, int]`, `list[str]`.
- Outputs are pure dataclasses: `ColoringResult`, `ValidationResult`, `GraphMetrics`.
