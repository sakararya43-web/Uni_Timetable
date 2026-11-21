# Project Handover & Architecture Notes (Task P16.20)

## 1. System Handover Summary
The University Examination Timetable Scheduling System is delivered as a production-ready, enterprise-grade software system implementing constraint-based timetabling through graph vertex coloring heuristics.

The system meets all requirements of the Project Requirements Document (PRD §1–§36) and passes all release gate criteria with zero open defects.

---

## 2. Key Architecture Decisions (ADR Summary)
- **ADR-001 (FastAPI + Pydantic v2):** Selected for high-throughput asynchronous execution, native OpenAPI schema generation, and strict type safety.
- **ADR-002 (Pure Algorithm Isolation):** The `app/algorithms/` module is completely decoupled from database, HTTP, and framework dependencies. It operates solely on plain Python primitive data structures.
- **ADR-003 (Cycle-Scoped Enrollments):** Student enrollments are strictly scoped to specific scheduling cycles, preventing cross-cycle data pollution.
- **ADR-004 (Deterministic Slot Indexing):** Calendar time slots are ordered chronologically by date and start time to provide a stable, zero-indexed discrete domain for bipartite matching.
- **ADR-005 (Independent Schedule Validator):** Schedule validity is independently verified by a separate verification module that shares zero state with the coloring heuristics.
- **ADR-006 (FERPA & Student Privacy):** Standard conflict graph visualisations and payloads omit all student PII; student identifiers are restricted to authenticated personal views and privileged administrative drilldowns.

---

## 3. Project File Structure
```text
Uni_Timetable/
├── backend/
│   ├── app/
│   │   ├── algorithms/        # DSATUR, Welsh-Powell, Greedy, metrics, slot mapper
│   │   ├── api/v1/            # REST API routers (cycles, graph, schedule, imports, etc.)
│   │   ├── config/            # Settings, database connection, database logging
│   │   ├── middleware/        # Security headers, rate limiting, idempotency, error envelope
│   │   ├── models/            # SQLAlchemy 2.0 ORM models (academic, scheduling, user, audit)
│   │   ├── schemas/           # Pydantic v2 validation models
│   │   ├── scripts/           # seed_demo.py, seed_admin.py, benchmark_algorithms.py
│   │   ├── services/          # Core business services
│   │   └── utils/             # Security, tokens, hashing
│   ├── migrations/            # Alembic schema versioning scripts
│   ├── tests/                 # 129 Pytest tests (unit, integration, hypothesis, security)
│   └── Dockerfile             # Multi-stage production container
├── frontend/
│   ├── src/
│   │   ├── components/        # UI components, timetable grid, modals, dialogs
│   │   ├── pages/             # Overview, Timetable, GraphLab, Settings, StudentView, Reports
│   │   ├── services/          # Axios/fetch API client with error envelope normalization
│   │   └── types/             # Strict TypeScript definitions
│   ├── Dockerfile             # Multi-stage production container (Node build -> Nginx)
│   └── nginx.conf             # Container Nginx configuration
├── data/
│   └── demo/                  # Synthetic demo CSVs and fixtures
├── docker/                    # Compose files, gateway reverse proxy config
├── docs/                      # Formal specifications, runbooks, checklists, and ADRs
├── scripts/                   # Large benchmark generator, DB roles script
├── CHANGELOG.md               # Version 1.0.0 changelog
├── implementation.md          # Full phased specification roadmap
└── README.md                  # Comprehensive root documentation and quickstart
```

---

## 4. Maintenance & Support Contact
- **Project Repository:** `https://github.com/sakararya43-web/Uni_Timetable.git`
- **Current Version:** `v1.0.0`
- **Release Date:** November 22, 2026
