# University Examination Timetable Scheduling System

An enterprise-grade, explainable, constraint-based university examination scheduling system powered by Graph Coloring algorithms (**DSATUR**, **Welsh–Powell**, and **Greedy Coloring**).

---

## 1. System Overview

The University Examination Timetable Scheduling System automates the generation, validation, visualization, optimization, and publishing of university examination timetables.

By modeling examinations as vertices in an undirected graph and student overlap as weighted conflict edges, the system produces conflict-free examination schedules where no student has overlapping examinations.

### Core Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, ReportLab, OpenPyXL
- **Algorithms:** DSATUR (Primary), Welsh–Powell, Greedy Coloring, Bipartite Matching
- **Frontend:** React 18+, Vite, TypeScript (strict), Tailwind CSS, React Flow, Recharts, TanStack Query
- **Database:** PostgreSQL with full relational integrity and audit logging

---

## 2. Quick-Start Guide

### Prerequisites
- Python 3.11+
- Node.js 20+ and npm
- (Optional) Docker & Docker Compose for containerized PostgreSQL

### Option A: Running with Docker Compose (Recommended)
```bash
# Start PostgreSQL, Backend (with hot-reload), and Frontend (Vite)
docker compose -f docker-compose.dev.yml up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API & OpenAPI Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

### Option B: Running Locally

#### 1. Backend Setup
```bash
# Navigate to backend and install dependencies
cd backend
pip install -e ".[dev]"

# Configure environment (copy .env.example if needed)
# Run database migrations
python -m alembic upgrade head

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
# Navigate to frontend and install dependencies
cd frontend
npm install

# Start Vite dev server
npm run dev
```

---

## 3. Running Automated Tests

### Backend Tests
```bash
# Run unit & integration tests with coverage
pytest backend/tests --cov=backend/app

# Run linter and type checker
python -m ruff check backend/
python -m mypy backend/app
```

### Frontend Tests
```bash
cd frontend
npm run test:run
npm run lint
npm run typecheck
npm run build
```

---

## 4. Target Repository Layout

```text
exam-scheduler/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory, CORS, health & ready endpoints
│   │   ├── config/            # settings.py, database.py, logging.py
│   │   ├── api/v1/            # API v1 routes & endpoints
│   │   ├── models/            # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/           # Pydantic v2 request/response schemas
│   │   ├── services/          # Business logic, imports, graph, scheduling, validation
│   │   ├── algorithms/        # PURE algorithms (DSATUR, Welsh-Powell, Greedy, metrics)
│   │   ├── repositories/      # Database queries & department-scoped lookups
│   │   ├── middleware/        # Request ID propagation & centralized error handlers
│   │   └── utils/
│   ├── migrations/            # Alembic database migration scripts
│   ├── tests/                 # Unit, integration, and property-based test suites
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/        # Layout, tables, dialogs, forms, design primitives
│   │   ├── pages/             # PRD §16.3 pages (Overview, Cycles, Subjects, Timetable, etc.)
│   │   ├── services/          # Typed API client with error normalization
│   │   ├── context/           # Auth and session context
│   │   └── styles/            # Tailwind CSS design tokens
│   ├── package.json
│   └── vite.config.ts
├── docker/                    # Dockerfiles, init SQL, and Nginx configurations
├── docs/                      # Architectural Decision Records (ADRs), glossary, backlog
├── .github/workflows/         # Continuous Integration (CI) configuration
└── README.md
```

---

## 5. Architectural Invariants (PRD §20, §36)

- **Pure Algorithm Isolation:** The `app/algorithms/` module has **zero dependencies** on FastAPI, SQLAlchemy, or the database. It operates strictly on plain Python data structures (`dict`, `set`, `list`, `dataclass`).
- **Separation of Coloring from Scheduling:** Coloring produces abstract independent sets; the scheduling service independently handles calendar date mapping, session times, holidays, and durations.
- **Independent Schedule Validator:** Verification runs on an independent code path from schedule generation.
- **Zero Raw Exceptions:** All API errors adhere to the standard envelope `{ "error": { "code", "message", "details", "requestId" } }`.
