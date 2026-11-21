# Implementation Plan
## University Examination Timetable Scheduling System

**Source document:** PRD.md v1.0
**Purpose:** An ordered, phase-by-phase build plan covering every requirement in the PRD (FR-01 to FR-22, Sections 11–35).
**Stack (per PRD §22):** React + Vite + TypeScript + Tailwind · FastAPI (Python) · PostgreSQL · SQLAlchemy + Alembic · Pytest · Vitest · Docker

---

## How to Use This Document

- Phases are ordered by dependency. Do not start a phase until the previous phase's **Exit Criteria** are met, unless the phase notes say it can run in parallel.
- Each task has an ID (`P3.4` = Phase 3, task 4) so it can be tracked in an issue tracker.
- Every phase ends with **Tests** and **Exit Criteria**. This implements the PRD's Definition of Done (§35): a feature is not done until it has validation, authorization, error handling, tests, UI states and docs.
- `[P0]`, `[P1]`, `[P2]` tags follow PRD §29 prioritisation. P0 = must have, P1 = strongly recommended, P2 = future (listed only in the final phase as a backlog).
- Appendix A maps every PRD requirement to the phase that implements it. Appendix B maps the 24 acceptance criteria. Appendix C lists ambiguities in the PRD and the decision this plan takes.

## Phase Overview

| # | Phase | Main output | PRD roadmap phase |
|---|---|---|---|
| 0 | Planning and decisions | Frozen scope, ADRs, conventions | 1 |
| 1 | Scaffolding and infrastructure | Running frontend/backend/DB skeleton, CI | 1 |
| 2 | Data model, auth, RBAC, audit foundation | Schema, login, role enforcement | 2 |
| 3 | Academic data management | CRUD for students, subjects, enrollments | 2 |
| 4 | CSV import | Validated, transactional imports | 2 |
| 5 | Scheduling cycles and slot generation | Cycle config, calendar slots | 5 |
| 6 | Conflict graph engine | Correct, validated, versioned graph | 3 |
| 7 | Coloring algorithms | Greedy, Welsh–Powell, DSATUR, validator | 4 |
| 8 | Scheduling engine | Color→slot mapping, constraints, generation, comparison | 5 |
| 9 | Schedule versions, editing, locks, regeneration | Safe editing backend | 7 |
| 10 | Publishing, student timetable, exports, reports (backend) | End-to-end backend MVP | 8 |
| 11 | Frontend foundation and data pages | App shell, auth, data screens | 6 |
| 12 | Frontend scheduling experience | Graph, generate, lab, timetable | 6 |
| 13 | Frontend editing, publishing, student and reports | End-to-end UI MVP | 7, 8 |
| 14 | Security, privacy, performance hardening | Hardened, benchmarked system | 9 |
| 15 | Testing and QA | Full test suite incl. E2E | 9 |
| 16 | Demo data, documentation, deployment | Demo-ready release | 9 |

Backend phases (2–10) and frontend phases (11–13) can overlap once the relevant API contract (OpenAPI) is stable. The suggested rule: frontend phase N+9 starts when backend phase N's endpoints are merged and documented.

---

## Target Repository Layout

```text
exam-scheduler/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config/            settings.py, database.py, logging.py
│   │   ├── api/v1/            auth, students, subjects, enrollments, cycles,
│   │   │                      graph, scheduling, schedules, exports, reports,
│   │   │                      users, audit
│   │   ├── models/            SQLAlchemy models
│   │   ├── schemas/           Pydantic request/response models
│   │   ├── services/          import, graph, slot, schedule, validation,
│   │   │                      export, audit, report, soft_constraint
│   │   ├── algorithms/        greedy.py, welsh_powell.py, dsatur.py,
│   │   │                      metrics.py, validators.py, types.py
│   │   ├── repositories/
│   │   ├── middleware/        request_id, error_handler, rate_limit, auth
│   │   ├── utils/
│   │   └── tests/             unit/, integration/, fixtures/
│   ├── migrations/            Alembic
│   ├── demo_data/             synthetic CSVs + seed script
│   ├── pyproject.toml
│   └── README.md
├── frontend/
│   ├── src/ app/ components/ pages/ features/ services/ hooks/ types/ utils/ styles/
│   ├── public/
│   └── package.json
├── docker/ (Dockerfiles, compose files, nginx conf)
├── docs/ (architecture, algorithms, ADRs, screenshots)
├── .github/workflows/ (CI)
└── README.md
```

Key structural rule (PRD §20, §36): `algorithms/` has **no imports** from `api/`, `models/`, `services/` or the database. It operates on plain Python data structures only. Graph construction, coloring, slot mapping and validation are separate modules with stable interfaces.

---

# Phase 0 — Planning and Decisions

**Goal:** Remove ambiguity before writing code.

### Tasks

- [ ] **P0.1** Review the PRD with stakeholders; confirm MVP scope (P0 + P1 items) and out-of-scope list (§5).
- [ ] **P0.2** Resolve the open questions in Appendix C and record each as an Architecture Decision Record in `docs/adr/`. Minimum ADRs:
  - ADR-001 Auth mechanism (JWT in httpOnly cookie vs bearer token).
  - ADR-002 Vertex definition: one `Exam` per subject per cycle.
  - ADR-003 Enrollment scoping: enrollment tied to a scheduling cycle.
  - ADR-004 Color-to-slot model: one color class = exactly one time slot.
  - ADR-005 How locked exams are precolored.
  - ADR-006 Graph storage: JSON snapshot plus persisted edge table.
  - ADR-007 Synchronous generation for MVP with a path to background jobs.
  - ADR-008 PDF library choice (ReportLab) and Excel (OpenPyXL).
- [ ] **P0.3** Define the glossary from PRD §8 in `docs/glossary.md` and use it consistently in code names.
- [ ] **P0.4** Define coding conventions: Python (ruff + black + mypy), TypeScript (ESLint + Prettier, strict mode), commit message format, branch strategy (trunk-based or GitHub-flow), PR template with a Definition-of-Done checklist from §35.
- [ ] **P0.5** Create the work breakdown: convert every task in this file into tracked issues with labels `phase-N`, `P0/P1`, `backend/frontend`.
- [ ] **P0.6** Define the error model (used everywhere): every error response is `{ "error": { "code": "STRING_CODE", "message": "human readable", "details": [...], "requestId": "..." } }`. Maintain an error-code registry covering PRD §25 (see Phase 14 task P14.9).
- [ ] **P0.7** Define the pagination contract: `?page=&pageSize=&sort=&q=` returning `{ items, total, page, pageSize }`.
- [ ] **P0.8** Define the time/date convention: all dates ISO-8601; times stored as `TIME` without timezone plus a cycle-level timezone setting; timestamps `timestamptz` in UTC.

**Exit criteria:** ADRs merged, backlog created, conventions documented.

---

# Phase 1 — Scaffolding and Infrastructure

**Goal:** A running skeleton for frontend, backend and database with CI. (PRD roadmap Phase 1 deliverable.)

### 1.1 Repository and tooling

- [ ] **P1.1** Create the repository and the directory layout above.
- [ ] **P1.2** Add `.gitignore`, `.editorconfig`, `.env.example` (never commit real secrets).
- [ ] **P1.3** Backend tooling: `pyproject.toml` with FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, Pydantic v2, psycopg, passlib/argon2 (or bcrypt), PyJWT, python-multipart, ReportLab, OpenPyXL, pytest, pytest-cov, httpx, ruff, black, mypy, slowapi (or equivalent rate limiter).
- [ ] **P1.4** Frontend tooling: Vite + React + TypeScript (strict), Tailwind CSS, React Router, TanStack Query, TanStack Table, React Flow, Recharts, Vitest, React Testing Library, MSW (API mocking), ESLint, Prettier.
- [ ] **P1.5** Pre-commit hooks for lint/format.

### 1.2 Backend skeleton

- [ ] **P1.6** `main.py` with app factory, CORS configured from settings (no wildcard in production), `/api/v1` router prefix, `/health` and `/ready` endpoints.
- [ ] **P1.7** `config/settings.py` using Pydantic Settings: DB URL, JWT secret, token lifetime, upload size limit, max CSV rows, rate-limit values, CORS origins, environment name. All from environment variables.
- [ ] **P1.8** `config/database.py`: engine, session factory, per-request session dependency, transaction helper.
- [ ] **P1.9** Structured logging (JSON), request-ID middleware (generate if absent, echo in response header and logs).
- [ ] **P1.10** Central exception handlers: validation errors, domain errors, authorization errors, unexpected errors (log full trace, return sanitized message with request ID; never expose stack traces, per §25).
- [ ] **P1.11** Enable OpenAPI/Swagger docs (disable or protect in production).

### 1.3 Database

- [ ] **P1.12** PostgreSQL via Docker Compose for local development. Use separate databases for dev and test.
- [ ] **P1.13** Initialise Alembic; verify `alembic upgrade head` and `downgrade` work against an empty DB.
- [ ] **P1.14** Naming conventions for constraints/indices configured in SQLAlchemy `MetaData` so migrations are deterministic.

### 1.4 Frontend skeleton

- [ ] **P1.15** App providers (QueryClient, Router, auth context placeholder), route table with placeholder pages for every page in PRD §16.3 (A–J).
- [ ] **P1.16** API client module (`services/api.ts`) with base URL from env, error normalisation matching the P0.6 error model, and typed request helpers.
- [ ] **P1.17** Tailwind configuration with design tokens (neutral palette, type scale, spacing) per PRD §16.1.

### 1.5 CI

- [ ] **P1.18** GitHub Actions (or equivalent): backend lint + type check + tests against a Postgres service; frontend lint + type check + tests + build; fail on coverage regressions in `algorithms/`.
- [ ] **P1.19** Dependency vulnerability scan step (pip-audit, npm audit) as non-blocking initially.

### 1.6 Local development

- [ ] **P1.20** `docker-compose.dev.yml`: postgres, backend (hot reload), frontend (Vite dev server).
- [ ] **P1.21** Root `README` with quick-start commands.

**Tests:** health endpoint test; DB connectivity test; frontend smoke render test.
**Exit criteria:** `docker compose up` brings up all three; CI is green on an empty feature; hitting `/health` and loading the frontend both work.

---

# Phase 2 — Data Model, Authentication, Authorization, Audit Foundation

**Goal:** Full relational schema (PRD §17), secure login, backend-enforced RBAC (FR-01, §7, §23).

### 2.1 Schema and migrations

- [ ] **P2.1** Implement SQLAlchemy models and an initial Alembic migration for all tables in PRD §17:
  `users`, `departments`, `academic_years`, `semesters`, `students`, `subjects`, `enrollments`, `scheduling_cycles`, `exams`, `time_slots`, `conflict_graph_snapshots`, `conflict_edges`, `schedule_runs`, `schedule_versions`, `exam_assignments`, `audit_logs`.
- [ ] **P2.2** Add supporting tables/columns the PRD implies but does not list:
  - `programs` (FR-02 requires programs as a managed entity).
  - `cycle_holidays`, `cycle_sessions` (or keep inside `configuration_json`; see P5.2).
  - `import_batches` (records each CSV import: type, file name, hash, counts, status, actor).
  - `subject_date_preferences` (preferred/restricted dates; or JSON column on exam).
  - `schedule_run_results` metadata for comparison (or a JSON column on `schedule_runs`).
  - `users.failed_login_count`, `users.locked_until` for brute-force protection.
- [ ] **P2.3** Constraints (PRD §17 notes):
  - `users.email` unique; `students.student_number` unique; `subjects.subject_code` unique within the applicable scope (decision: unique per department + academic year, or globally; record in ADR).
  - `enrollments` unique `(student_id, subject_id, cycle_id)` for active status.
  - `exams` unique `(scheduling_cycle_id, subject_id)`.
  - `exam_assignments` unique `(schedule_version_id, exam_id)` — prevents duplicate assignments (§12 hard constraint 7).
  - `conflict_edges` unique on normalised pair with `CHECK (exam_id_a < exam_id_b)` — enforces no self-loops and no duplicate/mirror edges.
  - `time_slots` unique `(scheduling_cycle_id, date, start_time)`.
  - `schedule_versions` unique `(scheduling_cycle_id, version_number)`.
  - Check constraints: end_date >= start_date, duration > 0, valid enum values for status/role.
- [ ] **P2.4** Indexes: foreign keys, `enrollments(subject_id)`, `enrollments(student_id)`, `conflict_edges(graph_snapshot_id)`, `exam_assignments(schedule_version_id)`, `audit_logs(entity_type, entity_id)`, `audit_logs(timestamp)`.
- [ ] **P2.5** Soft-delete/archive semantics: use `status` fields (`active`/`archived`) rather than physical delete for students, subjects, cycles (FR-02, FR-03). Hard delete only where safe.
- [ ] **P2.6** Immutability rule: a `schedule_versions` row with status `Published` must reject updates to its assignments. Enforce in the service layer and with a DB trigger or guarded repository (defence in depth).

### 2.2 Authentication (FR-01)

- [ ] **P2.7** Password hashing with Argon2id (or bcrypt with a strong cost factor). Never log or return hashes.
- [ ] **P2.8** `POST /auth/login`: validate credentials, check `status == active`, return a token (or set an httpOnly, Secure, SameSite cookie per ADR-001). Use constant-time comparison and generic error messages ("invalid credentials").
- [ ] **P2.9** `POST /auth/logout`: invalidate the session/token (token denylist or short-lived tokens plus refresh rotation).
- [ ] **P2.10** `GET /auth/me`: returns user id, name, role, department scope.
- [ ] **P2.11** Brute-force protection: rate limit per IP and per account; temporary lock after N failures; audit failed logins.
- [ ] **P2.12** CSRF protection if cookie-based auth is used.
- [ ] **P2.13** Seed command to create the first Admin user from environment variables (no default password in code).

### 2.3 Authorization (FR-01, §7)

- [ ] **P2.14** Roles enum: `admin`, `coordinator`, `faculty`, `student`. (System Administrator persona maps to `admin` plus deployment-level access; document this.)
- [ ] **P2.15** Dependency `require_role(...)` and a permission matrix module encoding the table in PRD §7 as data (capability → roles → scope rule). Every endpoint declares its required capability.
- [ ] **P2.16** Department scoping helper: filters queries by `user.department_id` for coordinator/faculty. Applied in repositories, not only in handlers.
- [ ] **P2.17** Student self-access guard: a student may only read their own record/timetable (match `student.user_id`). Add `students.user_id` link (nullable FK) for this.
- [ ] **P2.18** Access-denied handling: 401 for unauthenticated, 403 for forbidden, consistent error body, audit entry for denied admin operations.
- [ ] **P2.19** User management (admin only): create, update role/department, activate/deactivate, reset password. `GET/POST/PATCH /users`.

### 2.4 Audit foundation (FR-21)

- [ ] **P2.20** `audit_service.record(actor, action, entity_type, entity_id, before, after, request_meta)` — called from services, not handlers, so it can't be skipped.
- [ ] **P2.21** Redaction utility: strip passwords, tokens, and unnecessary personal data from before/after JSON (§FR-21 "avoid storing sensitive data").
- [ ] **P2.22** Audit action catalogue (enum): `LOGIN`, `LOGOUT`, `LOGIN_FAILED`, `IMPORT_*`, `SUBJECT_*`, `ENROLLMENT_*`, `GRAPH_BUILD`, `SCHEDULE_RUN`, `SCHEDULE_EDIT`, `EXAM_LOCK`, `EXAM_UNLOCK`, `SCHEDULE_SAVE`, `SCHEDULE_VALIDATE`, `SCHEDULE_PUBLISH`, `EXPORT`, `ADMIN_OP_FAILED`.

**Tests:**
- Migration up/down.
- Constraint tests (duplicate enrollment, self-edge insert, duplicate assignment all rejected by DB).
- Auth: valid login, wrong password, inactive account, lockout, token expiry, logout invalidation.
- Authorization: parametrised test hitting **every** protected endpoint with each role and with no credentials, asserting the PRD §7 matrix (FR-01 acceptance: "backend authorization is tested independently of frontend visibility").

**Exit criteria:** Admin can log in; role matrix enforced by tests; schema migrated; audit service usable.

---

# Phase 3 — Academic Data Management

**Goal:** CRUD and query features for academic structure, subjects, students, enrollments (FR-02, FR-03, FR-04).

### 3.1 Academic structure (FR-02)

- [ ] **P3.1** CRUD + archive + search/filter for: academic years, semesters, departments, programs. Validate date ranges and uniqueness.
- [ ] **P3.2** Seed reference data for development (a couple of departments, one academic year).

### 3.2 Subjects (FR-03)

- [ ] **P3.3** Schemas with validation: code format (regex, length), name, department, program, semester (range), credits (optional, >= 0), duration minutes (positive, within allowed range), exam type enum, preferred dates, restricted dates (no overlap between preferred and restricted), priority, active status.
- [ ] **P3.4** Endpoints: `GET /subjects` (paginated, search by code/name, filter by department/program/semester/status), `POST`, `GET /{id}`, `PATCH`, `DELETE` (archive; refuse hard delete when referenced by exams/enrollments).
- [ ] **P3.5** Derived fields: **enrollment count computed by query**, never accepted from input (FR-03).
- [ ] **P3.6** `GET /subjects/{id}/students` (staff only; paginated).
- [ ] **P3.7** Subject detail includes conflict degree and scheduling status — populated from the latest graph snapshot / schedule version when available (wire these after Phases 6 and 8; stub as null now).
- [ ] **P3.8** Department scoping for coordinators.

### 3.3 Students (FR-04)

- [ ] **P3.9** CRUD with validation: unique `student_number` (stable ID, immutable after creation), name, department, program, semester/year, optional email format, status.
- [ ] **P3.10** `GET /students` search/filter/pagination; `GET /students/{id}/subjects`.
- [ ] **P3.11** Archive instead of delete; archived students excluded from graph building (decision: only `active` students and `active` enrollments contribute to conflicts).

### 3.4 Enrollments (FR-04)

- [ ] **P3.12** `POST /enrollments` (student + subject + cycle): reject unknown references, reject duplicates with a clear message, reject enrolling into an archived subject.
- [ ] **P3.13** `DELETE /enrollments/{id}` (set status `withdrawn` to preserve history, or delete; follow ADR-003).
- [ ] **P3.14** `GET /enrollments` with filters (student, subject, cycle, status), paginated.
- [ ] **P3.15** `GET /enrollments/validate`: reports duplicate records, orphan references, students with zero enrollments, subjects with zero enrollments, cycles with no exams.
- [ ] **P3.16** **Stale-data signalling:** any create/update/delete of an enrollment, subject activation, or student status that affects a cycle marks that cycle's current graph snapshot and any candidate schedule as `stale` (set a `data_version` counter on the cycle, bumped by these operations; snapshots store the `enrollment_snapshot_hash`). Implemented once in a shared service hook, not per endpoint.
- [ ] **P3.17** Audit entries for all subject and enrollment changes with before/after values.

**Tests:** CRUD happy/error paths; uniqueness; archive behaviour; derived enrollment count correctness; department scoping; stale flag set on enrollment change; audit entries written.
**Exit criteria:** Data management API complete and documented in OpenAPI; scoped permissions verified.

---

# Phase 4 — CSV Import and Validation

**Goal:** Safe, transparent, transactional import of students, subjects, enrollments (FR-05).

### Tasks

- [ ] **P4.1** Upload endpoints: `POST /students/import`, `POST /subjects/import`, `POST /enrollments/import`, each supporting `?mode=preview` (validate only) and `?mode=commit`. Alternative: two-step flow with an `import_batch` id returned from preview and confirmed with `POST /imports/{batchId}/confirm` (preferred: it enforces PRD step 8 "confirm import" and avoids re-uploading).
- [ ] **P4.2** File safety (PRD import rules, §23):
  - Enforce max file size (config) at the reverse proxy and in the app (stream and abort when exceeded).
  - Accept only `.csv` / `text/csv`; sniff content, don't trust the extension.
  - Enforce UTF-8 (handle BOM; reject undecodable bytes with a clear message).
  - Enforce max row count.
  - Never write uploads to a path derived from the client filename; process in memory or in a temp dir with a random name; delete after processing.
  - Neutralise spreadsheet formula injection on any value later re-exported (prefix `'` for cells starting with `=`, `+`, `-`, `@`).
- [ ] **P4.3** Parsing: use the Python `csv` module (or Pandas with strict dtype=str) with header normalisation (trim, lowercase, aliases documented). Reject unknown or missing required columns listing exactly which are missing.
- [ ] **P4.4** Row-level validation per type:
  - **Students:** `student_id` (format, unique in file and DB), `student_name` (non-empty, length), `department` (exists), `semester` (integer in range). Optional `program`, `email`.
  - **Subjects:** `subject_code` (format, unique), `subject_name`, `department` (exists), `semester`, `duration_minutes` (integer, in allowed range). Optional columns accepted.
  - **Enrollments:** `student_id` and `subject_code` must exist (in DB or in the same import batch if imported together), no duplicate pairs in file, no pair already enrolled.
- [ ] **P4.5** Error report structure: for each problem return `{ row, field, value, errorCode, message, suggestion }` ("Row 14, field semester: 'five' is not an integer. Use a number such as 5."). Never silently skip a row (PRD import rule 1).
- [ ] **P4.6** Preview summary: total rows, valid rows, invalid rows, duplicates, unknown references, new vs update counts, and a sample of the first N valid rows. Provide a downloadable error CSV.
- [ ] **P4.7** Commit semantics: all-or-nothing in a single DB transaction by default (PRD §24: "failures should not leave partial inconsistent records"). Optional "import valid rows only" mode must be explicit, confirmed by the user, and recorded in the audit log with counts of skipped rows.
- [ ] **P4.8** Upsert policy for existing records (students/subjects): decide per ADR — default is *reject duplicates* and report them; an explicit "update existing" flag may be added later.
- [ ] **P4.9** Idempotency: store file hash on `import_batches`; warn when the same file was already imported.
- [ ] **P4.10** After a successful commit: bump the cycle `data_version` / mark graph and schedules stale (FR-05 step 10), and return which cycles became stale.
- [ ] **P4.11** Cancellation and re-upload: preview batches expire (e.g., 1 hour) and can be discarded; re-upload creates a new batch.
- [ ] **P4.12** Order dependency: enforce or guide import order Subjects → Students → Enrollments; enrollments import reports a friendly message if prerequisites are empty.
- [ ] **P4.13** Efficient bulk insert (batch inserts, preloaded lookup dictionaries for departments/students/subjects to avoid N+1 queries).
- [ ] **P4.14** Audit: `IMPORT_PREVIEW`, `IMPORT_COMMIT`, `IMPORT_CANCEL`, `IMPORT_FAILED` with counts (not row contents).
- [ ] **P4.15** Publish the three example CSVs from PRD §FR-05 as fixtures and as downloadable templates (`GET /imports/templates/{type}`).

**Tests (PRD §26.1):** valid CSV; missing columns; extra columns; empty values; invalid types; duplicate rows; unknown IDs; invalid enrollment; oversize file; too many rows; non-UTF-8; BOM file; UTF-8 non-ASCII names; CSV with formula-like values; transaction rollback on mid-batch DB failure; commit marks cycle stale.
**Exit criteria:** All three import types work through preview → confirm; zero silently accepted invalid rows (success metric); rollback verified.

---

# Phase 5 — Scheduling Cycles and Slot Generation

**Goal:** Configure an exam period and compute real time slots from the calendar (FR-06, FR-11 slot part, §13.1–13.2).

### 5.1 Cycle management

- [ ] **P5.1** Endpoints: `GET/POST /cycles`, `GET/PATCH/DELETE(archive) /cycles/{id}`. Status machine: `Draft → Generated → Reviewed → Published → Archived`; define legal transitions in one place and reject others. Editing configuration after `Generated` marks the schedule stale and requires regeneration.
- [ ] **P5.2** `configuration_json` schema (validated by a Pydantic model, versioned with a `schemaVersion`):
  - `startDate`, `endDate`, `timezone`
  - `examDaysOfWeek[]`
  - `holidays[]` (dates, optional labels)
  - `sessions[]`: `{ label, startTime, endTime, enabled }` (e.g., Morning 09:00–12:00, Afternoon 14:00–17:00)
  - `breaks[]` (optional)
  - `maxExamsPerSession`, `maxExamsPerDay` (optional)
  - `allowedDurations[]`, `defaultDurationMinutes`
  - `preferredTimeSlots[]` (optional)
  - `specialRestrictions[]` (e.g., excluded dates, disabled sessions on certain dates)
  - `softConstraintWeights{}` (defaults from PRD §14.3)
  - `scope`: semesters/programs/departments included
- [ ] **P5.3** Validation rules: `endDate >= startDate`; at least one exam weekday; sessions must not overlap each other or breaks; session end > start; default duration is in allowed durations; holidays outside the range produce a warning not an error; return all problems at once.
- [ ] **P5.4** Scope selection: choose which subjects participate (by semester/program/department). Creating/refreshing the cycle's `exams` table: one `Exam` per in-scope active subject with `duration_minutes` defaulting to the subject's default or the cycle default. Endpoint: `POST /cycles/{id}/exams/sync` (adds new, flags removed, never deletes an exam that has assignments without confirmation).
- [ ] **P5.5** Per-exam overrides: duration, preferred dates, restricted dates, priority (stored on `exams`).

### 5.2 Slot generation (FR-11, §13)

- [ ] **P5.6** Implement `slot_service.generate_slots(config)` as a **pure function**: iterate each calendar date from start to end; skip dates not in allowed weekdays; skip holidays and excluded dates; for each enabled session create a slot with date, start, end, label, duration, enabled flag, optional capacity.
- [ ] **P5.7** Apply per-date special restrictions (disabled sessions on specific dates produce slots with `enabled = false` rather than missing, so the UI can show them).
- [ ] **P5.8** Deterministic slot ordering: by date, then session start time; assign a stable `slot_index` used later for color→slot mapping and adjacency calculations (consecutive sessions, same day).
- [ ] **P5.9** `POST /cycles/{id}/slots/generate`: regenerate slots. If assignments exist, refuse (or require `force=true` plus confirmation) and list impacted exams; preserve slot IDs where date/time are unchanged so existing assignments and locks survive config edits that don't affect them.
- [ ] **P5.10** `GET /cycles/{id}/slots` with filters (date range, enabled).
- [ ] **P5.11** Capacity summary endpoint: total slots, enabled slots, slots by duration bucket, and a quick **feasibility pre-check** — e.g. "chromatic lower bound": number of enabled slots must be >= size of the largest clique found cheaply (max degree + 1 is an upper bound; a greedy clique lower bound is cheap). Surface as a warning, not a promise (algorithms can't guarantee optimality; PRD §12).
- [ ] **P5.12** Duration compatibility helper: `fits(exam_duration, slot_duration)` implementing `ExamDuration ≤ SlotDuration` (§13.4). Report incompatible exams (exams longer than every enabled slot) at slot-generation time so failures are caught early.

**Tests:** slot generation for the PRD example (10–20 June, Mon–Sat, 2 sessions, Sundays excluded, holidays); holiday exclusion; weekday filtering; invalid ranges; overlapping sessions rejected; deterministic ordering; slot IDs stable across no-op regeneration; status-transition table; feasibility warnings; exam duration longer than any slot flagged.
**Exit criteria:** Admin can create a cycle, sync exams, generate slots, and see correct slot list and capacity summary.

---

# Phase 6 — Conflict Graph Engine

**Goal:** Build, validate, version, store and export the conflict graph exactly as specified in PRD §11 (FR-07).

### 6.1 Pure graph module (no DB access)

- [ ] **P6.1** Define the graph type in `algorithms/types.py`: vertex IDs (strings), `adjacency: dict[str, set[str]]`, `edge_weights: dict[tuple[str,str], int]` keyed by sorted pair, plus vertex metadata passed separately.
- [ ] **P6.2** Implement `build_conflict_graph(exam_ids, enrollments)`:
  1. Build `student_id → set(exam_id)` from active enrollments of in-scope exams (PRD §11.5 steps 1–2).
  2. For each student's exam set, generate pairwise combinations (normalised so `a < b`), incrementing the shared-student count for that pair (steps 3–4). Using a dict of pair → count deduplicates edges automatically and yields edge weights `w(u,v)` for free.
  3. Create adjacency sets symmetrically (step 5).
  4. Include every exam as a vertex, including isolated ones.
  - Complexity note: cost is Σ k(k−1)/2 over students (PRD §11.5). Avoid scanning all students per exam pair. Process students in streaming fashion for large data.
  - Skip students with fewer than two exams quickly.
- [ ] **P6.3** Rules enforced at construction: no self-loops, no duplicates, undirected symmetry, one vertex per exam.
- [ ] **P6.4** **Graph validator** (`validate_graph`) independent of the builder (PRD §11.6): each exam exactly one vertex; no self-edge; no duplicate edge; adjacency symmetry; every edge corresponds to ≥1 shared student (recomputed directly from enrollments by a different code path); no shared-enrollment pair missing an edge; all vertex IDs resolve to valid exams. Returns a structured report, never raises on bad data.
- [ ] **P6.5** **Graph statistics** (`compute_stats`):
  - |V|, |E|
  - average, max, min degree; degree histogram
  - connected components count and largest component size (iterative BFS/DFS — no recursion, to avoid depth errors on 500+ nodes)
  - isolated vertices list/count
  - density `D = 2|E| / (|V|(|V|−1))`, and `0` when |V| < 2
  - top-N exams by degree
  - clique-based lower bound (greedy) for the chromatic number as optional context
- [ ] **P6.6** Hashing: compute `enrollment_snapshot_hash` = SHA-256 over a canonical sorted serialisation of (in-scope exam IDs, active enrollment pairs). Used for staleness detection (PRD §31 "changes invalidate graph").

### 6.2 Service, persistence and API

- [ ] **P6.7** `graph_service.build(cycle_id)`: load in-scope exams + active enrollments efficiently (one query each, no N+1), call the pure builder, run the validator (fail the build if validation fails), compute stats, persist.
- [ ] **P6.8** Persist a `conflict_graph_snapshots` row (version = previous + 1, counts, density, `enrollment_snapshot_hash`, `graph_data_json` containing adjacency and stats) and `conflict_edges` rows (bulk insert) with `shared_student_count`.
- [ ] **P6.9** No-op build: if the hash equals the latest snapshot's hash, return the existing snapshot (and say so) instead of creating a duplicate version, unless `force=true`.
- [ ] **P6.10** Staleness: `GET /cycles/{id}/graph` returns `isStale` by comparing the cycle's current enrollment hash/data_version with the snapshot's. Everything downstream (generation, publish) checks this and refuses or warns per policy (publishing a schedule built from a stale graph is blocked).
- [ ] **P6.11** Endpoints (PRD §18.6):
  - `POST /cycles/{id}/graph/build`
  - `GET /cycles/{id}/graph` (nodes, edges, stats; supports `?department=&semester=&minWeight=` filters for large graphs; **no student identities** in this response)
  - `GET /cycles/{id}/graph/stats`
  - `GET /cycles/{id}/graph/export?format=json|csv` (node list + edge list with weights; admin only; excludes student identities)
  - `GET /cycles/{id}/graph/edges/{edgeId}` or `.../edges?examA=&examB=` returning the **shared student list** — admin/authorized staff only, audited (FR-07 "explain conflicts… to authorized users", §23 privacy).
- [ ] **P6.12** Graph snapshot immutability: schedule runs reference a `graph_snapshot_id` and never mutate it.
- [ ] **P6.13** Populate the conflict-degree / scheduling-status fields stubbed in P3.7.
- [ ] **P6.14** Audit `GRAPH_BUILD` with counts and snapshot version.

**Tests (PRD §26.2):** empty enrollments; one subject; two subjects no shared student; two subjects one shared student; multiple shared students (weight > 1); 3+ exams, including a student taking k exams producing k(k−1)/2 edges; duplicate enrollment rows don't double-count; no self-loops; symmetric adjacency; degree and density exact on hand-computed fixtures; connected components on disconnected graphs; validator catches deliberately corrupted graphs (missing edge, extra edge, asymmetric adjacency, self-loop); hash stable across input ordering; hash changes after an enrollment change; large synthetic dataset (500 exams / thousands of students) completes within target; privacy: graph endpoint response contains no student identifiers.
**Exit criteria:** Graph matches test fixtures 100%; validator passes on all built graphs; snapshots versioned and stale detection working.

---

# Phase 7 — Coloring Algorithms

**Goal:** Three independently implemented, instrumented, deterministic algorithms plus an independent validator (FR-09, §12). Do not use NetworkX for the coloring itself.

### 7.1 Common contract

- [ ] **P7.1** Define input/output types:
  - Input: `adjacency`, optional `precolored: dict[vertex, color]`, optional `order` (for Greedy), `deterministic: bool = True`, optional `trace: bool`.
  - Output (`ColoringResult`): `colors: dict[vertex, int]`, `color_count`, `execution_time_ms`, `vertex_visits` (selections), `color_checks`, `valid`, `algorithm`, `algorithm_version`, `config`, optional `trace[]`, `graph_fingerprint`.
- [ ] **P7.2** Input guards: reject self-loops, asymmetric adjacency, unknown neighbor IDs, precolors that conflict with each other (return a typed error that lists the clashing locked pair — used by regeneration P9.x).
- [ ] **P7.3** Stable ordering helper: a single `stable_key(vertex)` (vertex id / subject code) used for all tie-breaks so results are reproducible (§12.4). No `set` iteration order dependence: always sort before iterating when determinism is on.
- [ ] **P7.4** Instrumentation: counters for vertex visits and color checks implemented via a light `Metrics` object passed in (so counting adds negligible overhead); wall-clock measured with `time.perf_counter()`, excluding I/O.
- [ ] **P7.5** Version constants: `ALGORITHM_VERSION = "1.0.0"` per algorithm, bumped when behaviour changes (recorded in `schedule_runs`).

### 7.2 Greedy (Algorithm A)

- [ ] **P7.6** Implement `greedy_color(adj, order, precolored=None)`: initialise all vertices uncolored; apply precolors first; for each vertex in `order` (skip precolored), collect the colors of colored neighbors into a set (`forbidden`), assign the smallest non-negative integer not in it.
- [ ] **P7.7** Default order if none given: stable ID order. Support alternative named orders for the UI: `by_id`, `by_degree_desc`, `as_given`. Validate that `order` is a permutation of the uncolored vertices.
- [ ] **P7.8** Document complexity: O(V + E) neighbor scan with set lookups, plus the smallest-missing-color search bounded by the max degree + 1.

### 7.3 Welsh–Powell (Algorithm B)

- [ ] **P7.9** Implement `welsh_powell(adj, precolored=None)`: order = vertices sorted by descending degree, ties broken by stable ID (use a stable sort with a composite key `(-degree, stable_key)`), then delegate to `greedy_color`. Keep it as a thin, separate module so its code and metrics are independently readable (PRD §20).
- [ ] **P7.10** Document complexity O(V log V + E).

### 7.4 DSATUR (Algorithm C — primary)

- [ ] **P7.11** Implement `dsatur(adj, precolored=None)`:
  - Maintain `neighbor_colors[v]: set[int]` (so saturation = `len(neighbor_colors[v])`).
  - Initialise saturation from precolored neighbors.
  - Loop while uncolored vertices remain: select the uncolored vertex maximising `(saturation, degree, -stable_rank)` (i.e. highest saturation, then highest degree, then stable ID), assign the smallest color not in `neighbor_colors[v]`, then add that color to each uncolored neighbor's set.
  - Basic version: linear scan selection → O(V² + E). Provide an optional heap-based variant (lazy-deletion priority queue with `(−sat, −deg, id)`) behind a flag; both must produce **identical** output under deterministic mode and be cross-tested against each other.
  - Count vertex selections and color checks.
- [ ] **P7.12** Educational trace (§FR-09 optional, §30.5): when `trace=true`, record per step: step number, chosen vertex, its degree, saturation, forbidden colors, assigned color, and which neighbor saturations changed. Cap trace size for large graphs.

### 7.5 Independent validator (§12.5)

- [ ] **P7.13** `validate_coloring(adj, colors)` in `validators.py`, written **without calling any algorithm code**: every vertex colored exactly once; every color is a non-negative int; for every edge (u,v), `color[u] != color[v]`; no vertices missing or extra. Returns `{valid, uncolored[], conflicts[(u,v,color)]}`.
- [ ] **P7.14** Every algorithm call path (service layer, comparison, regeneration, tests) runs the validator on the output and stores the result. A failed validation is a hard error (`INVALID_COLORING`), never a "warning".
- [ ] **P7.15** Metrics module (`metrics.py`): color count, color class sizes, largest/smallest class, imbalance (e.g., standard deviation and max/min ratio), `groups_by_color`.

### 7.6 Locked / precolored support (FR-16, §15.3)

- [ ] **P7.16** All three algorithms accept `precolored`; precolored vertices are never recolored; their colors count toward neighbors' forbidden sets (and toward DSATUR saturation from step 0). Validate precolors against each other first.
- [ ] **P7.17** Precolor feasibility rule: if two adjacent vertices are precolored with the same color, return `LOCKED_CONFLICT` naming both exams.

### 7.7 Benchmarking harness

- [ ] **P7.18** Script `scripts/benchmark_algorithms.py`: generate random graphs (Erdős–Rényi with several densities, plus structured: complete, bipartite, cycle, grid-like) at sizes 50/100/250/500/1000; record runtime and color counts per algorithm; output CSV for the project report (supports the "Design and Analysis of Algorithms" goal and the 500-exam < 5s target).
- [ ] **P7.19** Optional verification-only comparison against NetworkX's coloring (as a test oracle for validity, not as the implementation) — allowed by PRD §22.

**Tests (PRD §26.3):** empty graph; single vertex; no-edge graph (1 color); complete graph K_n (n colors); bipartite (≤2 colors for DSATUR; Greedy/WP may use more only with adversarial order — include a known crown-graph case demonstrating order sensitivity); triangle (3); path (2); even cycle (2); odd cycle (3); disconnected graph; self-loop rejection; asymmetric adjacency rejection; deterministic ties (run twice, equal output; shuffle input dict order, equal output); precolored vertices preserved and respected; contradictory precolors rejected; property-based tests (Hypothesis) over random graphs asserting `validate_coloring` is true for all algorithms and `color_count ≤ max_degree + 1`; DSATUR basic vs heap variant equality; validator catches hand-corrupted colorings; counters non-zero and monotonic; trace content correct on a small worked example.
**Exit criteria:** ≥95% line coverage (target 100% branch on `algorithms/`); all property tests pass; benchmark harness runs; module has zero imports from web/DB layers.

---

# Phase 8 — Scheduling Engine (Mapping, Constraints, Generation, Comparison)

**Goal:** Turn color classes into a real timetable and independently validate it (FR-09 service side, FR-10, FR-11, FR-12, FR-13, §13, §14). This phase implements the central architectural rule: coloring produces candidates; a separate layer decides whether they're a valid timetable.

### 8.1 Color-to-slot mapping (§13.3)

- [ ] **P8.1** Define `map_colors_to_slots(color_classes, slots, exams, graph, locked, config)` returning `{color → slot_id}` or an infeasibility report. A color class maps to **exactly one** slot (ADR-004), so exams in one class can never be split across slots.
- [ ] **P8.2** Eligible-slot computation per color class: only enabled slots; slots not on restricted dates for any exam in the class; slot duration ≥ the longest exam duration in the class; slot capacity/max-exams-per-session (if configured) ≥ class size (or split strategy, see P8.5).
- [ ] **P8.3** Assignment strategy (two stages):
  - **Feasibility stage:** bipartite matching between color classes and eligible slots (Hopcroft–Karp or simple augmenting paths) so that a valid one-to-one mapping is found whenever one exists. A naive "first color → first slot" can fail even when feasible because of duration/date restrictions.
  - **Quality stage:** among feasible mappings, order/choose slots to reduce soft-constraint penalty (e.g., place large classes in early sessions, spread classes that share many students across different days via the conflict weights between classes, honour preferred dates). Start simple (ordered assignment honoring preferences) and keep local-improvement as P8.14.
- [ ] **P8.4** Locked-exam handling (ADR-005): before coloring, group locked exams by their locked slot; assign each distinct locked slot a reserved color id; pass `precolored` to the algorithm; after coloring, map reserved colors to their locked slots and remaining colors to remaining slots via P8.3.
- [ ] **P8.5** Over-capacity classes (class size > `maxExamsPerSession`): per MVP, report as infeasible with a clear message **or** split the class into multiple slots on the same day, since members of a class are mutually non-conflicting this is always safe for student conflicts. Choose per ADR; if splitting is enabled, mark the split in output and run the full validator.
- [ ] **P8.6** Infeasibility reporting (§13.5): never silently drop an exam. Report `requiredSlots` vs `availableSlots`, the list of exams that could not be placed, duration groups that are incompatible, and recommendations (extend dates, add sessions, relax restrictions). Candidate remains marked `incomplete`.

### 8.2 Constraint engine (FR-12, §14.1–14.3)

- [ ] **P8.7** `validation_service.validate_schedule(exams, assignments, slots, graph_edges, locks, config)` — pure and independent of the coloring code. Hard checks, each returning detailed violations:
  1. **Conflict check:** for every edge (A,B), `slot(A) != slot(B)`. Computed from the enrollment data directly (not only from the stored graph) so a bad graph can't hide a clash — recompute per-student slot collisions: no student has two exams in one slot. Also check *overlapping time ranges* across different slots (if slots could ever overlap).
  2. **Completeness:** every in-scope exam has exactly one assignment; none missing.
  3. **No duplicates:** no exam with multiple assignments.
  4. **Duration fit:** `exam.duration ≤ slot.duration`.
  5. **Excluded dates / non-exam days / holidays.**
  6. **Disabled sessions/slots.**
  7. **Locked exams preserved:** assignment equals locked slot.
  8. **Exam-level restricted dates** respected.
  9. **Capacity** constraints if configured.
  10. **Valid references:** slot belongs to the cycle; exam belongs to the cycle.
- [ ] **P8.8** Validation report structure: `{ valid, hardViolations[{type, examIds, slotId, sharedStudents?, message}], softPenaltyTotal, softBreakdown[], warnings[] }`; violation messages are user-readable (§25).
- [ ] **P8.9** Soft-constraint scoring (`soft_constraint_service`), weights from cycle config (defaults PRD §14.3: two exams in a day 10, consecutive sessions 5, session load over target 3, preferred date missed 2, moved unlocked exam 1):
  - Per student: exams per day > 1; consecutive sessions (via `slot_index` adjacency and same-day check); excessive exams on a day (> configured threshold).
  - Session/day load balance (deviation from mean or target).
  - Department / cohort spread.
  - Preferred dates missed; undesirable sessions.
  - Movement from a previous schedule (regeneration).
  - Compute efficiently using per-student slot lists (O(total enrollments)), not pairwise exam scans.
  - Output each violation with the student count and affected exams (student identities only in staff-authorised detail views).
- [ ] **P8.10** Make the distinction explicit in code and API: hard violations block save/publish; soft penalties are displayed (§12).

### 8.3 Generation workflow (FR-13)

- [ ] **P8.11** `schedule_service.generate(cycle_id, algorithm, options, actor)` follows PRD §13 steps 2–11:
  1. Precondition checks: cycle has exams, students, enrollments; slots exist; graph snapshot exists **and is not stale** (auto-rebuild if the user opted in, otherwise return `GRAPH_STALE`).
  2. Load locked assignments from the base schedule version if `preserveLockedExams`.
  3. Run the coloring algorithm (pure function) with precolors; run the coloring validator (P7.14).
  4. Map colors to slots (P8.1–8.6).
  5. Build assignments; run `validate_schedule` (P8.7).
  6. Compute soft score (P8.9).
  7. Optionally run local improvement (P8.14) if `optimizeSoftConstraints`.
  8. Final re-validation after any optimization.
  9. Persist a `schedule_run` (algorithm, version, config, execution_time_ms, colors_used, validity, soft score, status, graph snapshot id) — persist runs whether successful or not, so failures are inspectable.
- [ ] **P8.12** Outcomes enum (FR-13): `success`, `success_with_warnings`, `infeasible_insufficient_slots`, `invalid_data_or_algorithm_error`, `cancelled`, `failed`. Each has a stable code and an explanation payload.
- [ ] **P8.13** Cancellation/timeouts: wrap generation with a configurable timeout (MVP algorithms are fast, but set the pattern); the `cancelled` state is reserved for background-job mode (ADR-007). Expose `status` for polling even if synchronous in MVP.
- [ ] **P8.14** *(P1)* Optional local improvement: iterate over moves "swap two color classes' slots" and "move an unlocked class/exam to another valid slot", accept only if all hard constraints still pass (re-checked incrementally) and total penalty decreases; stop at iteration/time cap; never move locked exams; deterministic order.
- [ ] **P8.15** Endpoints (PRD §18.7):
  - `POST /cycles/{id}/schedule/generate` (body per PRD §19; response per PRD §19 plus infeasibility/validation details)
  - `GET /cycles/{id}/schedule/runs`
  - `GET /schedule-runs/{runId}`
  - `POST /schedule-runs/{runId}/validate` (re-run validation)
  - `POST /schedule-runs/{runId}/save` → creates a `ScheduleVersion` (status `Candidate`) with its `ExamAssignment`s (including `color_id`, `locked`, `manual_override=false`); refuses invalid or incomplete runs.
- [ ] **P8.16** Update cycle status to `Generated` when the first candidate is saved.
- [ ] **P8.17** Audit: `SCHEDULE_RUN`, `SCHEDULE_SAVE`, `SCHEDULE_VALIDATE`.

### 8.4 Algorithm comparison (FR-10)

- [ ] **P8.18** `POST /cycles/{id}/schedule/compare`: run Greedy, Welsh–Powell, DSATUR on the **same graph snapshot** (same `graph_snapshot_id`, same precolors) in one request; produce for each: slots/color classes used, runtime ms, validity, exams scheduled, unscheduled count, class sizes, largest/smallest, imbalance, graph size and density, plus real-calendar outcome (feasible? slots required vs available, soft score) since fewer colors does not always mean a feasible real timetable (PRD FR-10 requirement "real constraints may require more slots").
- [ ] **P8.19** Each compared result is stored as a saved `schedule_run` so it can be reviewed later and selected as the candidate (`POST /schedule-runs/{id}/save`).
- [ ] **P8.20** Comparison honesty: response includes a `notes` array stating results are heuristic, no algorithm is guaranteed optimal, and runtime for small graphs is noise-level. Repeat timing N times (configurable, default 5) and report median to reduce jitter.
- [ ] **P8.21** Optional: a `GET /cycles/{id}/schedule/compare-report` export (feeds FR-20 "Algorithm comparison report").

**Tests (PRD §26.4 partly):**
- Mapping: feasible case; infeasible by slot count; infeasible by duration (long exam, only short slots); matching finds a solution a naive greedy mapping would miss; locked exams mapped to their slots; over-capacity handling.
- Validator: each hard constraint has a failing fixture (clash, missing exam, duplicate, too-long exam, holiday slot, disabled slot, lock moved) and a passing fixture; validator independent of graph (tamper with stored graph and confirm validator still catches the clash).
- Soft scoring: hand-computed penalty on a small timetable.
- Generation end-to-end (import → graph → color → map → validate) for all three algorithms on the demo dataset; deterministic repeatability (identical output on re-run); stale-graph refusal; unscheduled exams = 0 on success; infeasible response lists required vs available slots.
- Comparison: all three results reference the same snapshot id; each validated; table fields complete.
- Run persistence even on failure.
**Exit criteria:** A timetable is generated automatically from imported data with zero student conflicts and zero unscheduled exams (success metrics §4.2); infeasibility reported instead of silently dropping exams; comparison API returns the PRD table.

---

# Phase 9 — Schedule Versions, Manual Editing, Locking, Regeneration (Backend)

**Goal:** Safe human control over generated schedules (FR-15, FR-16, FR-17, §15).

### 9.1 Versions

- [ ] **P9.1** `GET /cycles/{id}/schedules` (list versions with status, source run, created_by, validity summary); `GET /schedules/{id}` (full assignments + slots + exam info + lock/override flags + latest validation report).
- [ ] **P9.2** Version rules: `Candidate` and `Reviewed` versions are editable; `Published` and `Archived` are immutable. Any change to a published schedule requires **cloning to a new Candidate version** (`POST /schedules/{id}/clone`) — never edit history in place (FR-19).
- [ ] **P9.3** Versioning of edits: each saved manual edit either updates the candidate in place with an audit trail, or creates an incremental revision; choose in ADR. Minimum: audit before/after of the assignment, plus an `edit_history` list retrievable per schedule so "undo"/history (PRD §24 usability) is feasible.
- [ ] **P9.4** `POST /schedules/{id}/archive`.

### 9.2 Manual editing (FR-15, §15.1–15.2)

- [ ] **P9.5** `POST /schedules/{id}/assignments/{aid}/preview-move` (body: target `timeSlotId`) — dry run: runs all hard checks for the move without persisting, returns validity, violations, and soft-score delta. (PRD flow: select → preview → validate → confirm.)
- [ ] **P9.6** `PATCH /schedules/{id}/assignments/{aid}` (body: `timeSlotId`, optional `expectedVersion` for optimistic concurrency): re-runs validation server-side (never trusts the preview), persists only if valid, sets `manual_override = true`.
- [ ] **P9.7** Move validation (incremental, but equivalent to full validation): student-conflict check against exams already in the target slot (using enrollment overlap, returning **conflicting exam codes and shared-student counts**); duration fit; excluded date; disabled/non-existent slot; locked status of the moved exam; exam-restricted dates; capacity.
- [ ] **P9.8** Invalid-move response (§15.2): `{ reason, conflictingExams[{code, sharedStudentCount}], incompatibleSlot{...}, examLocked: bool }`; HTTP 409/422 with the standard error body; **nothing is persisted**.
- [ ] **P9.9** Swap operation (two exams swapping slots) as a convenience endpoint, validated atomically.
- [ ] **P9.10** Concurrency control: optimistic locking via an `updated_at`/`row_version` check so two admins don't overwrite each other; return `CONCURRENT_MODIFICATION`.
- [ ] **P9.11** After every successful edit: re-validate the whole schedule, store the latest report, update soft score, and set cycle/ schedule status back from `Reviewed` to `Candidate` if it changed.

### 9.3 Locking (FR-16, §15.3)

- [ ] **P9.12** `POST .../lock` and `POST .../unlock` (admin only). Lock requires the assignment to currently be valid; unlock is always allowed but audited (`EXAM_LOCK`, `EXAM_UNLOCK` with actor and before/after).
- [ ] **P9.13** Locked exams cannot be moved by `PATCH` (clear error `EXAM_LOCKED`) unless unlocked first.
- [ ] **P9.14** Bulk lock/unlock by filter (e.g., lock all exams on a given date) — optional convenience.
- [ ] **P9.15** Lock-set validation endpoint: `POST /schedules/{id}/locks/validate` checking that locked exams are mutually compatible (no two locked exams with shared students in the same slot) — also used internally before regeneration.

### 9.4 Regeneration and repair (FR-17)

- [ ] **P9.16** `POST /schedules/{id}/regenerate` with options: `mode = full | unlocked_only`, `algorithm`, `preserveLockedExams` (default true), `minimizeDisruption` (default true), `compareToPrevious` (default true).
- [ ] **P9.17** Regeneration algorithm (PRD §15.3 / §FR-16 steps 1–7):
  1. Load locked assignments.
  2. Validate locked set (P9.15); on failure return `LOCKED_CONFLICT` naming the pair.
  3. Treat locked exams as precolored (P8.4).
  4. Color the remaining vertices without altering locked colors.
  5. Map classes to slots; for `minimizeDisruption`, bias the mapping stage so unlocked exams stay in their previous slot whenever that is conflict-free (a color class whose members mostly sat in slot S prefers S — the `existing unlocked exam moved` penalty from §14.3 drives this).
  6. Validate the full result; confirm every lock preserved.
  7. If impossible, return an infeasibility report with: contradictory locks, number of free slots vs needed, suggestions (unlock X, extend dates, add sessions).
- [ ] **P9.18** Regeneration always produces a **new** Candidate version (never overwrites the source), so the user can compare and discard.
- [ ] **P9.19** **Change impact report** (`GET /schedules/{newId}/diff/{oldId}`): exams moved (with from→to), exams unchanged, slots added/removed (when slots were regenerated), hard-constraint status old vs new, soft-score change, locked exams preserved (count and list), reasons for any failure.
- [ ] **P9.20** Handling data changes: when the graph is stale because enrollments changed, regeneration first rebuilds the graph (with confirmation flag) and reports new exams (no assignment yet), removed exams, and affected edges. New exams get placed by the coloring step; removed exams drop out of the new version with a note in the impact report.
- [ ] **P9.21** Repair mode (optional P1): `POST /schedules/{id}/repair` places only unassigned or newly conflicting exams, leaving all others fixed.

**Tests (PRD §26.4):** valid move accepted; each invalid-move type rejected with correct reason and **no persistence** (verify DB unchanged); move of locked exam rejected; concurrency conflict; preview equals actual result; lock → regenerate preserves lock exactly (slot id equality); contradictory locks reported; lock that makes remaining schedule infeasible reported with suggestions; minimize-disruption keeps unchanged exams where possible (assert moved-count ≤ baseline); diff report counts correct; published schedule rejects every mutation (edit, lock, unlock, regenerate-in-place); clone creates editable candidate; audit entries for every edit/lock/unlock.
**Exit criteria:** Invalid changes impossible to persist; locks provably survive regeneration; every edit audited and re-validated.

---

# Phase 10 — Publishing, Student Timetable, Export, Reports, Audit API (Backend)

**Goal:** Complete the backend MVP pipeline through to students and exports (FR-18 to FR-22, §35).

### 10.1 Publishing (FR-19)

- [ ] **P10.1** `POST /schedules/{id}/publish` (admin only), implemented as a single DB transaction:
  1. Select candidate; ensure it is not stale relative to the latest graph/enrollment data (block with `SCHEDULE_STALE` and explain).
  2. Run **final validation** (full recompute from raw enrollments; never reuse the cached report).
  3. If any hard violation: refuse and return the report.
  4. Require explicit confirmation payload (`confirm: true`, echo of the validation report hash the admin reviewed — prevents publishing something that changed after review).
  5. Mark version `Published`, set `published_at`, make it immutable.
  6. Archive/supersede the previously published version but **retain** it (FR-19 step 7).
  7. Update cycle status to `Published`.
  8. Audit `SCHEDULE_PUBLISH`.
- [ ] **P10.2** Publishable definition check (PRD §35): all required exams assigned; all slots valid; hard constraints pass; locks preserved; independent validation reports zero student conflicts; admin confirmed.
- [ ] **P10.3** Only one published version per cycle at a time (partial unique index on `(cycle_id) WHERE status='Published'`).
- [ ] **P10.4** Unpublish/withdraw is **not** in MVP; superseding via a new published version is the supported path. Document in README.

### 10.2 Student and role-scoped timetable views (FR-18, FR-14 data side)

- [ ] **P10.5** `GET /students/{id}/timetable`: returns only the student's exams from the **published** schedule (date, start/end, subject code/name, duration, department/program context), sorted by date. Student role can only request their own id (403 otherwise). Empty-state: structured response `{ published: false }` when nothing is published.
- [ ] **P10.6** `GET /me/timetable` convenience endpoint for the logged-in student.
- [ ] **P10.7** Whole/department/program/semester/subject timetable queries: `GET /schedules/{id}/timetable?department=&program=&semester=&subjectId=&date=`; scope enforced by role (coordinator/faculty → their department; students cannot use it).
- [ ] **P10.8** Privacy: responses to students contain no other students' data; exam payloads for students exclude enrollment counts if policy says so (decision in ADR; PRD FR-18 requires no other students' PII — enrollment *count* is not PII but confirm).

### 10.3 Export (FR-20, §18.9)

- [ ] **P10.9** CSV exports: full timetable, department, semester/program, student, subject; conflict graph (nodes+edges); algorithm comparison. Include header block rows or metadata columns for cycle name, generation date, schedule version, and filters applied. Apply formula-injection escaping (P4.2).
- [ ] **P10.10** PDF exports (ReportLab): print-friendly layout, repeated header with cycle/version/date, page numbers, table or day-grid layout, accessible text (not colour-only status), correct page breaks for long timetables. Student PDF is a compact personal timetable.
- [ ] **P10.11** XLSX export (optional, OpenPyXL): one sheet per day or one sheet with filters; metadata sheet.
- [ ] **P10.12** Role-aware exports: coordinator/faculty limited to their department; students only their own (PRD §7 table); full export admin only. Enforced in the service, with tests.
- [ ] **P10.13** Export content correctness checks: all published exams present exactly once with correct date/time (success metric); unpublished schedules can be exported only by admins and are watermarked "DRAFT / NOT PUBLISHED".
- [ ] **P10.14** Stream large exports; set `Content-Disposition` filenames from sanitised server-side values; audit `EXPORT` (type, filters, actor).

### 10.4 Reports and analytics (FR-22)

- [ ] **P10.15** `GET /cycles/{id}/reports/summary`: exam count, student count, enrollment count, graph vertices/edges, conflict density, average/max degree, connected components, slot count, validation result.
- [ ] **P10.16** `GET /schedules/{id}/reports/distribution`: exam load per session, per day; student exam distribution (histogram of exams per student, max exams per day, consecutive-session counts); top conflict-degree exams.
- [ ] **P10.17** `GET /schedules/{id}/reports/changes`: schedule change report (from audit trail + diff).
- [ ] **P10.18** Algorithm report: pulls saved comparison runs (FR-22 "algorithm comparison").
- [ ] **P10.19** Role scoping and no-PII rule: aggregate numbers only unless staff-authorised drill-down.

### 10.5 Audit API (FR-21)

- [ ] **P10.20** `GET /audit-logs` (admin only): filters by actor, action, entity type/id, date range; paginated; redacted payloads; immutable (no update/delete endpoints; DB role has no UPDATE/DELETE on the table if feasible).
- [ ] **P10.21** Verify audit coverage with a test that enumerates the action catalogue from P2.22 and asserts each is emitted at least once in the integration suite.

**Tests (PRD §26.4):** publish happy path; publish refused for invalid/stale/incomplete schedule; publish requires admin; previous published version retained; one-published-per-cycle constraint; published immutability; student sees only own timetable; student blocked from others; empty-state when unpublished; coordinator department scoping on timetable and export; CSV/PDF/XLSX content matches DB (parse the generated files in tests); export includes metadata; formula-injection escaped; report numbers match hand-computed fixtures; audit entries for publish/export.
**Exit criteria:** Backend end-to-end: login → import → graph → generate → edit/lock → regenerate → publish → student view → export, all via API, with audit trail.

---

# Phase 11 — Frontend Foundation and Data-Management Pages

**Goal:** App shell, authentication, role-aware navigation and the data-entry screens (PRD §16, §21). Starts once the Phase 2–5 APIs are stable; use generated TypeScript types from OpenAPI to keep the contract type-safe.

### 11.1 Foundation

- [ ] **P11.1** Generate TS API types from the backend OpenAPI schema (`openapi-typescript`); wire into a typed fetch layer and TanStack Query hooks (`features/*/api.ts`). Regenerate in CI and fail on drift.
- [ ] **P11.2** Auth flow: login page, token/cookie handling per ADR-001, `useAuth` context, automatic redirect on 401, logout, "session expired" handling, protected-route wrapper.
- [ ] **P11.3** Role-aware navigation (PRD §16.2): staff navigation (Overview, Scheduling Cycles, Subjects, Students, Enrollments, Conflict Graph, Generate Schedule, Timetable, Algorithm Lab, Reports, Settings) vs student navigation (My Timetable, Academic Information, Downloads). Hide what a role cannot use — but backend remains the authority (§7).
- [ ] **P11.4** Design system primitives (PRD §16.1: restrained, information-dense, neutral, functional colour; avoid decorative gradients, oversized rounded panels, repetitive KPI tiles): `Button`, `Input`, `Select`, `Table` (TanStack Table with sorting, pagination, column filters), `Dialog`, `Toast`, `Tabs`, `Badge/StatusPill` (text + icon, never colour alone), `EmptyState`, `ErrorState`, `LoadingSkeleton`, `ConfirmDialog` (for destructive actions), `FileDropzone`, `FormField` with inline errors.
- [ ] **P11.5** Global error boundary and API-error presenter that renders the `{code, message, details, requestId}` model; show request ID for support.
- [ ] **P11.6** Accessibility baseline: semantic HTML, visible focus, keyboard operability for all controls, ARIA labels, sufficient contrast (WCAG AA), `prefers-reduced-motion` respected. Add `eslint-plugin-jsx-a11y` and axe checks in component tests.
- [ ] **P11.7** Stale-data banner component used across pages ("Enrollment data changed since the graph/schedule was generated — rebuild/regenerate").

### 11.2 Pages

- [ ] **P11.8** **Overview (A):** active cycle selector; compact metrics (exams, students, conflict edges, density, slot count, schedule status, last run, validation status); quick actions (import data, build graph, generate). Dense layout, not tile-heavy.
- [ ] **P11.9** **Scheduling Cycles (B):** list with status, create/edit form implementing every FR-06 field (dates, weekdays, holidays editor, session editor with start/end validation, breaks, max exams per session/day, allowed/default durations, preferred slots, restrictions, soft-constraint weights with explanations, scope selection); archive; open cycle; slot preview calendar and capacity summary with feasibility warnings.
- [ ] **P11.10** **Subjects (C):** paginated table, search by code/name, filters (department, program, semester, status), subject detail drawer (enrollment count, conflict degree, scheduling state, enrolled students list for authorised staff), create/edit form, archive, bulk import entry point.
- [ ] **P11.11** **Students and Enrollments (D):** student search and detail; enrollment list per student/subject; add/remove enrollment; validation and duplicate report view (`/enrollments/validate`).
- [ ] **P11.12** **Import wizard (shared, FR-05):** step 1 choose type and download template → step 2 upload (drag/drop, size/type hints) → step 3 preview (valid/invalid/duplicate counts, paginated error table with row/field/message/suggestion, download error CSV) → step 4 confirm or cancel → step 5 result summary + "cycles marked stale" notice. Supports corrected re-upload.
- [ ] **P11.13** **Admin screens:** user management (create, role, department, activate/deactivate), audit log viewer (filters, paginated, JSON diff view).
- [ ] **P11.14** Every page implements loading, empty, error and permission-denied states (Definition of Done §35).

**Tests (PRD §26.5):** navigation per role; form validation messages; import wizard error display (MSW-mocked preview responses); table filters/pagination; stale banner; permission-denied rendering; a11y (axe) on each page.
**Exit criteria:** Admin can complete cycle setup and all three imports from the UI; student login shows only the student navigation.

---

# Phase 12 — Frontend Scheduling Experience

**Goal:** Conflict graph visualisation, schedule generation, algorithm lab and timetable viewing (PRD §16.3 E–H, FR-08, FR-10, FR-13, FR-14).

### 12.1 Conflict Graph page (FR-08)

- [ ] **P12.1** React Flow integration: custom node component showing subject code (+ name on toggle), department/semester styling, size scaled by degree, slot/colour badge, lock icon; custom edge showing weight on hover.
- [ ] **P12.2** Layout: compute a force-directed layout (d3-force in a Web Worker) so the UI thread isn't blocked; cache positions; persist per-user positions in `localStorage`-equivalent app state (or the backend if multi-device is needed); **Reset layout** and **Fit to screen** buttons.
- [ ] **P12.3** Interactions: zoom/pan, drag nodes, search subject (focus + highlight), select node, highlight neighbors, highlight connected component, filter by department/semester, filter by colour/time slot, toggle labels, highlight high-degree nodes (threshold slider/top-N), node details panel (code, name, department, semester, enrollment count, degree, assigned slot, lock status), edge details panel (shared-student count; authorised "show shared students" action that calls the audited endpoint).
- [ ] **P12.4** Original vs coloured view toggle; legend mapping colours to **slot labels** (e.g., "Mon 10 Jun · Morning") rather than relying on colour alone (PRD risk table); add patterns/labels so the graph is readable without colour.
- [ ] **P12.5** Visual states: uncolored, colored, locked, selected, high-degree, conflict-highlighted, invalid placement (from validation report).
- [ ] **P12.6** Metrics side panel: |V|, |E|, average/max/min degree, degree histogram (Recharts), components, isolated count, density, top exams by degree.
- [ ] **P12.7** Performance for ~500 nodes: memoised node/edge components, `onlyRenderVisibleElements`, hide edges by minimum weight, collapse-by-component, progressive loading, edge de-emphasis when zoomed out; large-graph warning with auto-applied filters. Target: interactive at 500 nodes; measure with a profiling test dataset.
- [ ] **P12.8** Graph rebuild button with stale indicator and result summary; graph export (JSON/CSV) button.
- [ ] **P12.9** Privacy: no student names/IDs in node labels or tooltips (§23).

### 12.2 Generate Schedule page (FR-13, §16.3 F)

- [ ] **P12.10** Cycle selector; available-slots summary and feasibility warnings; algorithm selector (Greedy / Welsh–Powell / DSATUR default) with short plain-language descriptions and complexity notes; options: deterministic (default on), preserve locked exams, optimise soft constraints, Greedy order selector; display of locked-exam list.
- [ ] **P12.11** Pre-flight checklist component mirroring PRD §13 step 2: subjects present, students present, enrollments present, slots generated, graph fresh. Blocking items link to the fix.
- [ ] **P12.12** Generate button with progress/loading state; result panel: outcome type (success / success with warnings / infeasible / invalid / cancelled / failed) with explanation text, colours used, runtime, scheduled vs unscheduled counts, validity, hard-violation count, soft warnings and penalty breakdown; **infeasibility report** view (required vs available slots, offending duration groups, recommendations).
- [ ] **P12.13** Validation report viewer: grouped violations with links to affected exams on the timetable/graph.
- [ ] **P12.14** Save candidate action → navigates to the timetable of the created version. Optional educational **trace viewer** (step through DSATUR choice, degree, saturation, forbidden colours, chosen colour — FR-09 optional / §30.5).

### 12.3 Algorithm Lab (FR-10, §16.3 G)

- [ ] **P12.15** Run one or all algorithms on the same snapshot; side-by-side results table with exactly the PRD columns (Slots Used, Runtime, Valid, Exams Scheduled) plus unscheduled count, class sizes, largest/smallest, imbalance, graph size/density, real-calendar feasibility and soft score.
- [ ] **P12.16** Charts (Recharts): colour-class size distribution per algorithm; colours used and runtime bars. Heuristic honesty note displayed (no optimality claim; fewer colours ≠ always fewer real slots).
- [ ] **P12.17** Select a result as the candidate and save; saved-runs history list for later review; compare current vs earlier runs; export comparison report.
- [ ] **P12.18** Optional benchmark view for the DAA demonstration (loads precomputed benchmark CSV or runs synthetic graphs of selectable size/density through a dev-only endpoint).

### 12.4 Timetable page (FR-14, §16.3 H — read-only parts)

- [ ] **P12.19** Calendar/grid: date columns × session rows; exam cards with subject code and name, department/semester, duration, enrollment count, status, conflict indicator, lock indicator; day navigation for narrow screens; version switcher and status label (Candidate/Reviewed/Published).
- [ ] **P12.20** Views: whole university, department, program, semester, subject, individual student (staff lookup by student ID, audited).
- [ ] **P12.21** Search and filters (department, program, semester, date range, session); validation indicators; empty slots visible but muted.
- [ ] **P12.22** Print-friendly CSS (`@media print`): clean grid, no controls, headers with cycle/version/date, page-break rules; readable in greyscale; indicators use text/icons in addition to colour.
- [ ] **P12.23** Keyboard navigation through cells/cards; screen-reader labels ("CS301 Data Structures, Monday 10 June, Morning session, 180 minutes, locked").

**Tests (PRD §26.5):** algorithm selection and options; generate workflow including each outcome state (MSW); infeasible report rendering; graph: node select highlights neighbours, filters change visible set, search focuses node, original/coloured toggle, no student PII in DOM; lab table rendering and honesty note; timetable filters and view switching; print stylesheet snapshot; a11y checks; performance smoke test with 500-node fixture (render time budget).
**Exit criteria:** From the UI an admin can build the graph, inspect it, run each algorithm, compare them, save a candidate and view it on a calendar.

---

# Phase 13 — Frontend Editing, Locking, Publishing, Student View, Reports

**Goal:** Finish the user-facing MVP (PRD §16.3 H–J, FR-15 to FR-22).

### 13.1 Editing and locking

- [ ] **P13.1** **Edit mode** toggle on the timetable (admin only, candidate/reviewed versions only; disabled with explanation on published versions).
- [ ] **P13.2** Move flow: select exam (or drag-and-drop card — optional P1) → target slot picker → **preview** (calls preview-move) showing validity, soft-score delta and any problems → confirm → save → optimistic UI update with rollback on server rejection.
- [ ] **P13.3** Drag-and-drop: show valid vs invalid drop targets while dragging (call a lightweight "valid slots for exam" endpoint `GET /schedules/{id}/assignments/{aid}/valid-slots`, which is an additional endpoint to add in Phase 9 for this purpose); keyboard-accessible alternative (select + "Move to…" menu).
- [ ] **P13.4** Invalid-move feedback panel (§15.2): reason, conflicting exams with shared-student counts, incompatible slot details, locked indicator. Never persist invalid moves (server-enforced; UI only presents).
- [ ] **P13.5** Lock/unlock controls on cards and in an inspector panel, with lock list; confirmation on unlock; lock icon + text label shown in graph, calendar and tables.
- [ ] **P13.6** Concurrency handling: if the server returns `CONCURRENT_MODIFICATION`, refetch and show a "schedule changed by another user" notice.
- [ ] **P13.7** Edit history panel and undo of last edit (re-applies previous assignment through the normal validated PATCH).
- [ ] **P13.8** Regenerate dialog: mode (full / unlocked only), algorithm, preserve locks (default on), minimise disruption; result opens a **change impact report** page (moved/unchanged exams, slots added/removed, hard status, soft-score change, locks preserved, failure reasons with unlock suggestions). New candidate is shown side-by-side with the previous version; user can discard or promote it.

### 13.2 Review and publish

- [ ] **P13.9** Validation action ("Run full validation") with report viewer; mark version `Reviewed` (admin action; allowed only when valid).
- [ ] **P13.10** Publish wizard (FR-19): select candidate → run final validation → show report (must be zero hard violations; soft warnings listed) → explicit confirmation with the cycle name/version typed or checkbox → publish → success state with link to the student view and exports. Blocks on stale data with a clear explanation.
- [ ] **P13.11** Published-version banner and "Create new version from this" (clone) action; version history list showing which version is currently published.

### 13.3 Student experience (FR-18)

- [ ] **P13.12** **My Timetable:** upcoming exams (date, start/end, subject code/name, duration, department/program), sort by date, list and calendar views, print and download (PDF), empty state ("No timetable has been published yet").
- [ ] **P13.13** **Academic Information:** the student's own subjects only. **Downloads:** personal PDF/CSV.
- [ ] **P13.14** Verify no other student's data appears anywhere in student-facing screens or responses (network-level test).

### 13.4 Reports and exports

- [ ] **P13.15** **Reports page (J):** schedule summary, graph statistics, algorithm report, student workload (histogram of exams per student), exam distribution per day/session charts (Recharts), change history, export controls.
- [ ] **P13.16** Export menu on timetable/reports: PDF, CSV, XLSX (if enabled), with scope selectors (whole, department, semester/program, subject, student) respecting role limits; show progress and handle failures with retry.
- [ ] **P13.17** Coordinator experience: department-scoped read-only views, "Request change" form (stores a change request record — add a minimal `change_requests` table/endpoint: coordinator submits text + affected exam; admin sees a queue). Faculty: read-only department timetable.
- [ ] **P13.18** Settings page: profile, password change, (admin) system configuration display, soft-constraint weight presets.

**Tests (PRD §26.5):** edit flow with valid/invalid moves; invalid move shows reasons and nothing changes; locked exam cannot be dragged; regeneration preserves lock in UI; publish wizard blocks on violations; student view permissions and empty state; export buttons call correct endpoints; coordinator cannot see other departments; print layout; a11y.
**Exit criteria:** Entire PRD §33 demo flow can be executed in the UI without touching the API directly.

---

# Phase 14 — Security, Privacy, Reliability and Performance Hardening

**Goal:** Meet PRD §23, §24, §25, and success-metric §4.2 targets.

### 14.1 Security (§23)

- [ ] **P14.1** Review every endpoint against the permission matrix (automated: introspect routes, assert each has a declared capability — fail CI if a route lacks one).
- [ ] **P14.2** HTTPS enforcement and HSTS in production; secure cookie flags; security headers (CSP, X-Content-Type-Options, X-Frame-Options/frame-ancestors, Referrer-Policy) via reverse proxy and/or middleware.
- [ ] **P14.3** Rate limiting: auth endpoints (strict), import/upload endpoints, export endpoints, generation endpoints (to prevent resource exhaustion), shared-student-detail endpoints (to deter scraping).
- [ ] **P14.4** Input validation audit: Pydantic constraints on every field (lengths, ranges, enums, regex), pagination caps, sort-field allowlists, no raw SQL (verify with a grep/lint rule); upload hardening re-checked.
- [ ] **P14.5** Secrets management: all secrets via environment/secret store; rotate JWT secret procedure documented; no secrets in logs, images, or repo (secret-scanning in CI).
- [ ] **P14.6** Dependency and container scanning (pip-audit, npm audit, Trivy); non-root container user; minimal base images; pinned versions.
- [ ] **P14.7** Least-privilege DB roles: app role without DDL; separate migration role; `audit_logs` insert/select only if feasible.
- [ ] **P14.8** Security tests: broken access control (horizontal: student A → student B; vertical: student → admin endpoints; department A → department B), JWT tampering/expiry, CSRF, mass-assignment (extra fields ignored/rejected), IDOR on UUIDs, verbose error leakage, file-upload abuse (zip bombs, huge lines, binary), formula injection in exports.
- [ ] **P14.9** Error-code registry complete for every case in PRD §25: invalid CSV, duplicate student IDs, duplicate subject codes, unknown student/subject references, empty enrollment data, no exams in cycle, invalid dates, end before start, no available slots, slot too short, invalid locked assignments, conflicting locked exams, graph generation failure, algorithm failure, invalid coloring, schedule validation failure, database failure, export failure, unauthorized access, stale graph. Each has a code, HTTP status, user-readable message, no internal detail, and a UI string. Add a test that raises each and checks the response shape.

### 14.2 Privacy (§23)

- [ ] **P14.10** Data-minimisation review: graph, timetable and report responses exclude student identifiers unless the role and endpoint explicitly require them; shared-student detail endpoints require staff role and write an audit entry.
- [ ] **P14.11** Exports respect role scope; audit all exports.
- [ ] **P14.12** Retention policy: document and (optionally) implement purge/archival for old cycles, import batch files (already not stored), and audit log retention.
- [ ] **P14.13** Demo/synthetic data labelling: all seed data visibly marked "SYNTHETIC".

### 14.3 Reliability (§24)

- [ ] **P14.14** Transaction boundaries reviewed: imports, graph snapshot persistence (snapshot + edges together), schedule save (version + assignments together), publish, regenerate.
- [ ] **P14.15** Database backups: scheduled `pg_dump` (or managed backups) with a **tested restore** procedure documented.
- [ ] **P14.16** Idempotency/retry safety for generate/save/publish (idempotency keys or conflict-safe checks) to avoid double-click duplicates.
- [ ] **P14.17** Structured logs for generation runs (algorithm, duration, counts, outcome), validation, errors; request IDs end-to-end; log levels per environment. Optional metrics endpoint (Prometheus) for request latency and generation time.
- [ ] **P14.18** Graceful failure UX: backend downtime, timeouts, partial failure; retry affordances.

### 14.4 Performance (§4.2, §24)

- [ ] **P14.19** Build a generator for large synthetic datasets (500 exams, ~10k–20k students, realistic enrollment patterns) and benchmark each pipeline stage separately: import, graph build, each algorithm, slot mapping, validation, soft scoring, persistence, graph API response, PDF export.
- [ ] **P14.20** Target: generation (graph already built → saved schedule) under 5 s for 500 exams on reference hardware; if exceeded, profile and optimise (adjacency sets, avoiding repeated sorting, DSATUR heap variant, batch DB writes, `COPY`/bulk inserts, indexes). Record results in `docs/performance.md`; revise the provisional target if justified (PRD notes targets are provisional).
- [ ] **P14.21** Pagination everywhere on large tables; indexed queries verified with `EXPLAIN` on the heaviest ones.
- [ ] **P14.22** Frontend performance: bundle size budget, code-splitting per route (graph page lazily loaded), React Flow optimisations from P12.7, Lighthouse run on key pages.
- [ ] **P14.23** If generation exceeds interactive limits on larger data, move to background jobs (task queue such as RQ/Celery/ARQ or FastAPI background tasks with a `jobs` table) with status polling and cancellation; the API contract (run status) is already designed for this in P8.13.

**Exit criteria:** Security test suite green; error registry complete; benchmarks documented and within target (or target formally revised); backup restore tested.

---

# Phase 15 — Testing and Quality Assurance

**Goal:** Prove the system against PRD §26–§27. Most tests are written inside their phases; this phase closes gaps, adds cross-cutting suites and gates the release.

### 15.1 Backend

- [ ] **P15.1** Unit tests: import (§26.1), graph (§26.2), algorithms (§26.3), mapping, validators, soft scoring, permissions. Coverage gates: `algorithms/` ≥ 95% (aim 100% branches), `services/validation_service` ≥ 95%, overall ≥ 80%.
- [ ] **P15.2** Property-based tests (Hypothesis): random graphs → every algorithm output validates; random enrollment sets → graph validator passes and builder is equivalent to a brute-force O(n²) set-intersection reference implementation; random edit sequences never produce an invalid persisted schedule; locks always preserved under random lock sets that are feasible.
- [ ] **P15.3** Integration tests (§26.4): import→graph; graph→coloring; coloring→slot mapping; schedule validation; manual edit validation; lock→regeneration; publish→student view; export→content correctness (parse the files).
- [ ] **P15.4** Regression fixtures: curated small graphs with known optimal colorings (including a case where Greedy/WP use more colours than DSATUR and a case where all heuristics exceed the chromatic number, to document limits honestly).
- [ ] **P15.5** Determinism test: run the full pipeline twice on the demo dataset with deterministic mode and assert byte-identical assignments (PRD success metric "Reproducibility").
- [ ] **P15.6** Authorization matrix test (from P2) extended to all endpoints added later; one test per row of PRD §7.

### 15.2 Frontend

- [ ] **P15.7** Component and page tests per §26.5 (navigation, filters, import errors, algorithm selection, generate workflow, graph interaction, edit flow, locked state, student permissions, export buttons).
- [ ] **P15.8** Accessibility audit (axe automated + manual keyboard and screen-reader pass on timetable, graph alternatives, forms).
- [ ] **P15.9** Cross-browser check (current Chrome, Firefox, Safari/WebKit, Edge) and responsive check (desktop primary; tablet acceptable; phone for student timetable).

### 15.3 End-to-end (§26.6)

- [ ] **P15.10** Playwright test of the full representative flow: admin login → create cycle → import subjects → students → enrollments → validate data → build graph → run DSATUR → validate → save candidate → lock one exam → regenerate → confirm lock preserved → publish → student login → view personal timetable. Run in CI against Dockerised stack with a fresh DB.
- [ ] **P15.11** E2E negative paths: invalid CSV rejected; invalid move blocked; publish blocked with stale data; student cannot reach admin pages; infeasible slot count reported.
- [ ] **P15.12** Visual/print regression for the timetable print view and PDF export.

### 15.4 Manual QA and UAT

- [ ] **P15.13** Run the PRD §33 demo script end-to-end by someone who did not build it; record defects.
- [ ] **P15.14** UAT with an examination administrator persona: usability of import errors, understanding of colour/slot mapping, clarity of infeasibility messages.
- [ ] **P15.15** Bug triage; no open severity-1/2 defects; known limitations written down.

### 15.5 Release gate checklist (from §27 and §35)

- [ ] All 24 acceptance criteria pass (Appendix B).
- [ ] Zero student conflicts in every published schedule produced by the test suite.
- [ ] Every Definition-of-Done item satisfied for each feature.
- [ ] CI green on main; coverage thresholds met; no high/critical vulnerabilities outstanding.

---

# Phase 16 — Demo Data, Documentation, Containerisation, Deployment

**Goal:** Demo-ready project (PRD §28 Phase 9, §32, §33, §34).

### 16.1 Demo dataset (§32)

- [ ] **P16.1** Create synthetic CSVs: 30–100 students, 8–15 subjects, 2 departments, 2 semesters/cohorts; shared enrollment patterns; several isolated subjects; one connected conflict subgraph; one deliberately high-degree exam; names clearly synthetic (e.g., "Student One").
- [ ] **P16.2** Tune the data (without cheating) so algorithms differ visibly where possible; document honestly that this is one dataset, not proof of superiority (PRD §32).
- [ ] **P16.3** Seed script: `python -m app.scripts.seed_demo` creates departments, an admin, a coordinator, a faculty user, a student user linked to a student record, a pre-configured cycle (e.g., 10–20 June, Mon–Sat, Morning 09:00–12:00 and Afternoon 14:00–17:00, Sunday excluded, holidays) — idempotent and refuses to run in production.
- [ ] **P16.4** Provide a "load demo data" button for admins in non-production environments only.
- [ ] **P16.5** Prepare scripted invalid-data CSVs for the import-error demo and a pre-built scenario for the invalid-move demo and lock/regenerate demo.

### 16.2 Documentation (§34, §27 criterion 24)

- [ ] **P16.6** `README.md`: overview, problem statement, features, tech stack, architecture diagram, setup (env vars, DB, running frontend/backend), demo dataset usage, test instructions, **known limitations** (heuristics not optimal; MVP excludes rooms/invigilators/multi-campus; fixed-length sessions model; synchronous generation), future enhancements.
- [ ] **P16.7** `docs/graph-model.md`: formal model G=(V,E), conflict rule, adjacency sets, edge weights, construction strategy and complexity (k(k−1)/2 per student), validation rules.
- [ ] **P16.8** `docs/algorithms.md`: pseudocode for Greedy, Welsh–Powell, DSATUR; correctness invariant (§12.5); complexity of each implementation actually built (including the heap variant); determinism policy; limitations; benchmark methodology and results table/graphs from P7.18.
- [ ] **P16.9** `docs/scheduling.md`: color→slot mapping, matching stage, locked-exam precolouring, hard vs soft constraints with penalty table, regeneration and diff reports.
- [ ] **P16.10** `docs/api.md` (or rely on OpenAPI) with example payloads from PRD §19 verified against the real implementation; Postman collection exported.
- [ ] **P16.11** `docs/security-privacy.md`, `docs/operations.md` (backup/restore, logs, rotating secrets, creating admins), `docs/adr/` complete.
- [ ] **P16.12** Screenshots for README (overview, graph before/after colouring, algorithm lab, timetable, invalid move message, student view).
- [ ] **P16.13** In-app help text/tooltips for key concepts (colour = slot group, saturation degree, locks, hard vs soft constraints).

### 16.3 Containerisation and deployment

- [ ] **P16.14** Production Dockerfiles: backend (multi-stage, non-root, gunicorn/uvicorn workers), frontend (build → static assets served by nginx). Healthchecks.
- [ ] **P16.15** `docker-compose.prod.yml` (or Kubernetes manifests): postgres with volume + backups, backend, nginx reverse proxy with TLS, environment configuration via secrets.
- [ ] **P16.16** Migration strategy: run `alembic upgrade head` as a release step before starting the new backend; rollback plan.
- [ ] **P16.17** CD pipeline: build images, tag with version/commit, push to registry, deploy to staging automatically and to production on approval.
- [ ] **P16.18** Staging environment smoke test (E2E subset); production checklist (HTTPS, CORS origins, rate limits, secrets, backups, monitoring, log shipping).
- [ ] **P16.19** Monitoring and alerting: uptime check, error-rate alert, slow-generation alert.

### 16.4 Release

- [ ] **P16.20** Tag `v1.0.0`; changelog; final run of the §33 demo; handover notes.

**Exit criteria:** A new developer can clone, follow the README, load demo data and run the full demo; the application is deployed and passes the release gate.

---

# Post-MVP Backlog (P2, PRD §29–§30)

Not part of the MVP; listed so the architecture leaves room for them.

- Room entities, capacities, allocation as a secondary constraint problem (§30.1) — keep `capacity` fields on `time_slots` and `exam_assignments` extensible; add `rooms` and `room_assignments` tables later.
- Invigilator allocation (§30.2).
- Advanced optimisation: backtracking exact solver for small graphs (useful as an optimality oracle for the benchmarks), branch and bound, tabu search, simulated annealing, genetic algorithms, constraint programming (§30.3). The algorithm interface from P7.1 is the extension point; record a random seed if randomness is introduced (§12.4).
- Fairness metrics: gaps between exams, total exam period, difficult-exam distribution (§30.4).
- Multi-duration optimisation, multi-campus support, ERP/SIS integration, notifications and calendar integration (.ics export), schedule-change notifications.
- Background job queue and cancellation for very large datasets.
- Expanded schedule-explanation traces beyond DSATUR (§30.5).

---

# Appendix A — Requirement Traceability Matrix

| PRD requirement | Implemented in |
|---|---|
| FR-01 Authentication & authorization | P2.7–P2.19, P14.1, P15.6 |
| FR-02 Academic structure | P3.1, P11.9 |
| FR-03 Subject management | P3.3–P3.8, P11.10 |
| FR-04 Student & enrollment management | P3.9–P3.17, P11.11 |
| FR-05 CSV import | P4.1–P4.15, P11.12 |
| FR-06 Scheduling cycle configuration | P5.1–P5.5, P11.9 |
| FR-07 Conflict graph construction | P6.1–P6.14 |
| FR-08 Interactive graph visualisation | P12.1–P12.9 |
| FR-09 Graph coloring engine | P7.1–P7.19, P8.11 |
| FR-10 Algorithm comparison lab | P8.18–P8.21, P12.15–P12.18 |
| FR-11 Color-to-time-slot mapping | P5.6–P5.12, P8.1–P8.6 |
| FR-12 Constraint engine (hard/soft) | P8.7–P8.10 |
| FR-13 Schedule generation | P8.11–P8.17, P12.10–P12.14 |
| FR-14 Timetable calendar view | P10.7, P12.19–P12.23 |
| FR-15 Manual schedule editing | P9.5–P9.11, P13.1–P13.4 |
| FR-16 Exam locking | P7.16–P7.17, P8.4, P9.12–P9.15, P13.5 |
| FR-17 Regeneration and repair | P9.16–P9.21, P13.8 |
| FR-18 Student timetable | P10.5–P10.8, P13.12–P13.14 |
| FR-19 Publishing | P10.1–P10.4, P13.9–P13.11 |
| FR-20 Export | P10.9–P10.14, P13.16 |
| FR-21 Audit and history | P2.20–P2.22, P10.20–P10.21, P11.13 |
| FR-22 Reports and analytics | P10.15–P10.19, P13.15 |
| §7 Roles & permissions | P2.14–P2.19, P13.17 |
| §11 Graph theory specification | P6.1–P6.6, P16.7 |
| §12 Algorithm specification | P7.*, P16.8 |
| §13 Time slot & calendar | P5.6–P5.12, P8.1–P8.6 |
| §14 Optimisation & quality | P8.9, P8.14, P9.17 |
| §15 Manual editing & locks | Phase 9 |
| §16 UX requirements | Phases 11–13 |
| §17 Data model | P2.1–P2.6 |
| §18–19 API & payloads | Phases 2–10 (each endpoint list), P16.10 |
| §20 Backend architecture | Layout section, P1.*, P7.* module isolation |
| §21–22 Frontend architecture & stack | P1.4, P1.15–P1.17, Phase 11–13 |
| §23 Security & privacy | P2.*, P4.2, P14.1–P14.13 |
| §24 Non-functional requirements | P14.14–P14.23, P11.6 |
| §25 Error handling | P0.6, P1.10, P14.9 |
| §26 Testing strategy | Per-phase **Tests** blocks, Phase 15 |
| §27 Acceptance criteria | Appendix B, P15.5 release gate |
| §28 Roadmap | Phase Overview mapping |
| §29 Prioritisation | `[P0/P1/P2]` tags, backlog section |
| §31 Risks | Appendix D |
| §32–33 Demo data & flow | P16.1–P16.5, P15.13 |
| §34 Documentation | P16.6–P16.13 |
| §35 Definition of Done | PR template (P0.4), Phase exit criteria, P15.5 |

---

# Appendix B — Acceptance Criteria Checklist (PRD §27)

| # | Criterion | Verified by |
|---|---|---|
| 1 | Admin can authenticate | Phase 2 tests; E2E P15.10 |
| 2 | Admin can create a scheduling cycle | Phase 5; P11.9; E2E |
| 3 | Admin can import subjects, students, enrollments | Phase 4; P11.12; E2E |
| 4 | Invalid data reported, not silently accepted | P4.5–P4.7 tests; negative E2E P15.11 |
| 5 | Conflict graph correctly represents overlap | P6 tests; graph validator; property test P15.2 |
| 6 | Graph statistics correct | P6.5 hand-computed fixtures |
| 7 | Graph visualised interactively | P12.1–P12.9 |
| 8 | Greedy implemented | P7.6 |
| 9 | Welsh–Powell implemented | P7.9 |
| 10 | DSATUR implemented | P7.11 |
| 11 | All results pass independent validation | P7.13–P7.14; property tests |
| 12 | Algorithms compared on same graph | P8.18; snapshot-id assertion |
| 13 | Color classes map to valid slots | P8.1–P8.7 |
| 14 | Timetable contains every required exam | P8.7 completeness check; success-metric test |
| 15 | No student has overlapping exams | P8.7 per-student recheck; publish gate P10.1 |
| 16 | Manual moves validated | P9.5–P9.8; P13.2–P13.4 |
| 17 | Admin can lock exams | P9.12; P13.5 |
| 18 | Regeneration preserves locks or reports infeasibility | P9.16–P9.17; lock E2E |
| 19 | Admin can publish validated schedule | P10.1; P13.10 |
| 20 | Student views personal timetable | P10.5; P13.12; E2E |
| 21 | Exports work | P10.9–P10.14; content-correctness tests |
| 22 | Important operations logged | P2.20–P2.22; P10.21 coverage test |
| 23 | Tests cover core graph and algorithm logic | Phases 6–7, P15.1–P15.4 |
| 24 | README: setup, algorithms, usage, limitations | P16.6–P16.9 |

---

# Appendix C — PRD Ambiguities and Decisions Taken

| # | Ambiguity in PRD | Decision in this plan (confirm in Phase 0 ADRs) |
|---|---|---|
| 1 | §17.7 says enrollment links to "academic_year_id **or** cycle_id". | Enrollments tie to a **cycle** so different exam periods can have different enrollment sets; academic year is derivable. |
| 2 | "Unique subject code within applicable academic scope" is undefined. | Unique per (department, academic year) at minimum; decide on global uniqueness with the registrar. Import uses `subject_code` as the lookup key, so global uniqueness is simplest. |
| 3 | FR-11: "color group not split into overlapping sessions" vs. capacity limits. | One color class = exactly one slot (ADR-004). Over-capacity classes either reported infeasible or split into same-day slots (P8.5), never silently dropped. |
| 4 | Locked exams as "precolored" — colors are abstract, slots are concrete. | Reserve one color per distinct locked slot before coloring (P8.4). |
| 5 | Varying exam durations in fixed-length sessions (§13.4). | MVP: `duration ≤ slot duration` check in eligibility; class mapped only to slots that fit its longest exam; true multi-duration optimisation is P2. |
| 6 | Role "System Administrator" appears as a persona but not in the §7 matrix. | Treated as `admin` plus deployment access; no separate in-app role. |
| 7 | Coordinator "Scoped/optional" import permission. | Default off; implement as a per-user flag `can_import`, scoped to their department. |
| 8 | Whether students see enrollment counts on their timetable. | Hide by default (FR-18 emphasises no data about others). |
| 9 | Save semantics for manual edits (in-place vs new revision). | In-place on Candidate/Reviewed versions with full audit + edit history; new version only on regenerate/clone/publish (P9.3). |
| 10 | Timing target "under 5 seconds for 500 exams" — scope of what is timed. | Measure graph-built → saved schedule, and separately the full pipeline including graph build; report both (P14.19–P14.20). |
| 11 | Excel export marked optional. | Include behind a feature flag after CSV/PDF are done. |
| 12 | PRD §18 lists `DELETE /students/{id}`, but FR-04 says archive. | `DELETE` performs archive; physical deletion not exposed. |
| 13 | Where a student has no user account. | Students can exist without `user_id`; only those with a linked account can log in (P2.17). |
| 14 | "Reviewed" status exists for cycles and versions but no transition is described. | Admin explicitly marks `Reviewed` after a clean validation (P13.9); any later edit reverts to `Candidate`. |

---

# Appendix D — Risk Register to Task Mapping (PRD §31)

| Risk | Mitigating tasks |
|---|---|
| Incorrect enrollment data | P4.4–P4.6 preview and validation; P3.15 data validation report |
| Graph construction bug | P6.4 independent validator; fixtures; P15.2 brute-force equivalence test |
| Heuristic uses too many colours | P8.18 comparison; P8.14 local improvement; P2 backlog exact solver |
| Insufficient time slots | P5.11 pre-check; P8.6 infeasibility report; P12.12 UI |
| Manual edits introduce conflicts | P9.5–P9.8 server-side validation; P8.7 re-validation |
| Locked exams make schedule infeasible | P9.15, P9.17 clear reports and unlock suggestions |
| Large graph rendering is slow | P12.7 optimisations; filters |
| Data privacy exposure | P2.15–P2.17, P6.11, P14.10–P14.11 |
| Algorithm runtime increases | P7.4 instrumentation; P7.11 heap variant; P14.19–P14.23 background jobs |
| Changes invalidate graph | P3.16, P4.10, P6.6, P6.10 stale detection |
| Users misinterpret colours | P12.4 labels and patterns; P16.13 help text |

---

# Appendix E — Suggested Build Order Summary (Critical Path)

1. Phase 0 → 1 (decisions, skeleton).
2. Phase 2 → 3 → 4 (schema, auth, data, import) — the foundation for everything.
3. **In parallel:** Phase 7 (pure algorithms; needs no DB) can start as soon as Phase 1 is done, since it depends only on the graph data structure defined in P6.1. Starting Phases 6 and 7 early de-risks the core DAA deliverable.
4. Phase 5 (cycles & slots) → Phase 6 (graph) → Phase 8 (scheduling engine) → Phase 9 (edit/lock/regen) → Phase 10 (publish/export/reports).
5. Frontend phases 11–13 trail the backend by one phase each.
6. Phase 14 hardening starts alongside Phase 10 and finishes before Phase 15's release gate.
7. Phase 16 demo/docs/deploy last; keep README and ADRs updated continuously rather than at the end.

**Minimum demo-able slice (P0 first):** Phases 1–8 backend plus a thin UI for import, generate, comparison table and timetable grid, plus CSV/PDF export. Then layer P1 features (interactive graph, edit, lock, regenerate, versions, student view, audit) in Phases 9, 12, 13.
