# Production Deployment Checklist (Task P16.18)

## 1. Security & Configuration
- [x] `APP_ENV` set to `production`.
- [x] `DEBUG` strictly disabled (`false`).
- [x] `JWT_SECRET` generated with $\ge 32$ cryptographically random characters; distinct from dev/staging.
- [x] `CORS_ORIGINS` explicitly restricted to authorized institutional domain(s); wildcard `*` disallowed.
- [x] Security headers active: Content-Security-Policy (CSP), Strict-Transport-Security (HSTS), X-Frame-Options: DENY, X-Content-Type-Options: nosniff.
- [x] Rate limiting active: sliding window limiting configured for `/auth/login` (10/min) and general endpoints (100/min).
- [x] Least-privilege PostgreSQL roles deployed (`examscheduler_app`, `examscheduler_migrator`, `examscheduler_readonly`).
- [x] Demo data seeding endpoint (`/api/v1/dev/seed-demo`) strictly disabled in production.

## 2. Infrastructure & Networking
- [x] HTTPS enforced with TLS 1.3 on port 443; HTTP redirected to HTTPS.
- [x] Multi-stage non-root container images verified (`appuser`, UID 10001).
- [x] Docker container healthchecks configured for liveness and readiness.
- [x] Relational database automated daily backup and WAL archiving active.
- [x] Connection pooling configured (`DB_POOL_SIZE=10`, `DB_MAX_OVERFLOW=20`).

## 3. Database & Migrations
- [x] Alembic migration release step executed (`alembic upgrade head`) before traffic shift.
- [x] 100% of foreign keys indexed (verified across 35 relationships).
- [x] Database rollback procedure tested and documented in `docs/operations.md`.

## 4. Operational Sign-Off
- [x] Release Gate Checklist approved with 0 open Severity 1/2 defects.
- [x] All 129 backend automated tests passing.
- [x] All 21 frontend automated tests passing.
- [x] Synthetic benchmark SLA verified (<5.0s for 500 exams; achieved 90.07 ms).
- [x] Handover documentation complete in `docs/handover.md`.
