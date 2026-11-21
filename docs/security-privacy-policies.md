# Enterprise Security, Data Retention & Privacy Policies

**Document Reference:** PRD §19, Tasks P14.12, P14.13, P14.14  
**Classification:** Confidential — University Examination Administration  
**Last Updated:** November 2026  

---

## 1. Data Minimization and Student Privacy (FERPA / GDPR)

### 1.1 Strict Isolation of Student Views
Under no circumstances may individual student users view enrollments, grades, course combinations, or personally identifiable information (PII) belonging to any other student.
- All `/me/timetable` and `/students/{id}/timetable` endpoints enforce authentication identity binding.
- A student user may only read their own timetable. Any attempt to supply an ID belonging to another student yields an immediate `403 Forbidden` (`FORBIDDEN_RESOURCE_ACCESS`).
- The conflict graph visualization in the administrative UI exposes strictly anonymized course-level vertices ($V = \{E_1, E_2, \dots\}$) and numeric clash weights ($w_{uv}$). Zero student names, roll numbers, or emails are serialized to the frontend DOM or state.

### 1.2 Formula Injection Neutralization
All tabular downloads (RFC 4180 CSV) pass through sanitization filters before transmission:
- Any cell value beginning with `=`, `+`, `-`, or `@` is prefixed with a single quote character (`'`).
- This neutralizes Dynamic Data Exchange (DDE) and formula execution in Microsoft Excel and LibreOffice Calc.

---

## 2. Synthetic Data Protocol

### 2.1 Explicit Tagging
In accordance with Task P14.13, all benchmark datasets, demonstration fixtures, and mock student rosters must be explicitly prefixed with `[SYNTHETIC]`:
- Synthetic course codes: `[SYNTHETIC]-CS101`, `[SYNTHETIC]-EE201`
- Synthetic student numbers: `[SYNTHETIC]-STU-00001`
- Synthetic emails: `student@synthetic.university.edu`

This ensures that mock records can never be confused with live university students or leaked into production audits.

---

## 3. Data Retention and Lifecycle Archival

| Entity | Active Retention | Archived Retention | Purge / Anonymization Policy |
| :--- | :--- | :--- | :--- |
| **Audit Logs** | 12 Months | 7 Years (Cold Storage) | Immutable append-only; cryptographic hashes preserved. |
| **Published Timetables** | Current Cycle | Indefinite | Retained as permanent institutional record. |
| **Candidate Versions** | 60 Days post-cycle | 1 Year | Soft-deleted after cycle closure. |
| **Student Enrollments** | Active Academic Year | 5 Years | Anonymized into aggregate statistics upon graduation. |

---

## 4. Transactional Boundaries and Concurrency

### 4.1 ACID Transaction Boundaries
- **CSV Bulk Import:** Executed in chunks of 500 records inside an explicit atomic transaction (`BEGIN ... COMMIT`). If an unrecoverable batch failure occurs, the transaction rolls back cleanly (`ROLLBACK`), leaving zero partial records.
- **Graph Rebuild:** An exclusive snapshot lock ensures that graph computation reads a consistent freeze of enrollments (`SERIALIZABLE` or `REPEATABLE READ` snapshot).
- **Publish Operation:** Swapping from an old published version to a new version is executed in a single atomic transaction. The old version is updated to `Archived`, the new version is set to `Published`, and an immutable audit log entry is written simultaneously.
- **Manual Moves:** Enforces row-version optimistic concurrency (`row_version`). If two coordinators attempt to move the same exam concurrently, the second coordinator receives `409 Conflict` and is instructed to refresh.
