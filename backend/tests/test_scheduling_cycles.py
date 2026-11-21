from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.academic import AcademicYear, Department, Subject
from app.models.enums import CycleStatus, EntityStatus
from app.services.slot_service import slot_service
from tests.conftest import make_auth_user


def setup_cycle_test_base(db: Session, admin_headers: dict):
    # Department
    dept = Department(code="PHYS", name="Physics", status=EntityStatus.ACTIVE)
    db.add(dept)
    db.flush()

    # Academic Year
    ay = AcademicYear(
        name="2026-2027-CYCLE",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 6, 30),
        status=EntityStatus.ACTIVE,
    )
    db.add(ay)
    db.flush()

    # Subjects
    s1 = Subject(
        subject_code="PHYS101",
        subject_name="Mechanics",
        department_id=dept.id,
        semester=1,
        credits=3.0,
        default_duration_minutes=180,
        priority=1,
        status=EntityStatus.ACTIVE,
    )
    s2 = Subject(
        subject_code="PHYS102",
        subject_name="Electromagnetism",
        department_id=dept.id,
        semester=1,
        credits=3.0,
        default_duration_minutes=180,
        priority=2,
        status=EntityStatus.ACTIVE,
    )
    db.add_all([s1, s2])
    db.commit()
    db.refresh(dept)
    db.refresh(ay)
    db.refresh(s1)
    db.refresh(s2)

    return dept, ay, s1, s2


# ==============================================================================
# 1. Cycle Management & Legal State Machine Tests (Task P5.1)
# ==============================================================================
def test_cycle_crud_and_status_transitions(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="cycle_admin@univ.edu")
    _, ay, _, _ = setup_cycle_test_base(db_session, admin_headers)

    # 1. Create cycle
    resp = client.post(
        "/api/v1/cycles",
        json={
            "name": "Summer 2026 Physics Exam",
            "academicYearId": ay.id,
            "startDate": "2026-06-10",
            "endDate": "2026-06-20",
            "timezone": "UTC",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    cycle_data = resp.json()
    cycle_id = cycle_data["id"]
    assert cycle_data["status"] == CycleStatus.DRAFT.value
    assert (cycle_data.get("dataVersion") or cycle_data.get("data_version")) == 1

    # 2. Illegal direct transition: Draft -> Published (must follow state machine)
    resp_illegal = client.patch(
        f"/api/v1/cycles/{cycle_id}",
        json={"status": CycleStatus.PUBLISHED.value},
        headers=admin_headers,
    )
    assert resp_illegal.status_code == 422
    assert resp_illegal.json()["error"]["code"] == "INVALID_CYCLE_STATE_TRANSITION"

    # 3. Legal transition: Draft -> Generated -> Reviewed -> Published
    resp_gen = client.patch(
        f"/api/v1/cycles/{cycle_id}",
        json={"status": CycleStatus.GENERATED.value},
        headers=admin_headers,
    )
    assert resp_gen.status_code == 200
    assert resp_gen.json()["status"] == CycleStatus.GENERATED.value

    resp_rev = client.patch(
        f"/api/v1/cycles/{cycle_id}",
        json={"status": CycleStatus.REVIEWED.value},
        headers=admin_headers,
    )
    assert resp_rev.status_code == 200
    assert resp_rev.json()["status"] == CycleStatus.REVIEWED.value

    resp_pub = client.patch(
        f"/api/v1/cycles/{cycle_id}",
        json={"status": CycleStatus.PUBLISHED.value},
        headers=admin_headers,
    )
    assert resp_pub.status_code == 200
    assert resp_pub.json()["status"] == CycleStatus.PUBLISHED.value

    # 4. Legal transition to Archived (terminal state)
    resp_arch = client.delete(f"/api/v1/cycles/{cycle_id}", headers=admin_headers)
    assert resp_arch.status_code == 200
    assert resp_arch.json()["status"] == CycleStatus.ARCHIVED.value

    # 5. Cannot transition out of Archived
    resp_out = client.patch(
        f"/api/v1/cycles/{cycle_id}",
        json={"status": CycleStatus.DRAFT.value},
        headers=admin_headers,
    )
    assert resp_out.status_code == 422
    assert resp_out.json()["error"]["code"] == "INVALID_CYCLE_STATE_TRANSITION"


# ==============================================================================
# 2. Configuration Validation Tests (Tasks P5.2, P5.3)
# ==============================================================================
def test_cycle_configuration_validation_rules(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="cfg_admin@univ.edu")
    _, ay, _, _ = setup_cycle_test_base(db_session, admin_headers)

    # 1. Reject overlapping sessions (e.g. Morning 09:00-13:00 and Afternoon 12:00-15:00)
    resp_overlap = client.post(
        "/api/v1/cycles",
        json={
            "name": "Overlapping Sessions Cycle",
            "academicYearId": ay.id,
            "startDate": "2026-06-10",
            "endDate": "2026-06-20",
            "configuration": {
                "startDate": "2026-06-10",
                "endDate": "2026-06-20",
                "sessions": [
                    {"label": "Morning", "startTime": "09:00", "endTime": "13:00"},
                    {"label": "Afternoon", "startTime": "12:00", "endTime": "15:00"},
                ],
            },
        },
        headers=admin_headers,
    )
    assert resp_overlap.status_code == 422

    # 2. Reject endDate < startDate
    resp_dates = client.post(
        "/api/v1/cycles",
        json={
            "name": "Invalid Dates Cycle",
            "academicYearId": ay.id,
            "startDate": "2026-06-20",
            "endDate": "2026-06-10",
        },
        headers=admin_headers,
    )
    assert resp_dates.status_code == 422


# ==============================================================================
# 3. Exam Synchronization & Overrides (Tasks P5.4, P5.5)
# ==============================================================================
def test_cycle_exam_synchronization_and_overrides(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="sync_admin@univ.edu")
    _, ay, s1, s2 = setup_cycle_test_base(db_session, admin_headers)

    resp_c = client.post(
        "/api/v1/cycles",
        json={
            "name": "Exam Sync Cycle",
            "academicYearId": ay.id,
            "startDate": "2026-06-10",
            "endDate": "2026-06-20",
        },
        headers=admin_headers,
    )
    cycle_id = resp_c.json()["id"]

    # Sync exams from active subjects
    resp_sync = client.post(f"/api/v1/cycles/{cycle_id}/exams/sync", headers=admin_headers)
    assert resp_sync.status_code == 200
    sync_data = resp_sync.json()
    synced_count = sync_data.get("synced_exams_count") if "synced_exams_count" in sync_data else sync_data.get("syncedExamsCount")
    assert synced_count >= 2

    # List exams
    resp_exams = client.get(f"/api/v1/cycles/{cycle_id}/exams", headers=admin_headers)
    assert resp_exams.status_code == 200
    exams = resp_exams.json()["items"]
    assert len(exams) >= 2

    exam_s1 = next(e for e in exams if e.get("subject_id") == s1.id or e.get("subjectId") == s1.id)
    exam_id = exam_s1["id"]

    # Override exam duration and priority (Task P5.5)
    resp_override = client.patch(
        f"/api/v1/cycles/{cycle_id}/exams/{exam_id}",
        json={
            "durationMinutes": 120,
            "priority": 5,
            "preferredDates": ["2026-06-12"],
            "restrictedDates": ["2026-06-15"],
        },
        headers=admin_headers,
    )
    assert resp_override.status_code == 200
    ov_data = resp_override.json()
    dur = ov_data.get("duration_minutes") if "duration_minutes" in ov_data else ov_data.get("durationMinutes")
    assert dur == 120


# ==============================================================================
# 4. Slot Generation Pure Function & PRD §FR-06 Example (Tasks P5.6, P5.7, P5.8)
# ==============================================================================
def test_slot_generation_prd_example():
    """
    Validates PRD §FR-06 Example:
    - 10 June to 20 June 2026 (11 calendar days).
    - Mon-Sat allowed (exam_days_of_week: [1, 2, 3, 4, 5, 6]), Sunday excluded.
    - 2 daily sessions (Morning 09:00-12:00, Afternoon 14:00-17:00).
    - 1 holiday (e.g. 2026-06-17).
    """
    config = {
        "examDaysOfWeek": [1, 2, 3, 4, 5, 6],
        "holidays": ["2026-06-17"],
        "sessions": [
            {"label": "Morning", "startTime": "09:00", "endTime": "12:00", "enabled": True},
            {"label": "Afternoon", "startTime": "14:00", "endTime": "17:00", "enabled": True},
        ],
        "specialRestrictions": [
            {"date": "2026-06-18", "sessionLabel": "Afternoon", "enabled": False}
        ],
    }

    start_d = date(2026, 6, 10)  # Wednesday
    end_d = date(2026, 6, 20)    # Saturday (11 calendar days total)

    slots = slot_service.generate_slots(start_date=start_d, end_date=end_d, config=config)

    # In 10 June to 20 June:
    # Days: Wed 10, Thu 11, Fri 12, Sat 13, Sun 14 (excluded), Mon 15, Tue 16, Wed 17 (holiday), Thu 18, Fri 19, Sat 20
    # Total active exam days: 11 - 1 (Sunday) - 1 (Holiday) = 9 days.
    # 9 days * 2 sessions/day = 18 total slots.
    assert len(slots) == 18

    # Verify no Sunday slots (June 14, 2026 is Sunday)
    assert all(s["date"] != date(2026, 6, 14) for s in slots)

    # Verify no Holiday slots (June 17, 2026 is Holiday)
    assert all(s["date"] != date(2026, 6, 17) for s in slots)

    # Verify per-date special restriction: June 18 Afternoon is disabled
    june18_afternoon = next(
        s for s in slots if s["date"] == date(2026, 6, 18) and s["session_label"] == "Afternoon"
    )
    assert june18_afternoon["enabled"] is False

    # Verify deterministic ordering and continuous slot_index (Task P5.8)
    for i, s in enumerate(slots):
        assert s["slot_index"] == i
        assert s["duration_minutes"] == 180


# ==============================================================================
# 5. Slot Persistence, Id Stability & Capacity Summary (Tasks P5.9, P5.11, P5.12)
# ==============================================================================
def test_slot_persistence_id_stability_and_capacity_summary(
    client: TestClient, db_session: Session
):
    _, admin_headers = make_auth_user(db_session, role="admin", email="slot_admin@univ.edu")
    _, ay, s1, s2 = setup_cycle_test_base(db_session, admin_headers)

    resp_c = client.post(
        "/api/v1/cycles",
        json={
            "name": "Slot Persistence Cycle",
            "academicYearId": ay.id,
            "startDate": "2026-06-10",
            "endDate": "2026-06-12",
        },
        headers=admin_headers,
    )
    cycle_id = resp_c.json()["id"]

    # 1. Generate slots
    resp_gen = client.post(f"/api/v1/cycles/{cycle_id}/slots/generate", headers=admin_headers)
    assert resp_gen.status_code == 200
    first_slots = resp_gen.json()
    assert len(first_slots) > 0
    first_slot_ids = [s["id"] for s in first_slots]

    # 2. Id Stability Test (Task P5.9): Re-generating identical slots preserves slot IDs
    resp_regen = client.post(f"/api/v1/cycles/{cycle_id}/slots/generate", headers=admin_headers)
    assert resp_regen.status_code == 200
    second_slots = resp_regen.json()
    second_slot_ids = [s["id"] for s in second_slots]
    assert first_slot_ids == second_slot_ids

    # 3. Capacity summary & feasibility pre-check (Task P5.11)
    client.post(f"/api/v1/cycles/{cycle_id}/exams/sync", headers=admin_headers)
    resp_cap = client.get(f"/api/v1/cycles/{cycle_id}/slots/capacity-summary", headers=admin_headers)
    assert resp_cap.status_code == 200
    cap_data = resp_cap.json()

    tot = cap_data.get("total_slots") if "total_slots" in cap_data else cap_data.get("totalSlots")
    en = cap_data.get("enabled_slots") if "enabled_slots" in cap_data else cap_data.get("enabledSlots")
    exams_cnt = cap_data.get("exam_count") if "exam_count" in cap_data else cap_data.get("examCount")
    feasible = cap_data.get("is_feasible_pre_check") if "is_feasible_pre_check" in cap_data else cap_data.get("isFeasiblePreCheck")

    assert tot > 0
    assert en > 0
    assert exams_cnt == 2
    assert feasible is True

    # 4. Duration compatibility helper (Task P5.12)
    assert slot_service.fits(120, 180) is True
    assert slot_service.fits(180, 180) is True
    assert slot_service.fits(240, 180) is False
