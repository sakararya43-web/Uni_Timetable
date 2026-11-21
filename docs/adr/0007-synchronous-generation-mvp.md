# ADR-007: Synchronous Schedule Generation for MVP with Background Worker Evolution

- **Status:** Accepted
- **Date:** 2026-11-21
- **Deciders:** Antigravity Architect, System Engineering Team
- **Context:** PRD §13, §18.7, §24, Appendix C Item 7

---

## Context and Problem Statement

Schedule generation requires running graph coloring, bipartite slot mapping, hard constraint validation, and soft penalty calculation.
On typical university workloads (up to 500 exams, thousands of enrollments), optimized in-memory Python implementations of Welsh–Powell and DSATUR complete in well under 2 seconds.
However, very large graphs (10,000+ exams) or compute-intensive local search optimization could exceed HTTP gateway timeouts (typically 30–60 seconds).

We must decide the API execution model for MVP schedule generation while ensuring forward compatibility with asynchronous job queues.

## Decision

1. **Synchronous MVP API with Job Schema Contract:**
   - Generation endpoints (`POST /cycles/{id}/schedule/generate`, `POST /cycles/{id}/schedule/compare`) execute synchronously in the HTTP request cycle for typical graphs.
   - However, generation immediately persists a `ScheduleRun` record with state `RUNNING` -> `SUCCESS` / `FAILED`.
   - The response payload returns the complete `ScheduleRun` object including `run_id`, `status`, `execution_time_ms`, and outcome diagnostics.
2. **Built-in Timeout Guard:**
   - Synchronous generation is wrapped in a configurable wall-clock timeout (default: 15 seconds).
   - If execution exceeds the threshold, the run transitions to `FAILED` with error code `GENERATION_TIMEOUT`.
3. **Evolution Path:**
   - Because generation already creates an explicit `ScheduleRun` entity, migrating to background worker execution (e.g., Celery, ARQ, or FastAPI BackgroundTasks) requires zero client-side schema changes: the frontend already handles polling `GET /schedule-runs/{run_id}` based on the initial `RUNNING` status response.

## Consequences

### Positive
- Zero infrastructure complexity for MVP: no external Redis/RabbitMQ queue dependency required to run the local dev stack.
- Fast, instant feedback for standard university scheduling cycles (< 2s).
- Contractually decoupled: status-polling architecture is supported from day one.

### Negative
- Extremely large batch computations must stay within the synchronous timeout window until external worker workers are activated in production deployments.
