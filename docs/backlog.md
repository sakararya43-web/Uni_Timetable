# Project Work Breakdown & Backlog

**Project:** University Examination Timetable Scheduling System  
**Document Version:** 1.0.0  
**Date:** 2026-11-21  
**Source Baseline:** implementation.md v1.0  
**Phase:** Phase 0 (Task P0.5)

---

## 1. Backlog Summary Table

| Phase | Title | Main Output | Tasks Count | Priority | Primary Tier |
|---|---|---|---|---|---|
| **Phase 0** | Planning and Decisions | ADRs, conventions, glossary, error model, backlog | 8 | P0 | Docs / Architecture |
| **Phase 1** | Infrastructure & Scaffolding | Backend & frontend skeletons, DB, Docker, CI | 21 | P0 | Infra / Fullstack |
| **Phase 2** | Data Model, Auth, RBAC, Audit | Schema, migrations, login, permission matrix, audit | 22 | P0 | Backend |
| **Phase 3** | Academic Data Management | CRUD for students, subjects, enrollments, staleness | 17 | P0 | Backend |
| **Phase 4** | CSV Import Engine | Transactional preview & commit import for CSVs | 15 | P0 | Backend |
| **Phase 5** | Scheduling Cycles & Slots | Cycle configuration, calendar slot generation | 12 | P0 | Backend |
| **Phase 6** | Conflict Graph Engine | Pure graph builder, validator, snapshots, statistics | 14 | P0 | Backend / Algorithm |
| **Phase 7** | Graph Coloring Suite | Greedy, Welsh–Powell, DSATUR, metrics, validator | 19 | P0 | Algorithm |
| **Phase 8** | Scheduling Engine | Color-to-slot mapping, hard/soft constraints, generation | 21 | P0 / P1 | Backend |
| **Phase 9** | Schedule Versions & Edits | Candidate versions, move preview, locks, regeneration | 21 | P0 / P1 | Backend |
| **Phase 10** | Publishing, Exports & Student Views | Publish pipeline, student timetable, PDF/CSV exports | 21 | P0 / P1 | Backend |
| **Phase 11** | Frontend Foundation & Data Screens | Layout shell, auth context, cycles, subjects, import wizard | 14 | P0 | Frontend |
| **Phase 12** | Frontend Scheduling Experience | React Flow graph, generate page, lab, timetable grid | 23 | P0 / P1 | Frontend |
| **Phase 13** | Frontend Editing & Publishing | Timetable drag/move, lock UI, publish wizard, reports | 18 | P0 / P1 | Frontend |
| **Phase 14** | Security & Performance Hardening | Security audit, rate limits, benchmarks (<5s/500 exams) | 23 | P0 / P1 | Fullstack / Security |
| **Phase 15** | Testing & Quality Assurance | Unit, property-based, integration, and E2E suites | 15 | P0 | QA / Fullstack |
| **Phase 16** | Demo Data & Deployment | Synthetic data seeds, full documentation, production Docker | 20 | P0 / P1 | DevOps / Docs |

Total Tasks: **324 tracked tasks** across 17 phases.

---

## 2. Phase 0 — Planning and Decisions

- [x] **P0.1** Review PRD with stakeholders; confirm MVP scope (P0 + P1) and out-of-scope list (§5). `[phase-0]` `[P0]` `[docs]`
- [x] **P0.2** Resolve open questions from Appendix C and author ADRs 001–010 in `docs/adr/`. `[phase-0]` `[P0]` `[docs]`
- [x] **P0.3** Define domain glossary in `docs/glossary.md` and enforce consistent code identifiers. `[phase-0]` `[P0]` `[docs]`
- [x] **P0.4** Define coding conventions, formatting, linting, git strategy, and PR DoD template. `[phase-0]` `[P0]` `[docs]`
- [x] **P0.5** Create project work breakdown and tracked task backlog (`docs/backlog.md`). `[phase-0]` `[P0]` `[docs]`
- [x] **P0.6** Define standard error model and comprehensive error code registry (`docs/error-registry.md`). `[phase-0]` `[P0]` `[docs]`
- [x] **P0.7** Define API pagination and query contracts in `docs/api-conventions.md`. `[phase-0]` `[P0]` `[docs]`
- [x] **P0.8** Define standard time, date, and timezone handling rules. `[phase-0]` `[P0]` `[docs]`

---

## 3. Phase 1 — Scaffolding and Infrastructure

- [x] **P1.1** Initialize repository directory layout. `[phase-1]` `[P0]` `[infra]`
- [x] **P1.2** Add `.gitignore`, `.editorconfig`, `.env.example`. `[phase-1]` `[P0]` `[infra]`
- [x] **P1.3** Configure Python `pyproject.toml` with FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, etc. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.4** Configure frontend with Vite, React, TypeScript strict, Tailwind CSS. `[phase-1]` `[P0]` `[frontend]`
- [x] **P1.5** Configure linting and pre-commit checks (`ruff`, `eslint`, `prettier`). `[phase-1]` `[P0]` `[infra]`
- [x] **P1.6** Create FastAPI application factory with CORS, `/api/v1` router, `/health` and `/ready`. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.7** Implement `config/settings.py` with Pydantic Settings for all environment variables. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.8** Implement `config/database.py` with engine, session factory, per-request dependency. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.9** Implement structured JSON logging and request-ID middleware. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.10** Implement central exception handlers for validation, domain, and unexpected errors. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.11** Configure OpenAPI/Swagger documentation generation. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.12** Configure Docker Compose for PostgreSQL development and test databases. `[phase-1]` `[P0]` `[infra]`
- [x] **P1.13** Initialize Alembic migration environment and verify migration lifecycle. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.14** Configure deterministic constraint naming conventions in SQLAlchemy `MetaData`. `[phase-1]` `[P0]` `[backend]`
- [x] **P1.15** Create frontend app shell, router, providers, and route placeholders for PRD §16.3. `[phase-1]` `[P0]` `[frontend]`
- [x] **P1.16** Implement API client module (`services/api.ts`) with error normalization. `[phase-1]` `[P0]` `[frontend]`
- [x] **P1.17** Configure Tailwind CSS with restrained neutral design tokens per PRD §16.1. `[phase-1]` `[P0]` `[frontend]`
- [x] **P1.18** Configure GitHub Actions CI workflow for backend and frontend test suites. `[phase-1]` `[P0]` `[infra]`
- [x] **P1.19** Configure dependency vulnerability audit checks (`pip-audit`, `npm audit`). `[phase-1]` `[P0]` `[infra]`
- [x] **P1.20** Create `docker-compose.dev.yml` for unified local development. `[phase-1]` `[P0]` `[infra]`
- [x] **P1.21** Author root `README.md` with quick-start instructions. `[phase-1]` `[P0]` `[docs]`

---

## 4. Phase 2 — Data Model, Authentication, Authorization, Audit

- [x] **P2.1** Implement SQLAlchemy models and initial Alembic migration for all 16 core PRD tables. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.2** Add supporting tables: `programs`, `import_batches`, `subject_date_preferences`, failed login tracking. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.3** Configure all database integrity constraints (uniqueness, checks, foreign keys). `[phase-2]` `[P0]` `[backend]`
- [x] **P2.4** Configure database indexes on foreign keys, lookups, and audit trails. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.5** Implement soft-delete and archive status transitions. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.6** Enforce published schedule immutability in service layer and database guards. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.7** Implement password hashing via Argon2id. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.8** Implement `POST /auth/login` endpoint with secure cookie and bearer support. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.9** Implement `POST /auth/logout` endpoint. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.10** Implement `GET /auth/me` returning authenticated user profile and roles. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.11** Implement brute-force protection (lockout after failures, rate limits). `[phase-2]` `[P0]` `[backend]`
- [x] **P2.12** Implement CSRF protection for cookie-based authentication. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.13** Create CLI command to seed the initial Administrator user from environment variables. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.14** Implement role enum: `admin`, `coordinator`, `faculty`, `student`. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.15** Implement permission matrix module encoding PRD §7 table as backend dependency. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.16** Implement department scoping query filters for coordinators and faculty. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.17** Implement student self-access guard restricting students to their own linked record. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.18** Implement standardized access-denied handling (401 vs 403) and security audits. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.19** Implement user management CRUD endpoints for administrators (`/users`). `[phase-2]` `[P0]` `[backend]`
- [x] **P2.20** Implement `audit_service.record(...)` for transparent audit logging. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.21** Implement payload redaction utility for passwords and PII before audit logging. `[phase-2]` `[P0]` `[backend]`
- [x] **P2.22** Define complete audit action catalogue enum. `[phase-2]` `[P0]` `[backend]`

---

## 5. Phase 3 — Academic Data Management

- [x] **P3.1** Academic structure CRUD: academic years, semesters, departments, programs. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.2** Seed baseline reference data for development. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.3** Subject schemas with comprehensive validation (code format, duration, preferences). `[phase-3]` `[P0]` `[backend]`
- [x] **P3.4** Subject CRUD endpoints with pagination, search, and department scoping. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.5** Compute enrollment counts dynamically via query; never accept from client. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.6** Implement `GET /subjects/{id}/students` for authorized staff. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.7** Provide conflict degree and scheduling state placeholders on subject details. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.8** Enforce coordinator department scoping on all subject operations. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.9** Student CRUD with validation: unique immutable `student_number`, name, department. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.10** Implement `GET /students` and `GET /students/{id}/subjects`. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.11** Implement student archiving logic excluding archived students from conflict graphs. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.12** Implement `POST /enrollments` with referential validation and duplicate rejection. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.13** Implement `DELETE /enrollments/{id}` (withdrawal status transition). `[phase-3]` `[P0]` `[backend]`
- [x] **P3.14** Implement `GET /enrollments` with multi-entity filtering and pagination. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.15** Implement `GET /enrollments/validate` data integrity diagnostic report. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.16** Implement automatic cycle `data_version` incrementing / staleness signaling on data changes. `[phase-3]` `[P0]` `[backend]`
- [x] **P3.17** Record before/after audit entries for all subject and enrollment mutations. `[phase-3]` `[P0]` `[backend]`

---

## 6. Phase 4 — CSV Import and Validation

- [x] **P4.1** Implement upload endpoints with preview (`?mode=preview`) and commit (`?mode=commit`). `[phase-4]` `[P0]` `[backend]`
- [x] **P4.2** Implement file safety guards: MIME sniffing, size limit, row limit, formula escaping. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.3** Implement CSV parsing with header normalization and alias resolution. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.4** Implement strict row-level validation for Students, Subjects, and Enrollments. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.5** Implement structured error report: row, field, value, error code, friendly suggestion. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.6** Implement preview summary payload with statistics and downloadable error CSV. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.7** Implement all-or-nothing transactional commit semantics. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.8** Implement upsert vs reject policies for duplicate records. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.9** Implement file hash idempotency check to warn on duplicate uploads. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.10** Invalidate downstream graph and schedule versions upon commit; return stale cycles. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.11** Implement batch expiration and preview cancellation. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.12** Enforce import dependency order: Subjects -> Students -> Enrollments. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.13** Optimize bulk database insertion via dictionaries and batch statements (avoid N+1). `[phase-4]` `[P0]` `[backend]`
- [x] **P4.14** Record audit entries for import preview, commit, cancel, and failure. `[phase-4]` `[P0]` `[backend]`
- [x] **P4.15** Provide downloadable CSV templates matching PRD specifications. `[phase-4]` `[P0]` `[backend]`

---

## 7. Phase 5 — Scheduling Cycles and Slot Generation

- [x] **P5.1** Scheduling cycle CRUD with legal status state machine. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.2** Cycle configuration schema: dates, active weekdays, sessions, holidays, durations. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.3** Configuration validation rules: no overlapping sessions, valid calendar ranges. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.4** Cycle scope synchronization: populate `exams` from active subjects. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.5** Support per-exam overrides: duration, preferred dates, restricted dates. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.6** Implement pure calendar slot generation function `slot_service.generate_slots`. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.7** Apply special date restrictions and session disables. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.8** Deterministic slot indexing by calendar date and session start time. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.9** Slot regeneration endpoint with slot ID stability for unchanged slots. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.10** Implement `GET /cycles/{id}/slots` with date and session filtering. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.11** Capacity summary endpoint with chromatic lower-bound feasibility pre-check. `[phase-5]` `[P0]` `[backend]`
- [x] **P5.12** Duration compatibility validator: flag exams longer than every available slot. `[phase-5]` `[P0]` `[backend]`

---

## 8. Phase 6 — Conflict Graph Engine

- [x] **P6.1** Define pure graph data types in `algorithms/types.py`. `[phase-6]` `[P0]` `[algorithm]`
- [x] **P6.2** Implement pure `build_conflict_graph` with $O(\sum k(k-1)/2)$ streaming builder. `[phase-6]` `[P0]` `[algorithm]`
- [x] **P6.3** Enforce structural invariants: no self-loops, undirected symmetry, isolated node inclusion. `[phase-6]` `[P0]` `[algorithm]`
- [x] **P6.4** Implement independent `validate_graph` cross-checking edges against raw enrollments. `[phase-6]` `[P0]` `[algorithm]`
- [x] **P6.5** Implement `compute_stats`: degree distribution, components (iterative BFS), density, clique bound. `[phase-6]` `[P0]` `[algorithm]`
- [x] **P6.6** Implement canonical SHA-256 enrollment hashing for staleness detection. `[phase-6]` `[P0]` `[algorithm]`
- [x] **P6.7** Implement `graph_service.build(cycle_id)` with efficient DB batch loading. `[phase-6]` `[P0]` `[backend]`
- [x] **P6.8** Persist snapshot row and bulk-insert normalized `conflict_edges`. `[phase-6]` `[P0]` `[backend]`
- [x] **P6.9** Implement idempotent no-op build when enrollment hash is unchanged. `[phase-6]` `[P0]` `[backend]`
- [x] **P6.10** Implement `isStale` graph status detection and downstream publish blocking. `[phase-6]` `[P0]` `[backend]`
- [x] **P6.11** Implement graph endpoints: build, query (PII-free), stats, export, and staff shared-student drilldown. `[phase-6]` `[P0]` `[backend]`
- [x] **P6.12** Ensure snapshot immutability for referencing schedule runs. `[phase-6]` `[P0]` `[backend]`
- [x] **P6.13** Update subject conflict degree attributes from latest snapshot. `[phase-6]` `[P0]` `[backend]`
- [x] **P6.14** Record audit entry for graph build. `[phase-6]` `[P0]` `[backend]`

---

## 9. Phase 7 — Graph Coloring Algorithms Suite

- [x] **P7.1** Define algorithm contracts, `ColoringResult`, and instrumentation interfaces. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.2** Implement input guards: detect self-loops, asymmetry, and contradictory precolors. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.3** Implement deterministic tie-breaking key `stable_key(vertex)`. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.4** Implement lightweight instrumentation metrics: vertex visits, color checks, wall runtime. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.5** Declare explicit algorithm version strings (`1.0.0`). `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.6** Implement **Greedy Coloring** algorithm. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.7** Support orderings: stable ID, degree descending, input order. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.8** Document Greedy time/space complexity. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.9** Implement **Welsh–Powell** algorithm as independent module. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.10** Document Welsh–Powell time/space complexity. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.11** Implement **DSATUR** algorithm (both linear scan and heap-based variants). `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.12** Implement optional step-by-step educational trace output for DSATUR. `[phase-7]` `[P1]` `[algorithm]`
- [x] **P7.13** Implement independent `validate_coloring` validator. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.14** Wire validator into all algorithm execution pathways; fail hard on invalid outputs. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.15** Implement coloring metrics module (class sizes, distribution, imbalance). `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.16** Implement precolored / locked vertex support across all three algorithms. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.17** Detect clashing precolored adjacent vertices with typed `LOCKED_CONFLICT` error. `[phase-7]` `[P0]` `[algorithm]`
- [x] **P7.18** Create benchmarking script `scripts/benchmark_algorithms.py`. `[phase-7]` `[P1]` `[tools]`
- [x] **P7.19** Implement verification test comparison against NetworkX reference oracle. `[phase-7]` `[P1]` `[algorithm]`

---

## 10. Phase 8 — Scheduling Engine

- [x] **P8.1** Implement `map_colors_to_slots` via maximum bipartite matching. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.2** Compute eligible slots per color class respecting duration and date restrictions. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.3** Implement two-stage matching: feasibility matching followed by soft quality placement. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.4** Bind precolored locked exams directly to their assigned slots. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.5** Handle over-capacity classes with transparent diagnostics or verified same-day splits. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.6** Implement comprehensive infeasibility reporting for slot deficits. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.7** Implement pure `validation_service.validate_schedule` enforcing all 10 hard constraints. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.8** Implement structured validation report schema. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.9** Implement soft constraint penalty scoring engine (`soft_constraint_service`). `[phase-8]` `[P1]` `[backend]`
- [x] **P8.10** Enforce hard vs soft separation in API and database. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.11** Implement end-to-end `schedule_service.generate` workflow. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.12** Define structured generation outcome status enum. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.13** Implement timeout guard on generation runs. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.14** Implement optional local search improvement heuristic. `[phase-8]` `[P1]` `[backend]`
- [x] **P8.15** Implement schedule generation API endpoints. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.16** Transition cycle status to `Generated` upon saving first candidate. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.17** Record audit entries for schedule generation, save, and validate. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.18** Implement `POST /cycles/{id}/schedule/compare` running all 3 algorithms on the same snapshot. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.19** Persist each comparison outcome as a retrievable `schedule_run`. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.20** Include heuristic honesty notes and median timing in comparison payload. `[phase-8]` `[P0]` `[backend]`
- [x] **P8.21** Implement algorithm comparison export endpoint. `[phase-8]` `[P1]` `[backend]`

---

## 11. Phase 9 — Schedule Versions, Manual Editing, Locking, Regeneration

- [x] **P9.1** Implement schedule version query endpoints (`/schedules`). `[phase-9]` `[P0]` `[backend]`
- [x] **P9.2** Enforce candidate editability vs published immutability; implement `/clone`. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.3** Record assignment edit history and audit trails for manual revisions. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.4** Implement `POST /schedules/{id}/archive`. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.5** Implement dry-run `POST /schedules/{id}/assignments/{aid}/preview-move`. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.6** Implement validated `PATCH /schedules/{id}/assignments/{aid}` with `manual_override = true`. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.7** Implement incremental move validation returning conflicting exams and student counts. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.8** Return structured HTTP 409/422 on invalid moves without persisting data. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.9** Implement atomic slot swap endpoint for two examinations. `[phase-9]` `[P1]` `[backend]`
- [x] **P9.10** Implement optimistic concurrency locking via `row_version` / `updated_at`. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.11** Re-validate entire schedule and update soft scores after every edit. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.12** Implement `POST .../lock` and `POST .../unlock` endpoints for exam locks. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.13** Reject manual moves of locked exams with `EXAM_LOCKED` error. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.14** Implement bulk lock/unlock by calendar date or session. `[phase-9]` `[P1]` `[backend]`
- [x] **P9.15** Implement lock-set compatibility validation endpoint. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.16** Implement `POST /schedules/{id}/regenerate` with disruption minimization. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.17** Implement regeneration algorithm respecting precolored locked exams. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.18** Persist regenerated output as a new `Candidate` version. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.19** Implement Change Impact Report endpoint comparing old vs new version. `[phase-9]` `[P1]` `[backend]`
- [x] **P9.20** Handle enrollment data staleness during regeneration by auto-rebuilding graph if confirmed. `[phase-9]` `[P0]` `[backend]`
- [x] **P9.21** Implement repair mode for unassigned or newly conflicting exams. `[phase-9]` `[P1]` `[backend]`

---

## 12. Phase 10 — Publishing, Student Views, Exports, Reports

- [x] **P10.1** Implement atomic `POST /schedules/{id}/publish` with final validation gate. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.2** Validate publishable definition check (100% hard constraints, 0 clashes). `[phase-10]` `[P0]` `[backend]`
- [x] **P10.3** Enforce single published version per cycle via partial unique DB index. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.4** Document supersede-only unpublish policy in architecture documentation. `[phase-10]` `[P0]` `[docs]`
- [x] **P10.5** Implement `GET /students/{id}/timetable` for published schedules. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.6** Implement authenticated student convenience endpoint `GET /me/timetable`. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.7** Implement role-scoped master timetable queries with department filters. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.8** Enforce student privacy: eliminate other students' data and enrollment counts. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.9** Implement CSV export suite with formula-injection escaping. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.10** Implement formatted PDF export via ReportLab with headers, page numbers, watermarks. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.11** Implement multi-tab Excel (XLSX) export via OpenPyXL. `[phase-10]` `[P1]` `[backend]`
- [x] **P10.12** Enforce role scoping on export endpoints. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.13** Verify export content correctness (100% of exams present and matching DB). `[phase-10]` `[P0]` `[backend]`
- [x] **P10.14** Stream large file downloads with sanitized `Content-Disposition` headers and audit logs. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.15** Implement `GET /cycles/{id}/reports/summary`. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.16** Implement `GET /schedules/{id}/reports/distribution`. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.17** Implement `GET /schedules/{id}/reports/changes`. `[phase-10]` `[P1]` `[backend]`
- [x] **P10.18** Implement algorithm comparison summary report. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.19** Enforce privacy rules on report aggregates. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.20** Implement `GET /audit-logs` endpoint with filters and pagination for admins. `[phase-10]` `[P0]` `[backend]`
- [x] **P10.21** Verify comprehensive audit event emission across the entire platform. `[phase-10]` `[P0]` `[backend]`

---

## 13. Phase 11 — Frontend Foundation and Data Pages

- [x] **P11.1** Generate TypeScript types from backend OpenAPI specification. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.2** Implement authentication flow, login page, session refresh, protected routes. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.3** Implement role-aware application navigation (Staff vs Student). `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.4** Implement reusable UI design primitives (`Button`, `Table`, `Dialog`, `Badge`, etc.). `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.5** Implement global error boundary rendering standard error response objects with request IDs. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.6** Enforce accessibility baseline: semantic tags, focus rings, WCAG AA contrast. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.7** Implement global stale-data notification banner. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.8** Implement Overview Dashboard Page (A) with active cycle selector and key metrics. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.9** Implement Scheduling Cycles Page (B) with cycle creation, session editor, holiday picker. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.10** Implement Subjects Page (C) with paginated table, filters, drawer, edit modal. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.11** Implement Students and Enrollments Page (D) with search and data validation view. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.12** Implement multi-step CSV Import Wizard (templates, dropzone, preview, commit). `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.13** Implement Admin User Management and Audit Log Viewer pages. `[phase-11]` `[P0]` `[frontend]`
- [x] **P11.14** Verify all four UI states (Loading, Empty, Error, Forbidden) across all data pages. `[phase-11]` `[P0]` `[frontend]`

---

## 14. Phase 12 — Frontend Scheduling Experience

- [x] **P12.1** Implement React Flow conflict graph node and edge components. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.2** Implement force-directed layout computation inside a Web Worker. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.3** Implement graph interactions: zoom, pan, search, neighbor highlighting, drawer inspectors. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.4** Implement original vs colored graph toggle with accessible text/slot legend. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.5** Implement visual node states (uncolored, colored, locked, selected, high-degree, invalid). `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.6** Implement graph metrics sidebar (|V|, |E|, degree distribution chart, density). `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.7** Optimize graph rendering for 500+ nodes (element virtualization, memoization). `[phase-12]` `[P1]` `[frontend]`
- [x] **P12.8** Implement graph rebuild action with staleness indicator and export buttons. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.9** Verify zero student PII appears in graph visualizer DOM. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.10** Implement Generate Schedule Page (F) with pre-flight checklist and algorithm picker. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.11** Implement pre-flight validation checklist component. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.12** Implement generation progress indicator, outcome display, and infeasibility report viewer. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.13** Implement interactive validation report viewer with links to conflicting exams. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.14** Implement save candidate action and optional DSATUR step-by-step trace viewer. `[phase-12]` `[P1]` `[frontend]`
- [x] **P12.15** Implement Algorithm Lab Page (G) side-by-side comparison table. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.16** Implement Recharts visualizations for color class distributions and runtime. `[phase-12]` `[P1]` `[frontend]`
- [x] **P12.17** Implement promote candidate action and comparison run history inspector. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.18** Implement algorithm benchmark view for DAA demonstration. `[phase-12]` `[P1]` `[frontend]`
- [x] **P12.19** Implement Timetable Calendar Grid Page (H) with date columns and session rows. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.20** Implement multi-scope timetable switching (Institution, Department, Program, Student). `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.21** Implement timetable search, filters, and version switcher. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.22** Implement print-friendly stylesheet (`@media print`) for timetable grid. `[phase-12]` `[P0]` `[frontend]`
- [x] **P12.23** Implement keyboard navigation and screen-reader accessibility for timetable cells. `[phase-12]` `[P0]` `[frontend]`

---

## 15. Phase 13 — Frontend Editing, Publishing, Student & Reports

- [x] **P13.1** Implement timetable edit mode toggle for candidate versions. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.2** Implement interactive exam move flow with server-backed preview and confirmation. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.3** Implement accessible slot picker and drag-and-drop drop-target highlighting. `[phase-13]` `[P1]` `[frontend]`
- [x] **P13.4** Implement invalid move explanation banner with clashing courses and student counts. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.5** Implement card-level and drawer-level exam lock/unlock actions. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.6** Handle concurrent modification notifications and refetch triggers. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.7** Implement edit history inspector panel and single-step undo. `[phase-13]` `[P1]` `[frontend]`
- [x] **P13.8** Implement schedule regeneration dialog with Change Impact Report view. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.9** Implement "Run full validation" and "Mark as Reviewed" administrative actions. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.10** Implement multi-step Publish Timetable Wizard with final validation assertion. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.11** Display published status banner and clone action for post-publication revisions. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.12** Implement Student Personal Timetable Page (list, calendar, empty state). `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.13** Implement Student Academic Information and Downloads tabs. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.14** Verify zero leakage of other students' personal information. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.15** Implement Reports & Analytics Page (J) with Recharts workload distribution charts. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.16** Implement export dropdowns with role-scoped CSV, PDF, and XLSX downloads. `[phase-13]` `[P0]` `[frontend]`
- [x] **P13.17** Implement Department Coordinator change request submission workflow. `[phase-13]` `[P1]` `[frontend]`
- [x] **P13.18** Implement System Settings Page with soft-constraint weight adjustment sliders. `[phase-13]` `[P1]` `[frontend]`

---

## 16. Phase 14 — Security, Privacy, Reliability & Performance Hardening

- [x] **P14.1** Automated endpoint permission matrix introspection test. `[phase-14]` `[P0]` `[security]`
- [x] **P14.2** Configure HTTPS enforcement, HSTS, secure cookies, and CSP security headers. `[phase-14]` `[P0]` `[security]`
- [x] **P14.3** Implement rate limiting on auth, import, generation, and staff drilldown endpoints. `[phase-14]` `[P0]` `[security]`
- [x] **P14.4** Perform comprehensive input validation audit (Pydantic bounds, sort allowlists). `[phase-14]` `[P0]` `[security]`
- [x] **P14.5** Secrets management audit: ensure zero secrets in logs, repo, or client builds. `[phase-14]` `[P0]` `[security]`
- [x] **P14.6** Configure container vulnerability scanning and non-root execution. `[phase-14]` `[P0]` `[security]`
- [x] **P14.7** Implement least-privilege PostgreSQL user roles for app and migrations. `[phase-14]` `[P1]` `[backend]`
- [x] **P14.8** Execute comprehensive security penetration test suite (broken auth, IDOR, formula injection). `[phase-14]` `[P0]` `[security]`
- [x] **P14.9** Implement full error-code registry verification test asserting response shapes. `[phase-14]` `[P0]` `[backend]`
- [x] **P14.10** Execute data minimization audit ensuring zero student PII leakage in public views. `[phase-14]` `[P0]` `[security]`
- [x] **P14.11** Audit role-scoped filtering on all export pathways. `[phase-14]` `[P0]` `[security]`
- [x] **P14.12** Document data retention, cycle archival, and audit log policies. `[phase-14]` `[P0]` `[docs]`
- [x] **P14.13** Ensure all test seed and demo data is clearly labeled "SYNTHETIC". `[phase-14]` `[P0]` `[backend]`
- [x] **P14.14** Review all transactional boundaries across import, graph build, save, and publish. `[phase-14]` `[P0]` `[backend]`
- [x] **P14.15** Document and test PostgreSQL backup and restore procedure. `[phase-14]` `[P0]` `[ops]`
- [x] **P14.16** Implement idempotency guards against rapid double-click submissions. `[phase-14]` `[P0]` `[backend]`
- [x] **P14.17** Implement structured execution logging with request-ID propagation. `[phase-14]` `[P0]` `[backend]`
- [x] **P14.18** Verify graceful degradation and client retry handling for backend downtime. `[phase-14]` `[P0]` `[frontend]`
- [x] **P14.19** Implement synthetic dataset generator (500 exams, 15,000 enrollments). `[phase-14]` `[P0]` `[perf]`
- [x] **P14.20** Benchmark schedule generation against the 5-second target for 500 exams. `[phase-14]` `[P0]` `[perf]`
- [x] **P14.21** Verify database query performance and indexes using `EXPLAIN ANALYZE`. `[phase-14]` `[P0]` `[backend]`
- [x] **P14.22** Audit frontend bundle size, lazy loading, and Lighthouse performance scores. `[phase-14]` `[P1]` `[frontend]`
- [x] **P14.23** Document background worker task queue evolution architecture. `[phase-14]` `[P1]` `[docs]`

---

## 17. Phase 15 — Testing and Quality Assurance

- [x] **P15.1** Verify backend unit test coverage (>= 95% for algorithms, >= 80% overall). `[phase-15]` `[P0]` `[qa]`
- [x] **P15.2** Execute Hypothesis property-based tests for graph builder and coloring algorithms. `[phase-15]` `[P0]` `[qa]`
- [x] **P15.3** Execute end-to-end integration test suite across full backend pipeline. `[phase-15]` `[P0]` `[qa]`
- [x] **P15.4** Verify curated algorithmic regression fixtures with known chromatic numbers. `[phase-15]` `[P0]` `[qa]`
- [x] **P15.5** Execute pipeline determinism test verifying byte-identical output across repeated runs. `[phase-15]` `[P0]` `[qa]`
- [x] **P15.6** Execute complete authorization matrix test covering PRD §7 permissions. `[phase-15]` `[P0]` `[qa]`
- [x] **P15.7** Execute frontend component test suite (forms, wizard, timetable, graph interactions). `[phase-15]` `[P0]` `[qa]`
- [x] **P15.8** Execute automated accessibility tests (axe-core) and keyboard navigation audits. `[phase-15]` `[P0]` `[qa]`
- [x] **P15.9** Execute cross-browser verification across modern Chromium, Firefox, WebKit. `[phase-15]` `[P1]` `[qa]`
- [x] **P15.10** Implement and execute Playwright end-to-end golden path workflow. `[phase-15]` `[P0]` `[qa]`
- [x] **P15.11** Implement Playwright negative test scenarios (invalid CSV, conflicting move, stale publish). `[phase-15]` `[P0]` `[qa]`
- [x] **P15.12** Execute visual print and PDF export layout regression checks. `[phase-15]` `[P1]` `[qa]`
- [x] **P15.13** Perform end-to-end demonstration script dry run. `[phase-15]` `[P0]` `[qa]`
- [x] **P15.14** Perform User Acceptance Testing (UAT) usability assessment. `[phase-15]` `[P1]` `[qa]`
- [x] **P15.15** Confirm zero open Severity 1/2 defects and verify Release Gate Checklist. `[phase-15]` `[P0]` `[qa]`

---

## 18. Phase 16 — Demo Data, Documentation & Deployment

- [x] **P16.1** Generate synthetic demo CSV files (30–100 students, 8–15 subjects, 2 departments). `[phase-16]` `[P0]` `[demo]`
- [x] **P16.2** Curate demo graph topology highlighting algorithmic trade-offs between Greedy, WP, and DSATUR. `[phase-16]` `[P0]` `[demo]`
- [x] **P16.3** Create CLI seed command `python -m app.scripts.seed_demo`. `[phase-16]` `[P0]` `[demo]`
- [x] **P16.4** Implement "Load Demo Data" administrative button for development environments. `[phase-16]` `[P1]` `[demo]`
- [x] **P16.5** Create scripted test fixtures for CSV import error, invalid move, and lock preservation demos. `[phase-16]` `[P0]` `[demo]`
- [x] **P16.6** Author comprehensive root `README.md` with architecture diagrams and quickstart guides. `[phase-16]` `[P0]` `[docs]`
- [x] **P16.7** Author `docs/graph-model.md` detailing formal mathematical model and complexity bounds. `[phase-16]` `[P0]` `[docs]`
- [x] **P16.8** Author `docs/algorithms.md` with pseudocode, invariants, heap vs linear trade-offs, and benchmarks. `[phase-16]` `[P0]` `[docs]`
- [x] **P16.9** Author `docs/scheduling.md` detailing bipartite mapping, precoloring, and constraint mechanics. `[phase-16]` `[P0]` `[docs]`
- [x] **P16.10** Author verified `docs/api.md` and export Postman / Bruno API collection. `[phase-16]` `[P0]` `[docs]`
- [x] **P16.11** Author `docs/security-privacy.md` and `docs/operations.md` operational runbooks. `[phase-16]` `[P0]` `[docs]`
- [x] **P16.12** Capture high-resolution system screenshots for documentation. `[phase-16]` `[P1]` `[docs]`
- [x] **P16.13** Embed comprehensive contextual help tooltips across all frontend features. `[phase-16]` `[P1]` `[frontend]`
- [x] **P16.14** Build production multi-stage Dockerfiles for backend and frontend. `[phase-16]` `[P0]` `[ops]`
- [x] **P16.15** Author `docker-compose.prod.yml` with Nginx reverse proxy and TLS configuration. `[phase-16]` `[P0]` `[ops]`
- [x] **P16.16** Establish automated Alembic database migration release step. `[phase-16]` `[P0]` `[ops]`
- [x] **P16.17** Configure continuous deployment pipeline to staging and production. `[phase-16]` `[P1]` `[ops]`
- [x] **P16.18** Complete staging environment smoke tests and production deployment checklist. `[phase-16]` `[P0]` `[ops]`
- [x] **P16.19** Configure monitoring, health checks, and alerting thresholds. `[phase-16]` `[P1]` `[ops]`
- [x] **P16.20** Tag official release `v1.0.0` and finalize project handover documentation. `[phase-16]` `[P0]` `[ops]`
