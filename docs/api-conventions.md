# API Conventions & Time/Date Standards

**Project:** University Examination Timetable Scheduling System  
**Document Version:** 1.0.0  
**Date:** 2026-11-21  
**Source Baseline:** PRD.md §17, §18, implementation.md P0.7, P0.8  
**Phase:** Phase 0 (Tasks P0.7, P0.8)

---

## 1. Pagination & Query Parameters Contract (P0.7)

All collection endpoints that return lists of records (e.g., `/students`, `/subjects`, `/enrollments`, `/schedules`, `/audit-logs`) must implement the standard pagination, sorting, and filtering contract.

### 1.1 Standard Request Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | `integer` | `1` | One-based page number (must be $\ge 1$). |
| `pageSize` | `integer` | `20` | Number of items per page (bounded between `1` and `100`). |
| `sort` | `string` | `"id:asc"` | Sort field and direction in `field:direction` format (e.g., `code:asc`, `createdAt:desc`). Only allowlisted fields may be sorted. |
| `q` | `string` | `null` | Free-text search term matched case-insensitively against primary natural keys and names. |

### 1.2 Additional Standard Filters
Individual endpoints may expose specific domain filters as query parameters:
- `departmentId`: UUID string filtering records by department.
- `status`: Lifecycle status filter (`active`, `archived`, `draft`, `published`).
- `semester`: Integer semester number.
- `cycleId`: UUID string scoping records to a specific scheduling cycle.

### 1.3 Standard Paginated Response Body

All paginated endpoints must return the uniform paginated envelope:

```json
{
  "items": [
    { "id": "uuid-1", "...": "..." },
    { "id": "uuid-2", "...": "..." }
  ],
  "total": 142,
  "page": 1,
  "pageSize": 20,
  "totalPages": 8,
  "hasNext": true,
  "hasPrev": false
}
```

---

## 2. Date, Time & Timezone Conventions (P0.8)

In examination scheduling, confusion between local wall-clock times and UTC timestamps can lead to exam misplacement or calendar day shifts across timezones. We enforce strict storage and serialization conventions across the full stack.

### 2.1 Calendar Dates (Days)
- **Concept:** Represents an abstract calendar date on which an examination takes place (e.g., June 15, 2026).
- **Format:** ISO-8601 Date string: `YYYY-MM-DD` (e.g., `"2026-06-15"`).
- **Database Type:** `DATE`.
- **Rule:** Dates have **no time component** and **no timezone offset**. June 15 is June 15 regardless of the client's current timezone.

### 2.2 Session Clock Times
- **Concept:** The recurring daily time window during which exams occur (e.g., Morning session starts at 09:00:00 and ends at 12:00:00).
- **Format:** ISO-8601 Time string: `HH:MM:SS` or `HH:MM` in 24-hour format (e.g., `"09:00:00"`).
- **Database Type:** `TIME WITHOUT TIME ZONE`.
- **Rule:** Wall-clock times are stored without timezone offsets. The institution/cycle timezone provides the local interpretation.

### 2.3 Cycle Timezone
- **Concept:** Every `SchedulingCycle` explicitly defines its local operational timezone.
- **Format:** Standard IANA Timezone Database string (e.g., `"Asia/Kolkata"`, `"America/New_York"`, `"UTC"`).
- **Database Type:** `VARCHAR(64)` on `scheduling_cycles.timezone`.
- **Rule:** All calendar computations and human-readable export headers use this timezone for rendering dates and times.

### 2.4 Event & Audit Timestamps
- **Concept:** Exact point-in-time system events (e.g., user login, schedule generation, edit audit, published timestamp).
- **Format:** ISO-8601 UTC timestamp with Zulu suffix: `YYYY-MM-DDTHH:MM:SS.sssZ` (e.g., `"2026-11-21T22:45:00.000Z"`).
- **Database Type:** `TIMESTAMP WITH TIME ZONE` (`timestamptz`).
- **Rule:** All timestamps are normalized to UTC in the database. Client applications convert UTC timestamps to user local time for display.

---

## 3. ID and Primary Key Conventions

- **Database Identifiers:** All table primary keys use UUID v4 strings (`UUID` in PostgreSQL, represented as lowercase 36-character hyphenated strings in JSON, e.g. `"f47ac10b-58cc-4372-a567-0e02b2c3d479"`).
- **Natural Institutional Keys:** Unique human-readable codes are preserved alongside UUIDs:
  - `student_number`: Alphanumeric (e.g., `"STU1001"`).
  - `subject_code`: Alphanumeric (e.g., `"CS301"`).
  - `version_number`: Monotonically increasing integer per cycle (`1, 2, 3...`).
