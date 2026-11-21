-- =============================================================================
-- PostgreSQL Least-Privilege Database Role Configuration
-- PRD §19, Task P14.7
--
-- Implements separation of duties across three specialized database roles:
-- 1. examscheduler_migrator: DDL schema migrations (Alembic execution).
-- 2. examscheduler_app: DML operations (FastAPI backend runtime).
-- 3. examscheduler_readonly: Read-only analytics & reporting queries.
-- =============================================================================

-- Step 1: Create application database if not exists
-- CREATE DATABASE exam_scheduler_prod;

-- Step 2: Role for Running Alembic Migrations (DDL Privileges)
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'examscheduler_migrator') THEN
      CREATE ROLE examscheduler_migrator WITH LOGIN PASSWORD 'MIGRATOR_STRONG_PASS_CHANGE_ME';
   END IF;
END
$do$;

GRANT CONNECT ON DATABASE exam_scheduler_prod TO examscheduler_migrator;
GRANT ALL PRIVILEGES ON SCHEMA public TO examscheduler_migrator;

-- Step 3: Runtime Role for FastAPI Application (Strict DML Only)
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'examscheduler_app') THEN
      CREATE ROLE examscheduler_app WITH LOGIN PASSWORD 'APP_RUNTIME_STRONG_PASS_CHANGE_ME';
   END IF;
END
$do$;

GRANT CONNECT ON DATABASE exam_scheduler_prod TO examscheduler_app;
GRANT USAGE ON SCHEMA public TO examscheduler_app;

-- Grant DML (SELECT, INSERT, UPDATE, DELETE) only - NO DROP TABLE, NO ALTER TABLE
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO examscheduler_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO examscheduler_app;

-- Grant Sequence usage for autoincrement primary keys
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO examscheduler_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO examscheduler_app;

-- Step 4: Analytical / Read-Only Role (Zero Mutation Privileges)
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'examscheduler_readonly') THEN
      CREATE ROLE examscheduler_readonly WITH LOGIN PASSWORD 'READONLY_STRONG_PASS_CHANGE_ME';
   END IF;
END
$do$;

GRANT CONNECT ON DATABASE exam_scheduler_prod TO examscheduler_readonly;
GRANT USAGE ON SCHEMA public TO examscheduler_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO examscheduler_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO examscheduler_readonly;

-- Revoke dangerous administrative defaults from PUBLIC
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
