# University Examination Timetable Scheduling System

An enterprise-grade, explainable, constraint-based university examination scheduling system powered by Graph Coloring algorithms (**DSATUR**, **Welsh–Powell**, and **Greedy Coloring**).

---

## Overview

The University Examination Timetable Scheduling System automates the generation, validation, visualization, optimization, and publishing of university examination timetables.

By modeling examinations as vertices in an undirected graph and student overlap as weighted conflict edges, the system produces conflict-free examination schedules where no student has overlapping examinations.

### Core Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, ReportLab, OpenPyXL
- **Algorithms:** DSATUR (Primary), Welsh–Powell, Greedy Coloring, Bipartite Matching
- **Frontend:** React, Vite, TypeScript (strict), Tailwind CSS, React Flow, Recharts
- **Database:** PostgreSQL with full relational integrity and audit logging

---

## Project Documentation

All foundational architectural decisions, conventions, and tracking documents are established in `docs/`:

- [Project Scope & Requirements Baseline](docs/scope.md)
- [Architecture Decision Records (ADRs)](docs/adr/README.md)
  - [ADR-001: Authentication Mechanism](docs/adr/0001-auth-mechanism.md)
  - [ADR-002: Vertex Definition](docs/adr/0002-vertex-definition.md)
  - [ADR-003: Enrollment Scoping](docs/adr/0003-enrollment-scoping.md)
  - [ADR-004: Color-to-Slot Model](docs/adr/0004-color-to-slot-model.md)
  - [ADR-005: Precoloring Locked Exams](docs/adr/0005-locked-exams-precoloring.md)
  - [ADR-006: Graph Storage Architecture](docs/adr/0006-graph-storage.md)
  - [ADR-007: Synchronous Generation & Worker Evolution](docs/adr/0007-synchronous-generation-mvp.md)
  - [ADR-008: Document Generation (PDF/Excel)](docs/adr/0008-export-libraries.md)
  - [ADR-009: Subject Code Uniqueness](docs/adr/0009-subject-code-uniqueness.md)
  - [ADR-010: Schedule Versioning & Immutability](docs/adr/0010-schedule-versioning-and-immutability.md)
- [Domain Glossary & Standard Identifiers](docs/glossary.md)
- [Coding Conventions & PR Definition-of-Done](docs/conventions.md)
- [Work Breakdown & Task Backlog](docs/backlog.md)
- [Error Model & Error-Code Registry](docs/error-registry.md)
- [API Pagination & Time/Date Standards](docs/api-conventions.md)
- [Pull Request Template](.github/pull_request_template.md)
