# Staging Environment Smoke Test Plan (Task P16.18)

## Purpose
Validates that deployed staging artifacts (containers, network, database migrations, authentication, and core algorithms) function properly prior to production sign-off.

---

## Smoke Test Steps

| Step # | Target Subsystem | Action | Expected Output | Status |
|---|---|---|---|---|
| **ST-01** | Gateway / Liveness | `GET /health` | HTTP 200, `{"status": "healthy"}` | Pass |
| **ST-02** | Gateway / Readiness | `GET /health/ready` | HTTP 200, `{"database": "connected"}` | Pass |
| **ST-03** | Auth Service | `POST /api/v1/auth/login` with admin credentials | HTTP 200, valid JWT accessToken and refreshToken | Pass |
| **ST-04** | Academic Data | `GET /api/v1/departments` | HTTP 200, list of departments returned | Pass |
| **ST-05** | Demo Seeder | `POST /api/v1/dev/seed-demo` | HTTP 200, 50 students, 12 subjects, cycle populated | Pass |
| **ST-06** | Conflict Graph | `POST /api/v1/cycles/{id}/graph/build` | HTTP 200, non-stale snapshot generated | Pass |
| **ST-07** | Timetable Engine | `POST /api/v1/cycles/{id}/schedule/generate` with DSATUR | HTTP 200, `isValid: true`, execution time < 5.0s | Pass |
| **ST-08** | Candidate Save | `POST /api/v1/schedule-runs/{id}/save` | HTTP 200, candidate version created | Pass |
| **ST-09** | Publishing Flow | `POST /api/v1/schedules/{id}/publish` | HTTP 200, version status set to Published | Pass |
| **ST-10** | Student Isolation | `GET /api/v1/me/timetable` with student token | HTTP 200, only student's own exams returned | Pass |
| **ST-11** | PDF / CSV Export | `GET /api/v1/schedules/{id}/export/pdf` | HTTP 200, valid binary PDF stream | Pass |
