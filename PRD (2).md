# University Examination Timetable Scheduling System
## Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Proposed / Ready for implementation planning  
**Product type:** Full-stack web application  
**Primary domain:** University examination scheduling  
**Core method:** Graph coloring  
**Primary algorithm:** DSATUR  
**Baseline algorithms:** Greedy Coloring and Welsh–Powell  
**Suggested stack:** React + Vite, TypeScript, Tailwind CSS, Python FastAPI, PostgreSQL

---

## 1. Executive Summary

The University Examination Timetable Scheduling System automates the creation, validation, visualization, optimization, and publishing of university examination timetables.

Exam scheduling is a constraint-heavy problem. Students enroll in multiple subjects, so some exams cannot occur simultaneously. Administrators also have to work within a limited exam period, available sessions, holidays, durations, department preferences, and special constraints. Manually producing a timetable becomes difficult as the number of courses and students increases, and timetable edits can introduce hidden conflicts.

The system models examinations as vertices in an undirected graph. An edge connects two exams when they share at least one enrolled student. A graph-coloring algorithm assigns colors to vertices such that adjacent vertices have different colors. Each color is mapped to a time slot, ensuring that conflicting exams do not overlap.

The application will support importing academic data, generating conflict graphs, running multiple coloring algorithms, visualizing graph structure, translating color groups into actual dates and sessions, validating schedules, allowing controlled manual edits and locked exams, comparing algorithm performance, viewing student-specific schedules, and exporting the final timetable.

The application is intended to be a usable scheduling tool and a demonstrable Design and Analysis of Algorithms project. Algorithm implementations must be independently written and instrumented so that algorithmic behavior and complexity can be evaluated.

---

## 2. Product Vision

Provide a reliable, explainable, and practical scheduling platform that transforms university enrollment data into conflict-free examination timetables with minimal scheduling effort.

### Product principles

1. **Correctness first:** Hard constraints must never be violated in a published timetable.
2. **Explainability:** Show why exams conflict and why a slot was assigned.
3. **Algorithm transparency:** Expose algorithm selection, metrics, and results.
4. **Human control:** Administrators can edit schedules, but invalid changes are prevented or clearly blocked.
5. **Reproducibility:** The same input and algorithm configuration should produce repeatable results when deterministic tie-breaking is enabled.
6. **Usability:** Data import, schedule generation, and review should be straightforward.
7. **Separation of concerns:** Graph coloring, slot assignment, constraint validation, persistence, and UI are separate modules.

---

## 3. Problem Statement

Manual exam timetable preparation can result in:

- Student exam clashes.
- Uneven distribution of exams across days or sessions.
- Excessive timetable length.
- Unbalanced session loads.
- Repeated manual revisions.
- Difficulty accommodating late enrollment changes.
- Unintentional conflict introduction during editing.
- Lack of visibility into highly conflicting courses.
- Poor ability to compare alternative schedules.
- No measurable or reproducible explanation of how a schedule was generated.

The system will use graph modeling and graph-coloring algorithms to solve the core conflict problem, then apply operational constraints to map color groups to real examination sessions.

---

## 4. Goals and Success Metrics

### 4.1 Primary goals

- Generate a valid timetable from imported enrollment data.
- Guarantee that no student has two overlapping exams.
- Minimize the number of required time slots, subject to configured constraints.
- Provide Greedy, Welsh–Powell, and DSATUR implementations.
- Make the conflict graph interactive and understandable.
- Permit safe editing, locking, and regeneration.
- Export and publish schedules.

### 4.2 Success metrics

| Metric | Target |
|---|---|
| Student exam conflicts in published schedule | 0 |
| Duplicate exam assignments | 0 |
| Unscheduled exams after successful generation | 0 |
| Invalid CSV rows silently accepted | 0 |
| Schedule validation | 100% of published schedules |
| Graph construction correctness | 100% against test fixtures |
| Generation response time | Target under 5 seconds for 500 exams on typical hardware; benchmark and revise |
| Conflict graph rendering | Usable for 500 nodes; larger graphs may use filtering or progressive rendering |
| Export correctness | All published exams included, with correct date/time |
| Reproducibility | Same dataset/configuration produces same output when deterministic mode is enabled |

Targets are provisional and should be validated on the actual deployment environment.

---

## 5. Non-Goals / Out of Scope for MVP

The first release will not include:

- Online exam delivery.
- Question paper authoring.
- Grading or result management.
- Attendance management.
- Fees, admissions, or full ERP functions.
- Predictive student performance features.
- AI-generated scheduling.
- Faculty invigilation assignment optimization.
- Advanced room allocation optimization.
- Campus transportation or travel-time optimization.
- Automated integration with external ERP/SIS systems.
- Complex multi-campus scheduling.

Room assignment, invigilator assignment, multi-campus coordination, and external integrations may be future extensions.

---

## 6. Stakeholders and User Personas

### 6.1 Examination Administrator
Primary operator who creates scheduling cycles, imports data, configures time slots, runs algorithms, edits, validates, and publishes timetables.

### 6.2 Department Coordinator
Reviews schedules for a department, checks department-specific needs, and submits change requests. Scope may be limited by permissions.

### 6.3 Faculty Member
Views relevant schedules and reports potential issues. No direct timetable editing in MVP.

### 6.4 Student
Views personal examination schedule, searches subjects, and downloads or prints their timetable.

### 6.5 System Administrator
Maintains application, users, configuration, security, backups, and deployment.

---

## 7. Roles and Permissions

| Capability | Admin | Coordinator | Faculty | Student |
|---|---|---|---|---|
| Manage users | Yes | No | No | No |
| Import students/enrollments | Yes | Scoped/optional | No | No |
| Manage subjects | Yes | Department-scoped | No | No |
| Configure exam period | Yes | No | No | No |
| Build conflict graph | Yes | Department-scoped view | View-only/limited | No |
| Generate schedule | Yes | No | No | No |
| Compare algorithms | Yes | View-only | No | No |
| Edit timetable | Yes | Request changes | No | No |
| Lock exams | Yes | No | No | No |
| Validate schedule | Yes | View report | No | No |
| Publish timetable | Yes | No | No | No |
| View full timetable | Yes | Department scope | Department scope | No |
| View personal schedule | Yes | Yes | Yes | Yes |
| Export schedule | Yes | Department scope | Department scope | Personal |

All permissions must be enforced by backend authorization checks. Frontend hiding is not security.

---

## 8. Terminology and Domain Model

| Term | Definition |
|---|---|
| Scheduling Cycle | One timetable generation exercise, e.g. Semester 5 End-Term Exams |
| Exam | An assessment event for a subject in a scheduling cycle |
| Subject/Course | Academic unit associated with an exam |
| Student | Student record |
| Enrollment | Relationship connecting a student to a subject |
| Vertex | Graph node representing an exam |
| Edge | Conflict relation between two exams |
| Conflict Graph | Graph of exams and student-overlap conflicts |
| Degree | Number of neighboring conflict vertices |
| Color | Abstract slot-group identifier assigned by a coloring algorithm |
| Time Slot | Actual date/time period to which a color is mapped |
| Saturation Degree | Count of distinct colors among a vertex's colored neighbors |
| Chromatic Number | Minimum number of colors required to color a graph |
| Locked Exam | Exam whose assignment is preserved during regeneration |
| Hard Constraint | Must be satisfied for schedule validity |
| Soft Constraint | Preference to optimize, not always guaranteed |
| Schedule Run | One algorithm execution with input/configuration and output |
| Published Schedule | Approved timetable made visible to relevant users |

---

## 9. Scope and Modules

The application is organized into modules:

1. Authentication and user management
2. Academic data management
3. Student management
4. Subject/course management
5. Enrollment management
6. CSV import and validation
7. Scheduling cycle management
8. Exam/session configuration
9. Conflict graph construction
10. Graph statistics
11. Interactive graph visualization
12. Coloring algorithm engine
13. Time-slot mapping
14. Constraint validation
15. Timetable visualization
16. Manual timetable editor
17. Exam locking
18. Regeneration and repair
19. Algorithm comparison lab
20. Student timetable lookup
21. Export and publishing
22. Audit log and history
23. Reports and analytics

---

# 10. Functional Requirements

## FR-01 — Authentication and Authorization

The system must support:

- Secure login and logout.
- Password hashing.
- Role-based authorization.
- Session or token handling.
- Account activation/deactivation.
- Protected backend endpoints.
- Access-denied handling.

**Acceptance criteria**
- Unauthenticated users cannot access protected resources.
- Student accounts cannot change schedules.
- Department-scoped users cannot access unrelated department data unless granted.
- Backend authorization is tested independently of frontend visibility.

## FR-02 — Academic Structure Management

Manage:

- Academic years.
- Semesters.
- Departments.
- Programs.
- Course/subject catalog.
- Scheduling cycles.

Required actions: create, view, update, archive, search, and filter where applicable.

## FR-03 — Subject Management

A subject record must include:

- Subject code (unique within the applicable academic scope).
- Subject name.
- Department.
- Program.
- Semester.
- Credits (optional).
- Exam duration in minutes.
- Exam type.
- Enrollment count (derived, not manually trusted).
- Preferred dates (optional).
- Restricted dates (optional).
- Priority (optional).
- Active status.

Operations:

- Create/edit/delete or archive.
- Bulk import.
- Search by code/name.
- Filter by department, program, semester.
- View enrollment list and conflict degree.
- View scheduling status.

## FR-04 — Student and Enrollment Management

The system must:

- Create/update/archive student records.
- Assign and remove subject enrollments.
- Import student and enrollment data.
- Display a student's subjects.
- Display a subject's students.
- Detect invalid and duplicate enrollment records.
- Maintain stable student IDs.

Student data fields:

- Student ID (unique).
- Name.
- Department.
- Program.
- Semester/year.
- Optional email.
- Status.

Enrollment fields:

- Student ID.
- Subject ID.
- Academic cycle.
- Enrollment status.

## FR-05 — CSV Import

Supported import types:

- Students.
- Subjects.
- Enrollments.

### Example student CSV

```csv
student_id,student_name,department,semester
S001,Student One,CSE,5
S002,Student Two,CSE,5
S003,Student Three,IT,5
```

### Example subject CSV

```csv
subject_code,subject_name,department,semester,duration_minutes
CS301,Data Structures,CSE,5,180
CS302,Operating Systems,CSE,5,180
CS303,Database Systems,CSE,5,180
```

### Example enrollment CSV

```csv
student_id,subject_code
S001,CS301
S001,CS302
S002,CS301
S002,CS303
S003,CS302
S003,CS303
```

### Import process

1. Upload CSV.
2. Parse headers and records.
3. Validate schema and field values.
4. Identify duplicate rows.
5. Identify unknown student/subject references.
6. Present valid/invalid row counts and error details.
7. Allow cancellation or corrected re-upload.
8. Confirm import.
9. Save records transactionally where practical.
10. Mark graph/schedule data as stale if imported changes affect it.

### Import rules

- Do not silently ignore invalid rows.
- Provide row number, field, error, and correction guidance.
- Support UTF-8.
- Limit file size and row count according to configuration.
- Prevent injection or unsafe file handling.
- Validate identifiers and numeric ranges.

## FR-06 — Scheduling Cycle Configuration

An administrator can create a scheduling cycle with:

- Name.
- Academic year.
- Semester/program scope.
- Start date.
- End date.
- Exam days of week.
- Holidays.
- Daily sessions.
- Session start/end times.
- Breaks.
- Maximum exams per session (optional).
- Maximum exams per day (optional).
- Allowed exam durations.
- Default exam duration.
- Preferred time slots (optional).
- Special restrictions.
- Status: Draft, Generated, Reviewed, Published, Archived.

### Example

| Setting | Example |
|---|---|
| Cycle | Semester 5 End-Term |
| Start date | 10 June |
| End date | 20 June |
| Allowed days | Monday–Saturday |
| Sessions/day | 2 |
| Morning | 09:00–12:00 |
| Afternoon | 14:00–17:00 |
| Sunday | Excluded |
| Holidays | Configurable |

The system calculates valid time slots from the calendar and configuration.

## FR-07 — Conflict Graph Construction

This is the core graph model.

### Formal model

Let:

\[
G=(V,E)
\]

- \(V\): set of exams/subjects.
- \(E\): set of undirected conflict edges.

An exam is a vertex. Two vertices share an edge if their corresponding exams share at least one student.

### Conflict rule

For subjects \(A\) and \(B\):

\[
Students(A)\cap Students(B)\neq\varnothing
\Rightarrow (A,B)\in E
\]

A shared student makes the pair a hard conflict for simultaneous scheduling.

### Requirements

- One vertex per scheduled exam.
- Edges for overlapping enrollment sets.
- No self-loops.
- No duplicate edges.
- Undirected edge representation.
- Rebuild graph when enrollment data changes.
- Record conflict counts.
- Record graph version or data snapshot.
- Explain conflicts by identifying shared students to authorized users.
- Support graph export as JSON/CSV for analysis.

### Graph statistics

Calculate:

- Vertex count \(|V|\).
- Edge count \(|E|\).
- Average degree.
- Maximum degree.
- Minimum degree.
- Degree histogram.
- Connected component count.
- Largest connected component size.
- Isolated vertices.
- Conflict density.
- Top exams by degree.

### Conflict density

For a simple undirected graph:

\[
D=\frac{2|E|}{|V|(|V|-1)}
\]

For graphs with fewer than two vertices, density is zero.

## FR-08 — Interactive Conflict Graph Visualization

The application shall display a graph with:

### Node attributes
- Subject code.
- Subject name.
- Department.
- Semester.
- Enrollment count.
- Degree/conflict count.
- Color/time slot.
- Lock status.

### Edge attributes
- Conflict status.
- Shared-student count.
- Authorized list of shared students (on demand).

### Interaction
- Zoom and pan.
- Drag nodes.
- Search subject.
- Select node.
- Highlight neighbors.
- Highlight connected components.
- Filter by department/semester.
- Filter by color/time slot.
- Toggle labels.
- Highlight high-degree nodes.
- View node details.
- View edge details.
- Switch between original graph and colored graph.
- Reset layout.
- Fit graph to screen.

### Visual states
- Uncolored.
- Colored.
- Locked.
- Selected.
- High-degree.
- Conflict highlighted.
- Invalid placement.

Graph rendering must remain responsive for the expected MVP data size. For larger graphs, filters, progressive rendering, or layout options may be used.

## FR-09 — Graph Coloring Engine

The system shall provide three independently implemented algorithms.

### Algorithm A — Greedy Coloring

Process vertices in a specified order. For each vertex, assign the smallest color not used by already-colored adjacent vertices.

Pseudocode:

```text
GREEDY-COLOR(G, order):
    for each vertex v in V:
        color[v] = UNCOLORED

    for v in order:
        forbidden = colors of colored neighbors of v
        color[v] = smallest non-negative color not in forbidden

    return color
```

The result is valid for the graph when implemented correctly, but color count depends on vertex ordering.

### Algorithm B — Welsh–Powell

1. Sort vertices by descending degree.
2. Break ties deterministically (e.g., subject code).
3. Apply greedy coloring in that order.

Pseudocode:

```text
WELSH-POWELL(G):
    order = vertices sorted by descending degree
    break ties using stable subject identifier
    return GREEDY-COLOR(G, order)
```

This is a heuristic, not a guarantee of minimum colors.

### Algorithm C — DSATUR (Primary)

At each iteration, select an uncolored vertex with the highest saturation degree. If tied, use highest graph degree. If still tied, use a deterministic identifier tie-breaker.

Saturation degree:

\[
sat(v)=|\{color(u):u\in N(v), u\text{ colored}\}|
\]

Pseudocode:

```text
DSATUR(G):
    initialize all vertices as uncolored
    while any vertex remains uncolored:
        choose uncolored vertex v with:
            maximum saturation degree
            then maximum degree
            then stable identifier tie-break
        forbidden = colors of colored neighbors of v
        assign smallest available color to v
        update saturation information for uncolored neighbors
    return coloring
```

DSATUR is a strong heuristic for many graph-coloring instances but does not guarantee an optimal coloring in general.

### Algorithm options

- Algorithm selection.
- Deterministic tie-breaking toggle (default on).
- Optional vertex-order configuration for Greedy.
- Execution timeout or cancellation for future advanced algorithms.
- Run metadata.
- Input graph version.

### Output

- Vertex-to-color mapping.
- Color count.
- Execution time.
- Number of vertex visits/selections.
- Number of color checks.
- Validity result.
- Algorithm name and version.
- Configuration.
- Graph snapshot/version.
- Optional explanation trace for educational mode.

## FR-10 — Algorithm Comparison Lab

Users can run all algorithms against the same graph and compare results.

### Metrics

- Number of colors/time-slot groups.
- Runtime (milliseconds).
- Number of exams scheduled.
- Validity.
- Number of unscheduled exams.
- Color group sizes.
- Largest group size.
- Smallest group size.
- Distribution imbalance.
- Graph size and density.

### Comparison table

| Algorithm | Slots Used | Runtime | Valid | Exams Scheduled |
|---|---:|---:|---|---:|
| Greedy | Result | Result | Yes/No | Count |
| Welsh–Powell | Result | Result | Yes/No | Count |
| DSATUR | Result | Result | Yes/No | Count |

### Requirements

- Execute algorithms on identical graph snapshots.
- Display results side by side.
- Do not misrepresent algorithmic optimality.
- Explain that fewer colors generally means fewer abstract sessions, but real scheduling constraints may require more slots.
- Allow a result to be selected as the candidate timetable.
- Save runs for later review.

## FR-11 — Color-to-Time-Slot Mapping

Graph colors are abstract groups. The scheduler must map each color to a real examination session.

A time slot includes:

- Slot ID.
- Date.
- Start time.
- End time.
- Session label.
- Capacity (optional).
- Availability.
- Duration compatibility.

### Requirements

- Generate slots from scheduling-cycle configuration.
- Exclude holidays and non-exam days.
- Respect session times.
- Ensure duration fits slot.
- Allow different examination durations only if slot compatibility is valid.
- Ensure one color group is not split into overlapping sessions.
- Support configurable session ordering.
- Support assigning color groups to dates/sessions.
- Detect insufficient available slots.
- Report infeasibility rather than silently dropping exams.

**Important distinction:** Coloring minimizes abstract groups. Actual calendar scheduling may require more sessions if durations, room capacities, session availability, or other constraints are introduced. The initial version primarily handles student conflicts and session compatibility.

## FR-12 — Constraint Engine

The system separates hard constraints from soft preferences.

### Hard constraints (MVP)

1. Exams with shared students must not overlap.
2. Each exam must be assigned exactly one valid time slot in a completed timetable.
3. Exam duration must fit the assigned slot.
4. No exam may be assigned to an excluded date.
5. No exam may be assigned to a disabled session.
6. Locked exams must retain their assignments during regeneration.
7. No duplicate exam assignments.
8. Published schedule must pass validation.

### Soft constraints (MVP / optional configurable)

1. Avoid multiple exams for the same student on adjacent sessions when possible.
2. Distribute exams across days fairly.
3. Avoid excessive exams on one day for an individual student.
4. Balance session loads.
5. Avoid early/late sessions when configured.
6. Respect preferred dates where feasible.
7. Minimize unnecessary schedule changes during regeneration.
8. Spread exams of the same program or cohort when feasible.

Soft constraints may be implemented as scoring or post-coloring optimization. Their violation must be displayed, not treated as a hard conflict.

## FR-13 — Schedule Generation

### User flow

1. Admin opens a scheduling cycle.
2. System validates that subjects, students, and enrollment data are available.
3. Admin configures dates and sessions.
4. System constructs or refreshes the conflict graph.
5. Admin selects an algorithm.
6. Admin selects algorithm options.
7. System runs coloring.
8. System maps colors to time slots.
9. System validates all hard constraints.
10. System evaluates soft-constraint scores.
11. System displays generated schedule and metrics.
12. Admin reviews schedule.
13. Admin saves candidate schedule.
14. Admin may edit, lock, rerun, compare, or publish.

### Generation outcomes

- Successful.
- Successful with soft-constraint warnings.
- Infeasible due to insufficient time slots.
- Invalid due to algorithm or data error.
- Cancelled.
- Failed.

The system must explain failure conditions.

## FR-14 — Timetable Calendar View

Provide timetable views for:

- Whole university.
- Department.
- Program.
- Semester.
- Individual student.
- Subject.

### Calendar requirements

- Date columns or day navigation.
- Session/time rows.
- Exam cards or cells.
- Subject code and name.
- Department/semester.
- Exam duration.
- Enrollment count.
- Status.
- Conflict indicators.
- Lock indicator.
- Search.
- Filters.
- Print-friendly layout.

Views should be accessible and readable without relying solely on color.

## FR-15 — Manual Schedule Editing

Administrators can manually move an exam to another time slot.

### Interaction

- Drag and drop exam card (optional).
- Select exam and choose target slot.
- Preview change.
- Validate change.
- Confirm save.

### Validation

Before accepting an edit:

- Check student conflicts.
- Check duration compatibility.
- Check excluded dates.
- Check session availability.
- Check locked status.
- Check any configured hard constraints.

Invalid changes must be blocked and accompanied by a clear reason and conflicting subjects.

## FR-16 — Exam Locking

Administrators may lock an exam in its current time slot.

### Lock behavior

- Locked exams remain in their assigned slot during regeneration.
- Conflicting exams cannot be assigned to the same slot as a locked exam.
- Lock state is displayed in the timetable and graph.
- Only authorized administrators may lock/unlock.
- Unlock operations are recorded.

### Regeneration

When regenerating:

1. Load locked exam assignments.
2. Validate that locked assignments are mutually compatible.
3. Treat locked vertices as precolored.
4. Color remaining vertices without violating locked colors.
5. Preserve all lock assignments.
6. Validate the resulting timetable.
7. If impossible, return a clear infeasibility report.

## FR-17 — Schedule Regeneration and Repair

The system shall support rerunning algorithms after data or configuration changes.

Regeneration options:

- Full regeneration.
- Regenerate unlocked exams only.
- Preserve locked exams.
- Select algorithm.
- Compare new schedule to previous schedule.

### Change impact report

Display:

- Exams moved.
- Exams unchanged.
- Time slots added/removed.
- Hard constraint status.
- Soft score change.
- Locked exams preserved.
- Reasons for failure if regeneration is not possible.

The system should prefer minimal disruption when feasible, but not at the expense of hard constraints.

## FR-18 — Student Timetable

Students can view their own examination schedule.

### Features

- Upcoming exams.
- Date.
- Start/end time.
- Subject code/name.
- Duration.
- Department/program context.
- Sort by date.
- Print/download.
- Calendar view.
- Empty-state message if no schedule is published.

Students must not see enrollment details or personally identifiable information about other students.

## FR-19 — Publishing

Only authorized administrators can publish a timetable.

### Publish workflow

1. Select candidate schedule.
2. Run final validation.
3. Review validation report.
4. Confirm publish.
5. Mark schedule as published.
6. Make it visible to permitted users.
7. Preserve previous published version.
8. Record publication event.

Published schedules should be immutable snapshots. Changes should create a new version rather than silently rewriting history.

## FR-20 — Export

Supported export formats for MVP:

- PDF.
- CSV.
- Excel (optional depending on implementation time).

Export types:

- Full university timetable.
- Department timetable.
- Semester/program timetable.
- Student timetable.
- Subject schedule.
- Conflict graph data.
- Algorithm comparison report.

Exports must include the scheduling cycle, generation date, version, and relevant filters.

## FR-21 — Audit and History

Record important operations:

- User login/logout (security logs as appropriate).
- CSV imports.
- Subject/enrollment changes.
- Graph rebuilds.
- Algorithm runs.
- Schedule edits.
- Exam locks/unlocks.
- Schedule saves.
- Validation.
- Publishing.
- Exports.
- Failed administrative operations.

Audit entries should contain actor, action, timestamp, affected record, and before/after values where appropriate. Avoid storing sensitive data unnecessarily.

## FR-22 — Reports and Analytics

Reports should include:

- Exam count.
- Student count.
- Enrollment count.
- Graph vertices/edges.
- Conflict density.
- Average/max degree.
- Connected components.
- Slot count.
- Exam load per session.
- Exam load per day.
- Student exam distribution.
- Exams with highest conflict degree.
- Algorithm comparison.
- Schedule validation result.
- Schedule change report.

---

# 11. Graph Theory Specification

## 11.1 Graph Type

Use a simple undirected graph:

\[
G=(V,E)
\]

- No directed edges.
- No self-loops.
- No duplicate edges.
- Each exam is represented by one vertex.

## 11.2 Vertex Definition

A vertex represents an examination event, usually one exam for a subject in a particular scheduling cycle.

Vertex metadata may include:

- Exam ID.
- Subject ID.
- Subject code.
- Name.
- Student set or enrollment reference.
- Degree.
- Assigned color.
- Assigned time slot.
- Locked state.

## 11.3 Edge Definition

An edge represents at least one shared enrolled student.

\[
(u,v)\in E \iff Students(u)\cap Students(v)\neq\emptyset
\]

Edge weight, if supported, may equal the number of shared students:

\[
w(u,v)=|Students(u)\cap Students(v)|
\]

The edge remains a conflict even when the shared-student count is one.

## 11.4 Adjacency Representation

Preferred representation for coloring:

- Adjacency list.
- Set of neighbor IDs per vertex.

For example:

```text
CS301: {CS302, CS303}
CS302: {CS301, CS303}
CS303: {CS301, CS302}
CS304: {}
```

Adjacency sets avoid duplicate neighbors and make neighbor-color checks straightforward.

## 11.5 Graph Construction Strategy

Recommended approach:

1. Load active exams and enrollment relationships.
2. Build a mapping from student ID to exam IDs.
3. For each student's exam list, create pairwise conflict edges.
4. Deduplicate edges using normalized exam ID pairs.
5. Build adjacency sets.
6. Calculate graph metrics.
7. Persist graph snapshot or version metadata.

A student taking \(k\) exams contributes up to:

\[
\frac{k(k-1)}{2}
\]

pairwise conflict edges. Large enrollment lists should be processed efficiently.

## 11.6 Graph Validation

Validate:

- Every exam appears exactly once as a vertex.
- No self-edge.
- No duplicate edge.
- Symmetry of adjacency.
- Every edge corresponds to shared enrollment.
- No shared-enrollment exam pair is missing an edge.
- Vertex IDs resolve to valid exams.

---

# 12. Algorithm Specification and Analysis

## 12.1 Greedy Coloring

### Strategy
Color vertices in a given order. For each vertex, use the smallest color not used by its already-colored neighbors.

### Complexity
Using adjacency lists and a straightforward color lookup, typical implementation complexity is approximately \(O(V+E)\) for a fixed ordering with efficient neighbor-color tracking, though worst-case color lookup overhead depends on the implementation and number of colors.

### Strengths
- Simple.
- Fast.
- Easy to explain.
- Good baseline.

### Weaknesses
- Sensitive to vertex ordering.
- Can use many colors.

## 12.2 Welsh–Powell

### Strategy
1. Sort vertices by descending degree.
2. Apply greedy coloring in that order.
3. Use deterministic tie-breaking.

### Complexity
Sorting: \(O(V\log V)\). Greedy coloring with adjacency lists: approximately \(O(V+E)\) with efficient bookkeeping. Overall: \(O(V\log V+E)\).

### Strengths
- Uses degree information.
- Often better than arbitrary greedy ordering.
- Easy to implement and benchmark.

### Weaknesses
- Not guaranteed optimal.
- Degree-only ordering ignores dynamic saturation information.

## 12.3 DSATUR

### Strategy
Repeatedly select the uncolored vertex with the highest saturation degree; ties are resolved by graph degree and stable ID.

### Saturation degree

\[
sat(v)=|\{c(u):u\in N(v),u\text{ colored}\}|
\]

### Complexity
A simple implementation that recomputes selection and saturation each iteration can be \(O(V^2+E)\) or higher depending on data structures and color lookup. A priority-queue implementation with careful updates can improve performance but adds implementation complexity.

### Strengths
- Uses dynamically changing neighbor-color information.
- Often performs well on exam-conflict graphs.
- Strong heuristic for reducing color count.

### Weaknesses
- More complex.
- Not guaranteed optimal.
- Selection strategy can be more computationally expensive.

## 12.4 Determinism

To ensure repeatable results:

- Use stable exam IDs or subject codes for tie-breaking.
- Avoid random tie-breaking by default.
- Record algorithm version and configuration.
- Use stable sorting.

If randomized behavior is later added, record the random seed.

## 12.5 Algorithm correctness invariant

For every coloring step, the selected vertex receives a color not used by any already-colored neighbor.

Therefore, after all vertices are colored, every edge connects vertices of different colors, and the coloring is valid.

The system must independently validate output rather than trusting the algorithm.

---

# 13. Time Slot and Calendar Scheduling

## 13.1 Slot Definition

A time slot consists of:

- Slot identifier.
- Date.
- Start time.
- End time.
- Session name.
- Duration.
- Availability state.
- Optional capacity.

## 13.2 Slot Generation

Slots are generated from:

- Scheduling cycle start/end.
- Allowed weekdays.
- Holidays.
- Daily session configuration.
- Break periods.
- Duration constraints.

## 13.3 Color Mapping

A color class is a set of mutually non-conflicting exams. Map color classes to actual slots.

The mapping must account for:

- Available slot count.
- Slot duration.
- Exam duration.
- Slot restrictions.
- Locked exams.
- Any capacity constraints introduced.

## 13.4 Duration Compatibility

An exam must fit within its assigned session:

\[
ExamDuration \le SlotDuration
\]

For MVP, use fixed session lengths and allow exams only when duration is compatible. If exam durations vary substantially, the slot-generation and assignment model may need to become more sophisticated than simple color-to-slot mapping.

## 13.5 Slot Insufficiency

If the configured period cannot accommodate all exams:

- Do not silently omit exams.
- Report the number of required slots versus available slots.
- Identify incompatible duration groups.
- Recommend extending dates, adding sessions, or relaxing soft constraints.
- Keep the candidate timetable marked as incomplete until resolved.

---

# 14. Optimization and Scheduling Quality

Graph coloring minimizes the number of abstract color classes heuristically. Real scheduling quality also depends on distribution and operational preferences.

## 14.1 Hard Constraints

Must always be satisfied:

- No conflicting exams in the same slot.
- Each exam assigned exactly once.
- Valid slot and date.
- Exam duration fits.
- No exam on excluded dates.
- Locked assignments preserved.
- No duplicate assignment.
- Published schedule passes all validators.

## 14.2 Soft Constraints

May be violated, but should be scored and reported:

- Avoid too many exams for one student on a single day.
- Avoid exams in consecutive sessions for a student.
- Balance exams across days.
- Balance total exam count per session.
- Avoid very uneven department distribution.
- Respect preferred dates.
- Minimize changes from an existing schedule.
- Avoid undesirable session preferences.

## 14.3 Soft-Constraint Scoring

Use a configurable penalty system. Example:

| Soft constraint | Example penalty |
|---|---:|
| Student has two exams in one day | 10 |
| Student has exams in consecutive sessions | 5 |
| Session load exceeds preferred target | 3 |
| Preferred date missed | 2 |
| Existing unlocked exam moved | 1 |

The score is an illustrative configuration. Lower penalty is better. Penalty weights should be adjustable and explained.

## 14.4 Optimization Stages

MVP optimization stages:

1. Graph coloring.
2. Color-to-slot mapping.
3. Hard-constraint validation.
4. Soft-constraint scoring.
5. Optional local improvement/swaps.
6. Final validation.

Advanced local search may attempt moving exams between slots or swapping slot groups while maintaining all hard constraints and reducing penalty.

---

# 15. Manual Editing and Locked Exams

## 15.1 Editing Flow

1. Administrator selects an exam.
2. Chooses a target slot.
3. System previews the move.
4. Validator checks conflicts and constraints.
5. If valid, administrator confirms.
6. Schedule version is updated.
7. Audit event is recorded.

## 15.2 Invalid Move Feedback

When a move is invalid, display:

- Reason.
- Conflicting exams.
- Shared-student count.
- Incompatible slot details.
- Whether the exam is locked.

Invalid moves must not be persisted.

## 15.3 Locking

A locked exam retains its slot across schedule regeneration.

During regeneration:

- Preassign locked exams.
- Validate locked exams against one another.
- Prevent neighbors from using the locked color/slot.
- Color remaining vertices.
- Validate full result.
- Preserve locks.

If locked assignments are contradictory or the remaining schedule cannot fit, return a clear error and suggest unlocking or expanding available slots.

---

# 16. User Experience and Interface Requirements

## 16.1 Design Direction

The UI should feel like a professional university operations tool—not a generic AI dashboard.

Design principles:

- Clean, restrained, information-dense layouts.
- Strong typography hierarchy.
- Neutral color palette.
- Functional color use for time slots and status.
- Avoid unnecessary gradients, decorative cards, oversized rounded panels, and repetitive dashboard tiles.
- Prioritize tables, calendars, graph views, clear controls, and compact metrics.
- Provide consistent spacing and alignment.
- Ensure accessible contrast and keyboard navigation.

## 16.2 Application Navigation

Suggested primary navigation:

- Overview
- Scheduling Cycles
- Subjects
- Students
- Enrollments
- Conflict Graph
- Generate Schedule
- Timetable
- Algorithm Lab
- Reports
- Settings

Student navigation should be reduced to:

- My Timetable
- Academic Information
- Downloads

## 16.3 Page Specifications

### A. Overview
Show:
- Active scheduling cycle.
- Number of exams.
- Number of students.
- Conflict edges.
- Graph density.
- Current slot count.
- Schedule status.
- Last generation run.
- Validation status.
- Quick actions.

Avoid excessive decorative KPI cards.

### B. Scheduling Cycles
- List cycles.
- Create cycle.
- Edit configuration.
- Open cycle.
- Archive.
- View status.

### C. Subjects
- Table.
- Search.
- Filters.
- Subject detail.
- Enrollment count.
- Conflict degree.
- Scheduling state.
- Bulk import.

### D. Students and Enrollments
- Student search.
- Student details.
- Subject enrollment list.
- Enrollment import.
- Validation and duplicate reports.

### E. Conflict Graph
- Interactive graph.
- Graph metrics.
- Node/edge details.
- Filters.
- Coloring results.
- Highlight conflicts.
- Graph rebuild.

### F. Generate Schedule
- Scheduling-cycle selector.
- Available slots summary.
- Algorithm selector.
- Algorithm settings.
- Locked exam list.
- Generate button.
- Loading/progress state.
- Result metrics.
- Validation report.
- Save candidate action.

### G. Algorithm Lab
- Run one or more algorithms.
- Side-by-side comparison.
- Runtime.
- Slot count.
- Validity.
- Distribution.
- Graph metrics.
- Save/select result.

### H. Timetable
- Calendar/grid.
- Day and session view.
- Department/semester filters.
- Search.
- Edit mode.
- Lock controls.
- Validation indicators.
- Print/export.

### I. Student View
- Personal exam list.
- Calendar.
- Date/time.
- Subject.
- Duration.
- Download/print.

### J. Reports
- Schedule summary.
- Graph statistics.
- Algorithm report.
- Student workload.
- Exam distribution.
- Change history.
- Export controls.

---

# 17. Data Model

The MVP database should use relational storage with normalized tables.

## 17.1 User

- id (UUID/primary key)
- name
- email (unique)
- password_hash
- role
- department_id (nullable)
- status
- created_at
- updated_at

## 17.2 Department

- id
- code
- name
- created_at

## 17.3 AcademicYear

- id
- label
- start_date
- end_date

## 17.4 Semester

- id
- name/number
- academic_year_id
- start_date
- end_date

## 17.5 Student

- id
- student_number (unique)
- name
- department_id
- program
- semester
- email (optional)
- status
- created_at
- updated_at

## 17.6 Subject

- id
- subject_code
- name
- department_id
- program
- semester
- credits (nullable)
- default_exam_duration_minutes
- exam_type
- status
- created_at
- updated_at

## 17.7 Enrollment

- id
- student_id
- subject_id
- academic_year_id or cycle_id
- status
- created_at

Unique constraint should prevent duplicate active enrollment for the same student/subject/cycle.

## 17.8 SchedulingCycle

- id
- name
- academic_year_id
- semester_id (optional)
- start_date
- end_date
- configuration_json
- status
- created_by
- created_at
- updated_at

## 17.9 Exam

- id
- scheduling_cycle_id
- subject_id
- duration_minutes
- status
- created_at
- updated_at

Unique constraint: one exam per subject per scheduling cycle unless the product explicitly supports multiple assessment events.

## 17.10 TimeSlot

- id
- scheduling_cycle_id
- date
- start_time
- end_time
- session_label
- capacity (optional)
- enabled
- created_at

## 17.11 ConflictGraphSnapshot

- id
- scheduling_cycle_id
- graph_version
- vertex_count
- edge_count
- density
- graph_data_json or graph storage references
- enrollment_snapshot_hash
- created_at

## 17.12 ConflictEdge (optional persisted graph table)

- id
- graph_snapshot_id
- exam_id_a
- exam_id_b
- shared_student_count

Unique constraint on normalized exam pair.

## 17.13 ScheduleRun

- id
- scheduling_cycle_id
- graph_snapshot_id
- algorithm
- algorithm_version
- configuration_json
- execution_time_ms
- colors_used
- validity
- soft_constraint_score
- status
- created_by
- created_at

## 17.14 ExamAssignment

- id
- schedule_run_id or schedule_version_id
- exam_id
- time_slot_id
- color_id
- locked
- manual_override
- created_at
- updated_at

Unique constraints should prevent duplicate exam assignments within a schedule version.

## 17.15 ScheduleVersion

- id
- scheduling_cycle_id
- version_number
- status (Candidate, Reviewed, Published, Archived)
- source_run_id
- created_by
- created_at
- published_at (nullable)

## 17.16 AuditLog

- id
- user_id
- action
- entity_type
- entity_id
- before_json
- after_json
- timestamp
- request metadata as appropriate

---

# 18. API Requirements

Use REST APIs for MVP.

Base prefix:

```text
/api/v1
```

## 18.1 Authentication

```text
POST /auth/login
POST /auth/logout
GET  /auth/me
```

## 18.2 Students

```text
GET    /students
POST   /students
GET    /students/{studentId}
PATCH  /students/{studentId}
DELETE /students/{studentId}
POST   /students/import
GET    /students/{studentId}/subjects
GET    /students/{studentId}/timetable
```

## 18.3 Subjects

```text
GET    /subjects
POST   /subjects
GET    /subjects/{subjectId}
PATCH  /subjects/{subjectId}
DELETE /subjects/{subjectId}
POST   /subjects/import
GET    /subjects/{subjectId}/students
```

## 18.4 Enrollments

```text
GET    /enrollments
POST   /enrollments
DELETE /enrollments/{enrollmentId}
POST   /enrollments/import
GET    /enrollments/validate
```

## 18.5 Scheduling Cycles

```text
GET    /cycles
POST   /cycles
GET    /cycles/{cycleId}
PATCH  /cycles/{cycleId}
DELETE /cycles/{cycleId}
POST   /cycles/{cycleId}/slots/generate
GET    /cycles/{cycleId}/slots
```

## 18.6 Graph

```text
POST   /cycles/{cycleId}/graph/build
GET    /cycles/{cycleId}/graph
GET    /cycles/{cycleId}/graph/stats
GET    /cycles/{cycleId}/graph/export
```

## 18.7 Algorithms and Scheduling

```text
POST   /cycles/{cycleId}/schedule/generate
POST   /cycles/{cycleId}/schedule/compare
GET    /cycles/{cycleId}/schedule/runs
GET    /schedule-runs/{runId}
POST   /schedule-runs/{runId}/validate
POST   /schedule-runs/{runId}/save
```

## 18.8 Schedule Versions

```text
GET    /cycles/{cycleId}/schedules
GET    /schedules/{scheduleId}
PATCH  /schedules/{scheduleId}/assignments/{assignmentId}
POST   /schedules/{scheduleId}/assignments/{assignmentId}/lock
POST   /schedules/{scheduleId}/assignments/{assignmentId}/unlock
POST   /schedules/{scheduleId}/validate
POST   /schedules/{scheduleId}/publish
POST   /schedules/{scheduleId}/archive
```

## 18.9 Export

```text
GET /schedules/{scheduleId}/export/pdf
GET /schedules/{scheduleId}/export/csv
GET /schedules/{scheduleId}/export/xlsx
```

Endpoints and payloads may be adjusted during implementation. API validation, consistent errors, pagination, and authorization are required.

---

# 19. API Payload Examples

## Generate schedule request

```json
{
  "algorithm": "DSATUR",
  "options": {
    "deterministic": true,
    "preserveLockedExams": true,
    "optimizeSoftConstraints": false
  }
}
```

## Schedule generation response

```json
{
  "runId": "run-example",
  "algorithm": "DSATUR",
  "status": "success",
  "colorsUsed": 4,
  "executionTimeMs": 18.42,
  "scheduledExamCount": 32,
  "unscheduledExamCount": 0,
  "valid": true,
  "assignments": [
    {
      "examId": "exam-1",
      "subjectCode": "CS301",
      "colorId": 0,
      "timeSlotId": "slot-1"
    }
  ],
  "validation": {
    "hardConstraintViolations": 0,
    "softConstraintWarnings": 2
  }
}
```

Values above are illustrative only.

---

# 20. Backend Architecture

## Recommended architecture

Use a modular FastAPI backend.

```text
backend/
├── app/
│   ├── main.py
│   ├── config/
│   │   ├── settings.py
│   │   └── database.py
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── students.py
│   │       ├── subjects.py
│   │       ├── enrollments.py
│   │       ├── cycles.py
│   │       ├── graph.py
│   │       ├── scheduling.py
│   │       ├── schedules.py
│   │       └── exports.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │   ├── import_service.py
│   │   ├── graph_service.py
│   │   ├── schedule_service.py
│   │   ├── validation_service.py
│   │   ├── export_service.py
│   │   └── audit_service.py
│   ├── algorithms/
│   │   ├── greedy.py
│   │   ├── welsh_powell.py
│   │   ├── dsatur.py
│   │   ├── metrics.py
│   │   └── validators.py
│   ├── repositories/
│   ├── middleware/
│   ├── utils/
│   └── tests/
├── migrations/
├── pyproject.toml
└── README.md
```

## Backend design principles

- Keep algorithms independent from HTTP handlers.
- Keep graph construction independent from coloring.
- Keep schedule validation independent from coloring.
- Use schemas for request/response validation.
- Use repository/service patterns where they add clarity.
- Use database transactions for import and publication.
- Avoid storing derived values that can become inconsistent unless versioned/cached.
- Version graph snapshots and schedule runs.
- Implement centralized error handling.

---

# 21. Frontend Architecture

## Recommended stack

- React.
- Vite.
- TypeScript.
- Tailwind CSS.
- React Router.
- TanStack Query for server state.
- React Flow for conflict graph visualization.
- Recharts for simple analytics.
- A table library such as TanStack Table if required.
- A form/validation library if complexity warrants it.

## Suggested structure

```text
frontend/
├── src/
│   ├── app/
│   │   ├── router.tsx
│   │   └── providers.tsx
│   ├── components/
│   │   ├── layout/
│   │   ├── tables/
│   │   ├── forms/
│   │   ├── graph/
│   │   ├── calendar/
│   │   └── common/
│   ├── pages/
│   │   ├── Overview/
│   │   ├── Cycles/
│   │   ├── Subjects/
│   │   ├── Students/
│   │   ├── Enrollments/
│   │   ├── ConflictGraph/
│   │   ├── GenerateSchedule/
│   │   ├── AlgorithmLab/
│   │   ├── Timetable/
│   │   ├── Reports/
│   │   └── StudentTimetable/
│   ├── features/
│   ├── services/
│   ├── hooks/
│   ├── types/
│   ├── utils/
│   └── styles/
├── public/
└── package.json
```

---

# 22. Suggested Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React + Vite | Web application |
| Language | TypeScript | Safer frontend development |
| Styling | Tailwind CSS | Consistent styling |
| Graph | React Flow | Interactive graph |
| State/server data | TanStack Query | API caching and requests |
| Charts | Recharts | Analytics |
| Backend | FastAPI | API and business logic |
| Backend language | Python | Graph and algorithms |
| Database | PostgreSQL | Persistent data |
| ORM | SQLAlchemy | Database interaction |
| Migrations | Alembic | Schema versioning |
| Authentication | JWT or secure session | Access control |
| CSV | Python CSV/Pandas as appropriate | Import processing |
| PDF | ReportLab or equivalent | Export |
| Excel | OpenPyXL | Optional XLSX export |
| Testing | Pytest | Backend and algorithm tests |
| Frontend testing | Vitest/React Testing Library | UI tests |
| API testing | OpenAPI/Swagger, Postman | Endpoint validation |
| Deployment | Docker | Consistent environments |

Do not rely on NetworkX to perform the main graph-coloring algorithms if the purpose is to demonstrate DAA implementation. It may be used for optional graph metrics or verification, but the core algorithms should be written independently.

---

# 23. Security, Privacy, and Data Handling

## Security requirements

- Passwords stored as strong hashes, never plaintext.
- HTTPS in production.
- Authorization checks for every protected endpoint.
- Input validation.
- SQL injection prevention through ORM/parameterized queries.
- CSV upload size and type limits.
- Safe parsing of uploaded files.
- Rate limiting for authentication and sensitive endpoints.
- Secrets stored in environment variables or secret management.
- Secure error messages that do not leak sensitive information.
- Audit records for important actions.
- Backups.
- Least-privilege database access.

## Privacy requirements

- Student identifiers and enrollment data are restricted.
- Only authorized staff can view shared-student conflict details.
- Students can access only their own schedules.
- Exports should follow role permissions.
- Avoid exposing student data in graph labels or public reports.
- Retain only data required for scheduling and academic operations.

---

# 24. Non-Functional Requirements

## Performance

- Handle at least 500 exams in a typical MVP dataset.
- Support graph construction and coloring within practical interactive limits.
- Graph visualization should support filtering and rendering optimization.
- Pagination should be used for large data tables.
- Generation operations should provide a loading state.
- Long-running jobs may later move to background task execution.

## Reliability

- Validate all schedules before saving or publishing.
- Import failures should not leave partial, inconsistent records.
- Published schedules should be versioned.
- Database backups should be configured.
- Errors should be logged.

## Scalability

- Use indexed IDs and enrollment relationships.
- Build graph from efficient student-to-exam mappings.
- Avoid naive repeated full student scans for every exam pair.
- Separate algorithm execution from UI rendering.
- Use background processing if dataset size grows.

## Usability

- Clear navigation.
- Search and filtering.
- Error messages with actionable explanations.
- Empty states.
- Confirmation for destructive actions.
- Undo or version history for schedule edits where feasible.
- Keyboard and accessibility support.

## Maintainability

- Modular code.
- Type-safe API schemas.
- Unit tests.
- Documented algorithms.
- Stable interfaces between graph, coloring, and scheduling modules.

## Observability

- Log generation runs.
- Track runtime.
- Track errors.
- Record algorithm configuration.
- Track schedule validation.
- Include request IDs where appropriate.

---

# 25. Error Handling

The application must handle:

- Invalid CSV.
- Duplicate student IDs.
- Duplicate subject codes.
- Unknown student references.
- Unknown subject references.
- Empty enrollment data.
- No exams in scheduling cycle.
- Invalid dates.
- End date earlier than start date.
- No available time slots.
- Slot duration too short.
- Invalid locked assignments.
- Conflicting locked exams.
- Graph generation failure.
- Algorithm failure.
- Invalid coloring.
- Schedule validation failure.
- Database failure.
- Export failure.
- Unauthorized access.
- Stale graph due to enrollment changes.

Errors must be user-readable and must not expose secrets or internal stack traces.

---

# 26. Testing Strategy

## 26.1 Unit Tests — Data Import

Test:

- Valid CSV.
- Missing columns.
- Empty values.
- Invalid types.
- Duplicate records.
- Unknown IDs.
- Invalid enrollment.
- Large file handling.
- UTF-8 text.

## 26.2 Unit Tests — Graph Construction

Test:

- No students/no enrollments.
- One subject.
- Two subjects with no shared students.
- Two subjects with shared student.
- Multiple shared students.
- Three or more exams.
- Duplicate enrollment rows.
- No self-loops.
- Symmetric adjacency.
- Correct degree calculations.
- Correct graph density.
- Connected components.

## 26.3 Unit Tests — Coloring Algorithms

Test:

- Empty graph.
- Single vertex.
- No-edge graph.
- Complete graph.
- Bipartite graph.
- Triangle.
- Path graph.
- Cycle graph.
- Disconnected graph.
- Self-loop rejection.
- Deterministic ties.
- Locked precolored vertices.
- Invalid graph input.

For every result, verify:

\[
\forall (u,v)\in E,\ color(u)\neq color(v)
\]

## 26.4 Integration Tests

Test:

- Import → graph build.
- Graph build → coloring.
- Coloring → slot mapping.
- Schedule validation.
- Manual edit validation.
- Lock → regeneration.
- Publish → student view.
- Export → content correctness.

## 26.5 Frontend Tests

Test:

- Navigation.
- Filters.
- Import error display.
- Algorithm selection.
- Generate workflow.
- Graph interaction.
- Timetable edit flow.
- Locked exam state.
- Student view permissions.
- Export buttons.

## 26.6 End-to-End Tests

Representative flow:

1. Admin logs in.
2. Creates cycle.
3. Imports subjects.
4. Imports students.
5. Imports enrollments.
6. Validates data.
7. Builds graph.
8. Runs DSATUR.
9. Validates schedule.
10. Saves candidate.
11. Locks one exam.
12. Regenerates.
13. Confirms lock preserved.
14. Publishes.
15. Student logs in.
16. Views personal timetable.

---

# 27. Acceptance Criteria

The MVP is complete when:

1. Admin can authenticate.
2. Admin can create an exam scheduling cycle.
3. Admin can import subjects, students, and enrollments.
4. Invalid data is reported and not silently accepted.
5. The conflict graph correctly represents enrollment overlap.
6. Graph statistics are calculated correctly.
7. The graph is visualized interactively.
8. Greedy coloring is implemented.
9. Welsh–Powell is implemented.
10. DSATUR is implemented.
11. All algorithm results pass independent coloring validation.
12. Algorithms can be compared on the same graph.
13. Color classes map to valid configured time slots.
14. The timetable contains every required exam.
15. No student has overlapping exams.
16. Admin can manually move exams with validation.
17. Admin can lock exams.
18. Regeneration preserves locked exams or reports infeasibility.
19. Admin can publish a validated schedule.
20. Student can view their personal timetable.
21. Timetable exports work.
22. Important operations are logged.
23. Tests cover core graph and algorithm logic.
24. README explains setup, algorithms, usage, and limitations.

---

# 28. Development Roadmap

## Phase 1 — Requirements and Setup

- Finalize scope.
- Create repository.
- Configure frontend/backend.
- Set up PostgreSQL.
- Configure environment variables.
- Establish code conventions.
- Add linting and formatting.
- Add basic CI.

**Deliverable:** Running frontend/backend skeleton.

## Phase 2 — Academic Data

- User roles.
- Students.
- Subjects.
- Enrollments.
- CRUD endpoints.
- CSV imports.
- Validation reports.

**Deliverable:** Data management working.

## Phase 3 — Graph Engine

- Build graph from enrollment.
- Adjacency list.
- Edge deduplication.
- Graph metrics.
- Graph validation.
- Graph export.

**Deliverable:** Correct conflict graph.

## Phase 4 — Coloring Algorithms

- Greedy.
- Welsh–Powell.
- DSATUR.
- Independent validator.
- Metrics instrumentation.
- Deterministic tie-breaking.

**Deliverable:** Tested algorithm module.

## Phase 5 — Scheduling

- Exam cycle configuration.
- Calendar slot generation.
- Color-to-slot mapping.
- Duration checks.
- Hard constraints.
- Soft scoring.

**Deliverable:** Automatically generated timetable.

## Phase 6 — Visualization

- Interactive conflict graph.
- Graph filters.
- Timetable grid/calendar.
- Algorithm comparison UI.
- Metrics display.

**Deliverable:** User-facing scheduling interface.

## Phase 7 — Editing and Locks

- Manual changes.
- Validation preview.
- Lock/unlock.
- Regeneration with locked exams.
- Schedule versioning.

**Deliverable:** Safe schedule editing.

## Phase 8 — Publishing and Reports

- Publish workflow.
- Student timetable.
- PDF/CSV export.
- Reports.
- Audit log.

**Deliverable:** End-to-end MVP.

## Phase 9 — QA and Deployment

- Unit/integration/e2e tests.
- Performance testing.
- Security review.
- Docker setup.
- Deployment.
- Documentation.

**Deliverable:** Demo-ready project.

---

# 29. Suggested MVP Prioritization

## P0 — Must Have

- Academic data import.
- Student/subject/enrollment model.
- Conflict graph generation.
- Graph correctness validator.
- Greedy.
- Welsh–Powell.
- DSATUR.
- Time-slot generation.
- Timetable generation.
- Hard-constraint validator.
- Timetable view.
- Algorithm comparison.
- CSV/PDF export.
- Admin access.

## P1 — Strongly Recommended

- Interactive graph.
- Manual edits.
- Locked exams.
- Regeneration.
- Schedule versioning.
- Student timetable.
- Audit logs.
- Soft constraint metrics.

## P2 — Future Enhancements

- Room assignment.
- Room capacity.
- Invigilator assignment.
- Advanced local search.
- Backtracking exact solver for small graphs.
- Multi-campus support.
- Multi-duration optimization.
- ERP/SIS integration.
- Notification system.
- Student calendar integration.
- Schedule change notifications.
- Advanced fairness optimization.

---

# 30. Future Enhancements

## 30.1 Room Allocation

Introduce rooms with:

- Capacity.
- Building.
- Accessibility.
- Availability.
- Equipment.
- Exam-specific restrictions.

Room allocation becomes a secondary constraint problem after or alongside time-slot assignment.

## 30.2 Invigilator Allocation

Assign invigilators while respecting:

- Availability.
- Workload limits.
- Department restrictions.
- Session overlap.
- Required staffing ratios.

## 30.3 Advanced Optimization

Possible techniques:

- Backtracking.
- Branch and bound.
- Tabu search.
- Simulated annealing.
- Genetic algorithms.
- Local search.
- Constraint programming.

These can be benchmarked against graph-coloring heuristics.

## 30.4 Fairness Metrics

Evaluate:

- Exams per student per day.
- Consecutive exam sessions.
- Gaps between exams.
- Total exam period.
- Distribution of difficult exams.

## 30.5 Schedule Explanation

Show a trace explaining:

- Why an exam was selected next.
- Its degree.
- Saturation degree.
- Colors unavailable.
- Chosen color.
- How the assignment affects neighboring exams.

This can make the project especially valuable as an algorithm demonstration.

---

# 31. Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Incorrect enrollment data | Wrong conflicts and invalid schedule | Import validation and data preview |
| Graph construction bug | Schedule may contain clashes | Independent graph validator and test fixtures |
| Heuristic uses too many colors | Longer exam period | Compare algorithms and add optimization |
| Insufficient time slots | Incomplete schedule | Report infeasibility and allow configuration changes |
| Manual edits introduce conflicts | Invalid timetable | Validate every edit |
| Locked exams make schedule infeasible | Regeneration failure | Explain conflicting locks and allow authorized unlock |
| Large graph rendering is slow | Poor UX | Filtering, layout tuning, progressive rendering |
| Data privacy exposure | Student information leakage | RBAC and minimized data exposure |
| Algorithm runtime increases | Slow generation | Instrument, optimize, and optionally background-run |
| Changes invalidate graph | Stale scheduling data | Version graph snapshots and detect stale data |
| Users misinterpret colors | Confusion | Pair colors with slot labels and textual identifiers |

---

# 32. Demo Dataset

A sample dataset should be included so the application can be demonstrated without uploading real student data.

Suggested demo:

- 30–100 students.
- 8–15 subjects.
- 2 departments.
- 2 semesters or cohorts.
- Shared enrollment patterns.
- Several isolated subjects.
- A connected conflict subgraph.
- A high-degree exam.
- Configured exam dates and sessions.

The demo should produce visible differences between algorithms where possible, but not artificially claim one algorithm is always superior.

Demo data must be clearly labeled as synthetic.

---

# 33. Project Demonstration Flow

Recommended live demo:

1. Open overview.
2. Show scheduling cycle.
3. Import or load synthetic data.
4. Display data validation.
5. Open conflict graph.
6. Select a subject and highlight its conflicts.
7. Show graph metrics.
8. Run Greedy.
9. Run Welsh–Powell.
10. Run DSATUR.
11. Compare slot counts and runtime.
12. Select a candidate.
13. Show timetable.
14. Attempt an invalid exam move and demonstrate conflict prevention.
15. Lock an exam.
16. Regenerate and show lock preservation.
17. Validate final timetable.
18. Publish.
19. View student-specific timetable.
20. Export PDF.

---

# 34. Documentation Requirements

The repository documentation must include:

- Project overview.
- Problem statement.
- Features.
- Tech stack.
- System architecture.
- Graph model.
- Conflict construction explanation.
- Algorithm explanations.
- Algorithm pseudocode.
- Complexity analysis.
- Installation.
- Environment setup.
- Database setup.
- Running frontend/backend.
- Demo dataset.
- API documentation.
- Screenshots.
- Test instructions.
- Known limitations.
- Future enhancements.

---

# 35. Definition of Done

A feature is considered complete only when:

- Its requirements are implemented.
- Input validation is included.
- Authorization is applied where needed.
- Error states are handled.
- Unit tests are added.
- Integration points are tested.
- UI loading/empty/error states are handled.
- Documentation is updated.
- It does not break core timetable validation.

A schedule is considered publishable only when:

- All required exams are assigned.
- All assignments use valid time slots.
- All hard constraints pass.
- Locked assignments are preserved.
- Independent validation reports zero student conflicts.
- The administrator confirms publication.

---

# 36. Final Product Summary

The University Examination Timetable Scheduling System is a graph-theory-driven academic scheduling application.

Its central pipeline is:

**Academic Data → Enrollment Analysis → Conflict Graph → Graph Coloring → Time-Slot Mapping → Constraint Validation → Timetable → Review → Publication**

The system will implement three coloring strategies—Greedy, Welsh–Powell, and DSATUR—and compare them through measurable algorithm metrics.

The most important architectural rule is that **graph coloring generates a candidate grouping, while a separate scheduling and validation layer determines whether that grouping can become a valid real-world timetable**.

The system must never treat a heuristic result as automatically correct. Every generated, edited, regenerated, and published timetable must pass independent validation.

This separation makes the project algorithmically sound, easier to test, easier to extend, and suitable for both academic evaluation and a practical demonstration.
