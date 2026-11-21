# Project Scope and Requirements Baseline

**Project:** University Examination Timetable Scheduling System  
**Document Version:** 1.0.0  
**Date:** 2026-11-21  
**Source Baseline:** PRD.md v1.0, implementation.md v1.0  
**Phase:** Phase 0 (Planning and Decisions — Task P0.1)

---

## 1. Executive Scope Summary

The University Examination Timetable Scheduling System automates the generation, validation, visualization, optimization, manual editing, and publishing of conflict-free examination schedules for higher education institutions.

The core computational mechanism uses **graph coloring algorithms** (DSATUR as primary; Greedy Coloring and Welsh–Powell as comparative baselines) where examinations are represented as vertices and shared student enrollments are represented as weighted, undirected edges. Color classes are mapped deterministically to real calendar time slots, subject to hard operational constraints and soft quality preferences.

---

## 2. In-Scope Requirements (MVP: P0 + P1)

The MVP scope encompasses all **P0 (Must Have)** and **P1 (Strongly Recommended)** requirements defined in PRD §29 and tracked through Phases 1 to 16.

### 2.1 P0 (Must Have — Core Release Gate)

1. **Authentication & Authorization (FR-01, PRD §7):**
   - Secure authentication via email/password.
   - Argon2id password hashing.
   - Role-Based Access Control (RBAC) supporting four roles: `admin`, `coordinator`, `faculty`, `student`.
   - Department-scoped authorization for coordinators and faculty.
   - Student self-access isolation (students access only their own records).

2. **Academic Data & Subject Management (FR-02, FR-03, FR-04):**
   - CRUD and archival for academic years, semesters, departments, programs, subjects, and students.
   - Enrollment association per student, subject, and scheduling cycle.
   - Dynamic computation of enrollment counts and conflict degrees.
   - Data staleness signaling when underlying academic data changes.

3. **CSV Import Engine (FR-05):**
   - Transactional, atomic multi-table bulk import for Subjects, Students, and Enrollments.
   - Two-step flow: Upload/Preview (validation, duplicate checking, reference resolution) -> Confirmation/Commit.
   - Zero tolerance for silently corrupt or skipped data: comprehensive row-level error reporting.
   - Spreadsheet formula injection protection on all imported/exported data.

4. **Scheduling Cycle & Slot Management (FR-06, FR-11):**
   - Cycle configuration: start/end dates, active weekdays, holiday exclusions, daily session windows, duration bounds.
   - Pure function time-slot generator producing deterministic calendar slots.
   - Capacity summary and chromatic lower-bound feasibility pre-checks.

5. **Conflict Graph Engine (FR-07):**
   - Pure, non-DB graph construction: vertices (exams), edges (shared enrollments with integer weights).
   - O(Σ k(k-1)/2) student-centric streaming construction.
   - Independent graph validator verifying edge symmetry, absence of self-loops, and exact correspondence with raw enrollments.
   - Comprehensive graph metrics: |V|, |E|, degree distribution, connected components (iterative BFS/DFS), density, chromatic bounds.
   - Versioned graph snapshots and cryptographic enrollment hashing (`SHA-256`) for staleness detection.

6. **Coloring Algorithm Suite (FR-09, §12):**
   - Independent, zero-dependency implementations of:
     - **Greedy Coloring** (with configurable vertex orderings).
     - **Welsh–Powell** (degree-descending with deterministic tie-breaking).
     - **DSATUR** (saturation degree, tie-broken by degree and stable vertex key).
   - Support for precolored / locked exams.
   - Independent coloring validator verifying that no adjacent vertices share a color and all vertices are colored.
   - Algorithmic performance metrics: vertex visits, color checks, execution runtime (ms).

7. **Scheduling Engine & Color-to-Slot Mapping (FR-11, FR-12, FR-13):**
   - Color-to-slot mapping via bipartite matching ensuring each color class occupies exactly one compatible time slot.
   - Duration compatibility enforcement: `ExamDuration <= SlotDuration`.
   - Constraint engine enforcing all 10 hard constraints.
   - Infeasibility diagnostics: clear reporting of slot deficits and duration mismatches without silent drops.

8. **Schedule Versions, Editing & Publishing (FR-14, FR-15, FR-16, FR-17, FR-19):**
   - Candidate vs Published version lifecycle.
   - Server-side validated manual moves and swaps with conflict explanations.
   - Exam locking mechanism guaranteeing slot preservation during regeneration.
   - Deterministic schedule regeneration with disruption minimization.
   - Atomic schedule publishing with strict immutability of published records.

9. **Student View & Exports (FR-18, FR-20):**
   - Dedicated, privacy-isolated student timetable view.
   - Printable timetable and structured CSV exports for all scopes.
   - Formatted PDF timetable exports via ReportLab.

10. **Audit & Accountability (FR-21):**
    - Immutable audit log tracking all administrative, import, scheduling, editing, locking, and publishing actions with before/after state redaction.

---

### 2.2 P1 (Strongly Recommended — Included in Full MVP Implementation)

1. **Interactive Conflict Graph Visualization (FR-08):**
   - React Flow visualizer with force-directed layout.
   - Node styling scaled by degree, color/slot badges, lock indicators.
   - Search, neighbor highlighting, connected component filtering, metrics panel.
   - Zero student PII exposed in graph views.

2. **Algorithm Comparison Lab (FR-10, FR-22):**
   - Multi-algorithm side-by-side benchmark execution on identical graph snapshots.
   - Metrics comparison: slots used, execution time (median of N runs), color class variance/imbalance, feasibility on calendar.
   - Educational DSATUR step-by-step trace viewer.

3. **Soft Constraint Optimization (FR-12, §14):**
   - Multi-factor soft penalty scoring: consecutive exam sessions, multi-exam days per student, session load balancing, preferred dates.
   - Post-coloring local improvement heuristic (bounded pairwise class swapping).

4. **Change Impact & Diff Reporting (FR-17):**
   - Side-by-side version comparison showing moved exams, unchanged exams, and soft-score delta.

5. **Excel (XLSX) Export Engine (FR-20):**
   - Multi-tab Excel export via OpenPyXL with cycle metadata and formatting.

---

## 3. Explicit Non-Goals / Out-of-Scope (§5)

The following capabilities are formally excluded from the MVP scope:

| Item | Reason for Exclusion / Deferred Phase |
|---|---|
| **Online Examination Delivery** | Belongs to Learning Management Systems (LMS / Canvas / Moodle). |
| **Question Paper Authoring & Printing** | Examination board editorial workflow; distinct security domain. |
| **Grading, Scoring & Result Management** | Academic registrar/grading system domain. |
| **Student Attendance Tracking** | Invigilation hall management software. |
| **Fee Collection & Admissions** | Enterprise Resource Planning (ERP) domain. |
| **Predictive Student Performance** | Analytics/BI domain. |
| **AI / LLM-Generated Timetables** | Non-deterministic; conflicts cannot be formally guaranteed or mathematically proven. |
| **Faculty Invigilator Allocation** | Post-MVP backlog (§30.2); requires staff availability contracts. |
| **Physical Classroom / Room Allocation** | Post-MVP backlog (§30.1); slot-level scheduling precedes spatial assignment. |
| **Campus Transit / Travel-Time Optimization** | Post-MVP backlog; single-campus focus for initial release. |
| **Real-time SIS/ERP Direct Database Sync** | CSV file import/export provides standardized boundary decoupling. |

---

## 4. Stakeholders & Personas

- **Examination Administrator (Primary):** Manages cycles, imports academic data, configures session constraints, generates schedules, resolves edge cases, locks critical exams, and publishes timetables.
- **Department Coordinator:** Reviews department-specific timetables, inspects conflict degrees, submits structured change requests.
- **Faculty Member:** Views scheduled exam sessions for courses taught; checks room/time compatibility.
- **Student:** Authenticates to view a personalized, clash-free examination timetable with calendar integration and PDF download.
- **System Administrator:** Oversees operational infrastructure, database migrations, security policies, backup verification, and administrative user provisioning.

---

## 5. Success Metrics Baseline (§4.2)

| Metric | Target | Verification Method |
|---|---|---|
| Student exam conflicts in published schedule | **0** | Automated verification by independent constraint validator |
| Duplicate exam assignments | **0** | DB unique constraint `(schedule_version_id, exam_id)` |
| Unscheduled exams after successful generation | **0** | Completeness assertion in validation engine |
| Silently accepted invalid CSV rows | **0** | Strict preview validation with row-by-row error reporting |
| Validation coverage on published schedules | **100%** | Hard transactional check in publish workflow |
| Graph construction correctness | **100%** | Property-based tests and brute-force cross-validation |
| Generation response time (500 exams) | **< 5.0 seconds** | Algorithmic benchmarking harness |
| Conflict graph rendering performance | **Interactive at 500 nodes** | Web worker layout calculation and viewport virtualization |
| Data reproducibility | **100% deterministic** | Bit-identical output across repeated runs given same seed/order |
