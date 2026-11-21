# Operations & Production Runbook

## 1. Production Architecture Overview

The production deployment runs via Docker Compose or Kubernetes, comprising:
- **Nginx Reverse Proxy:** Terminates TLS (HTTPS), applies security headers (HSTS, CSP, nosniff), manages CORS, serves optimized frontend static assets, and proxies API requests to the backend.
- **Backend Application (`api`):** FastAPI running under Gunicorn with Uvicorn worker processes as a non-privileged `appuser`.
- **Relational Database (`postgres`):** PostgreSQL 16 with least-privilege role separation (`examscheduler_app`, `examscheduler_migrator`, `examscheduler_readonly`).

---

## 2. Automated Migration & Release Strategy

Before traffic is routed to newly deployed backend containers, database migrations must execute as an atomic release step.

### Migration Release Step
```bash
# Execute within migration container or CI/CD deployment pipeline:
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

### Rollback Procedure
If a migration fails or a release is aborted:
```bash
# Revert the latest migration
docker compose -f docker-compose.prod.yml run --rm backend alembic downgrade -1

# Or revert to a specific stable revision
docker compose -f docker-compose.prod.yml run --rm backend alembic downgrade <REVISION_ID>
```

---

## 3. Database Backup & Disaster Recovery (DR)

### Automated Daily Dump
```bash
# Run via cron daily at 02:00 UTC
BACKUP_FILE="/var/backups/pg_examscheduler_$(date +\%Y\%m\%d_\%H\%M\%S).sql.gz"
pg_dump -h localhost -U examscheduler_migrator -d examscheduler | gzip > "$BACKUP_FILE"
```

### Disaster Recovery / Restoration
```bash
# Restore from compressed dump
gunzip -c /var/backups/pg_examscheduler_20261122.sql.gz | psql -h localhost -U examscheduler_migrator -d examscheduler
```

---

## 4. Secret & Key Rotation Procedures

### JWT Secret Rotation
1. Update `JWT_SECRET` in production `.env` or Kubernetes Secret.
2. Invalidate existing sessions: all current JWT access tokens will be rejected. Users must re-authenticate.
3. Restart backend workers:
   ```bash
   docker compose -f docker-compose.prod.yml restart backend
   ```

### Admin User Bootstrapping
To create or update the initial administrative user:
```bash
ADMIN_EMAIL=admin@univ.edu ADMIN_PASSWORD=ComplexSecurePassword123! python -m app.scripts.seed_admin
```

---

## 5. Healthchecks, Monitoring & Alerting Thresholds

### Health Check Endpoints
- **Liveness Probe:** `GET /health` -> Returns `200 OK` if the process is responsive.
- **Readiness Probe:** `GET /health/ready` -> Returns `200 OK` after verifying database connection and connection pool responsiveness.

### Alerting Thresholds
| Metric | Warning Threshold | Critical Threshold | Action Required |
|---|---|---|---|
| **API Error Rate (5xx)** | > 1.0% over 5m | > 5.0% over 2m | Inspect application logs, verify database connection pool. |
| **P95 Response Latency** | > 500 ms | > 2,000 ms | Check slow queries, database indexes, and CPU load. |
| **Algorithm Execution** | > 3,000 ms | > 5,000 ms | Check graph density and dataset size; review memory allocation. |
| **Database Pool Exhaustion** | > 80% pool utilized | > 95% pool utilized | Increase `DB_POOL_SIZE` or investigate unclosed sessions. |
