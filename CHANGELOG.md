# Changelog

All notable changes to the University Examination Timetable Scheduling System are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-22

### Added
- **Graph Coloring Engine:**
  - Implemented pure DSATUR, Welsh-Powell, and Greedy graph coloring heuristics with deterministic tie-breaking.
  - Implemented $O(m)$ inverted index conflict graph builder with canonical edge IDs and PII minimization.
  - Implemented bipartite slot mapping and multi-factor soft constraint penalty scoring ($W_{\text{consec}}, W_{\text{sameday}}, W_{\text{gap}}, W_{\text{balance}}$).
  - Implemented independent hard constraint verification engine.
- **Academic & Cycle Management:**
  - Full relational schema for Departments, Programs, Subjects, Students, Enrollments, Cycles, and TimeSlots.
  - Atomic CSV bulk import pipeline with row-level validation and RFC-4180 parsing.
  - Calendar slot generator supporting session windows, excluded weekdays, and institutional holidays.
- **Schedule Versions & Editing:**
  - Candidate version branching, manual exam move with real-time conflict preview, and exam locking.
  - Incremental partial re-scheduling preserving locked exams.
  - Atomic version publication with immutability enforcement and superseded version archiving.
- **Security & Reliability:**
  - Least-privilege PostgreSQL roles (`migrator`, `app`, `readonly`).
  - Standard error envelope across 100% of API endpoints.
  - Sliding window rate limiting, idempotency keys, and OWASP security headers (CSP, HSTS).
  - 100% indexed foreign keys (35 FKs verified).
- **User Interface:**
  - Interactive Timetable Grid with drag/move modal and lock toggle.
  - Visual Conflict Graph Lab with Cytoscape Canvas rendering, degree distribution, and density metrics.
  - Student personal timetable view with FERPA privacy isolation.
  - Comprehensive reporting suite with RFC-4180 CSV, ReportLab PDF, and OpenPyXL Excel exports.
  - "Load Demo Data" administrative button and in-app concept glossary.
- **Testing & Quality:**
  - 129 backend unit, integration, and Hypothesis property-based tests.
  - 21 frontend component and accessibility tests.
  - Playwright browser end-to-end golden path workflow.
- **Deployment & Operations:**
  - Multi-stage non-root Dockerfiles for backend and frontend.
  - Production `docker-compose.prod.yml` and Nginx reverse proxy configuration.
  - CI/CD pipeline automation (`.github/workflows/ci-cd.yml`).
