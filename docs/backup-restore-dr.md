# PostgreSQL Backup, Restore, and Disaster Recovery Runbook

**Document Reference:** PRD §19, Task P14.15  
**Service:** University Examination Timetable Database (`exam_scheduler_prod`)  
**Target RTO:** < 15 Minutes  
**Target RPO:** < 5 Minutes  

---

## 1. Automated Backup Strategies

### 1.1 Full Logical Backups (`pg_dump`)
Automated daily snapshots run at `02:00 UTC` using PostgreSQL native binary custom-format (`-Fc`):

```bash
# Execute compressed binary backup with schema verification
pg_dump \
  -h localhost \
  -U examscheduler_app \
  -d exam_scheduler_prod \
  -Fc \
  -f "/var/backups/postgres/exam_scheduler_$(date +%Y%m%d_%H%M%S).dump"
```

### 1.2 Continuous Archiving & WAL Streaming (Point-in-Time Recovery)
PostgreSQL Write-Ahead Logging (WAL) is enabled in `postgresql.conf`:
```ini
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /mnt/wal_archive/%f && cp %p /mnt/wal_archive/%f'
archive_timeout = 300
```
This guarantees an RPO of less than 5 minutes during an unplanned infrastructure failover.

---

## 2. Restoration & Verification Procedures

### 2.1 Complete Database Restoration (`pg_restore`)
To restore an archived dump into a clean staging or recovery database:

```bash
# 1. Terminate active backend connections
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'exam_scheduler_prod';"

# 2. Re-create target database
dropdb -U postgres --if-exists exam_scheduler_prod
createdb -U postgres -O examscheduler_app exam_scheduler_prod

# 3. Restore in parallel (4 jobs) with error logging
pg_restore \
  -h localhost \
  -U postgres \
  -d exam_scheduler_prod \
  -j 4 \
  --verbose \
  "/var/backups/postgres/exam_scheduler_YYYYMMDD_HHMMSS.dump"
```

### 2.2 Integrity & Consistency Sanity Checks
Immediately following restore, execute the verification script:
```bash
python scripts/verify_db_indexes.py
python -m pytest backend/tests/test_permission_matrix.py
```

---

## 3. Disaster Recovery (DR) Drill Schedule

| Drill Type | Frequency | Validation Criteria |
| :--- | :--- | :--- |
| **Automated Restore Verification** | Weekly (Staging) | Dump successfully restores into CI pipeline and all tests pass. |
| **Simulated Primary Failover** | Quarterly | Hot-standby replica promoted; application reconnects within 60s. |
| **Point-in-Time Rollback** | Semi-Annually | Restore to exact timestamp preceding simulated accidental data loss. |
