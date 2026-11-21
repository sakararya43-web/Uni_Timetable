# University Exam Timetable Scheduling API Reference

## 1. Authentication & Base URL
- **Base URL:** `http://localhost:8000/api/v1`
- **Authentication:** Bearer JWT in `Authorization` header (`Bearer <access_token>`).
- **Standard Error Envelope:**
  ```json
  {
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "Scheduling cycle not found",
      "details": {},
      "timestamp": "2026-11-22T01:30:00Z",
      "requestId": "req-9a8b7c"
    }
  }
  ```

---

## 2. API Endpoints by Domain

### 2.1 Authentication & Profile (`/auth`, `/users`, `/me`)
| Method | Path | Role Required | Description |
|---|---|---|---|
| `POST` | `/auth/login` | Public | Obtain access token and refresh token. |
| `POST` | `/auth/refresh` | Public | Refresh expired access token with valid refresh token. |
| `POST` | `/auth/logout` | Authenticated | Invalidate JWT token and revoke session. |
| `GET` | `/me` | Authenticated | Retrieve current user profile and role scope. |
| `GET` | `/me/timetable` | Student | Retrieve personalized exam timetable (FERPA protected). |
| `GET` | `/users` | Admin | List all registered system users. |
| `POST` | `/users` | Admin | Create a new user account with assigned role. |

### 2.2 Academic Structure (`/departments`, `/programs`, `/subjects`, `/students`, `/enrollments`)
| Method | Path | Role Required | Description |
|---|---|---|---|
| `GET` | `/departments` | Authenticated | List all active academic departments. |
| `POST` | `/departments` | Admin | Create an academic department. |
| `GET` | `/subjects` | Authenticated | List subjects with optional filters by department/semester. |
| `POST` | `/subjects` | Admin, Coordinator | Register a new subject. |
| `GET` | `/students` | Admin, Coordinator | List enrolled students. |
| `POST` | `/students` | Admin, Coordinator | Register a student record. |
| `POST` | `/imports/csv` | Admin, Coordinator | Bulk import students, subjects, or enrollments from CSV. |

### 2.3 Scheduling Cycles & Time Slots (`/cycles`)
| Method | Path | Role Required | Description |
|---|---|---|---|
| `GET` | `/cycles` | Authenticated | List all examination scheduling cycles. |
| `POST` | `/cycles` | Admin, Coordinator | Create a new scheduling cycle with calendar dates and session rules. |
| `GET` | `/cycles/{id}` | Authenticated | Fetch cycle details and status. |
| `GET` | `/cycles/{id}/slots` | Authenticated | Retrieve all generated time slots for the cycle. |
| `POST` | `/cycles/{id}/slots/generate` | Admin, Coordinator | Generate deterministic calendar slots based on cycle configuration. |

### 2.4 Conflict Graph Engine (`/cycles/{id}/graph`)
| Method | Path | Role Required | Description |
|---|---|---|---|
| `POST` | `/cycles/{id}/graph/build` | Admin, Coordinator | Compute or refresh the conflict graph snapshot. |
| `GET` | `/cycles/{id}/graph` | Authenticated | Retrieve vertices, edges, density, and chromatic lower bounds (PII-free). |
| `GET` | `/cycles/{id}/graph/conflicts/{edge_id}/students` | Admin, Coordinator | Privileged drilldown of shared students on a conflict edge. |

### 2.5 Scheduling Engine & Versions (`/cycles/{id}/schedule`, `/schedules`)
| Method | Path | Role Required | Description |
|---|---|---|---|
| `POST` | `/cycles/{id}/schedule/generate` | Admin, Coordinator | Execute coloring algorithm (DSATUR, Welsh-Powell, Greedy). |
| `POST` | `/schedule-runs/{run_id}/save` | Admin, Coordinator | Save algorithmic run as an editable candidate schedule version. |
| `GET` | `/cycles/{id}/schedules` | Authenticated | List all schedule versions for a cycle. |
| `GET` | `/schedules/{id}` | Authenticated | Get full schedule version details, assignments, and soft score. |
| `PATCH` | `/schedules/{id}/assignments/{aid}` | Admin, Coordinator | Move an exam to a new time slot with conflict preview. |
| `POST` | `/schedules/{id}/assignments/{aid}/lock` | Admin, Coordinator | Toggle lock status on an exam assignment. |
| `POST` | `/schedules/{id}/regenerate` | Admin, Coordinator | Incrementally re-color schedule preserving locked exams. |
| `POST` | `/schedules/{id}/publish` | Admin | Atomically publish candidate schedule version. |

### 2.6 Publishing, Exports & Reporting (`/schedules/{id}/export`, `/reports`)
| Method | Path | Role Required | Description |
|---|---|---|---|
| `GET` | `/schedules/{id}/export/csv` | Authenticated | Download RFC-4180 CSV with CSV injection escaping. |
| `GET` | `/schedules/{id}/export/pdf` | Authenticated | Download publication-ready PDF timetable grid. |
| `GET` | `/schedules/{id}/export/excel` | Authenticated | Download formatted Excel (.xlsx) workbook. |
| `GET` | `/cycles/{id}/reports/distribution` | Authenticated | Retrieve exam load distribution report across sessions. |
| `GET` | `/cycles/{id}/reports/conflicts` | Admin, Coordinator | Retrieve unresolved conflict report. |

### 2.7 Demonstration & Development (`/dev`)
| Method | Path | Role Required | Description |
|---|---|---|---|
| `GET` | `/dev/status` | Admin | Check demonstration seeding availability. |
| `POST` | `/dev/seed-demo` | Admin | Populate demo departments, subjects, students, cycle, and graph. |

---

## 3. Sample cURL Commands

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@univ.edu", "password": "AdminPass123!"}'
```

### Build Conflict Graph Snapshot
```bash
curl -X POST http://localhost:8000/api/v1/cycles/1b6f5cdc-0e2f-4c00-8eac-fa4245456684/graph/build \
  -H "Authorization: Bearer <TOKEN>"
```

### Generate Timetable with DSATUR
```bash
curl -X POST http://localhost:8000/api/v1/cycles/1b6f5cdc-0e2f-4c00-8eac-fa4245456684/schedule/generate \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "dsatur", "deterministic": true, "preserveLockedExams": true}'
```

### Download Published Schedule CSV
```bash
curl -X GET http://localhost:8000/api/v1/schedules/<VERSION_ID>/export/csv \
  -H "Authorization: Bearer <TOKEN>" \
  -o timetable.csv
```
