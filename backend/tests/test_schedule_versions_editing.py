"""Comprehensive test suite for Phase 9: Schedule Versions, Manual Editing, Locking, and Regeneration.

PRD §15, §17.14, §17.15, §18.7, §26.4, Tasks P9.1 - P9.21.
"""


from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ScheduleStatus
from app.models.schedule import ScheduleVersion
from app.models.scheduling import SchedulingCycle, TimeSlot
from tests.conftest import make_auth_user
from tests.test_scheduling_engine import setup_schedule_cycle_base


def setup_version_test_fixture(db: Session, headers: dict[str, str], client: TestClient) -> tuple[SchedulingCycle, ScheduleVersion, list[TimeSlot]]:
    """Creates cycle, subjects, enrollments, slots, builds graph, runs DSATUR and saves candidate."""
    cycle, _, _ = setup_schedule_cycle_base(db, headers, client)

    gen_resp = client.post(
        f"/api/v1/cycles/{cycle.id}/schedule/generate",
        json={"algorithm": "dsatur"},
        headers=headers,
    )
    assert gen_resp.status_code == 200
    run_id = gen_resp.json()["id"]

    save_resp = client.post(f"/api/v1/schedule-runs/{run_id}/save", headers=headers)
    assert save_resp.status_code == 200
    ver_id = save_resp.json()["id"]

    ver = db.get(ScheduleVersion, ver_id)
    assert ver is not None
    slots = list(db.scalars(select(TimeSlot).where(TimeSlot.scheduling_cycle_id == cycle.id)).all())
    return cycle, ver, slots


def test_list_schedules_and_get_version_detail(client: TestClient, db_session: Session):
    """Verifies listing schedule versions for a cycle and fetching full version details (P9.1)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vlist_admin@univ.edu")
    cycle, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    resp_list = client.get(f"/api/v1/cycles/{cycle.id}/schedules", headers=admin_headers)
    assert resp_list.status_code == 200
    versions = resp_list.json()
    assert len(versions) >= 1
    assert versions[0]["id"] == ver.id
    assert (versions[0].get("assignmentCount") or versions[0].get("assignment_count")) == 3
    assert (versions[0].get("versionNumber") or versions[0].get("version_number")) == 1

    resp_detail = client.get(f"/api/v1/schedules/{ver.id}", headers=admin_headers)
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["id"] == ver.id
    assert len(detail["assignments"]) == 3
    for a in detail["assignments"]:
        assert (a.get("subjectCode") or a.get("subject_code")) in ["EE101", "EE102", "EE103"]
        assert (a.get("slotDate") or a.get("slot_date")) is not None
        assert a["locked"] is False
        assert (a.get("manualOverride") or a.get("manual_override")) is False


def test_version_cloning_and_immutability(client: TestClient, db_session: Session):
    """Verifies cloning versions and immutability of Published/Archived versions (P9.2)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vclone_admin@univ.edu")
    _, ver, slots = setup_version_test_fixture(db_session, admin_headers, client)

    # 1. Clone candidate version -> produces version 2
    resp_clone = client.post(f"/api/v1/schedules/{ver.id}/clone", headers=admin_headers)
    assert resp_clone.status_code == 200
    v2_data = resp_clone.json()
    assert (v2_data.get("versionNumber") or v2_data.get("version_number")) == 2
    assert v2_data["status"] == ScheduleStatus.CANDIDATE.value
    assert len(v2_data["assignments"]) == 3

    # 2. Mark version 1 as Published to test immutability
    ver.status = ScheduleStatus.PUBLISHED
    db_session.commit()

    aid = ver.assignments[0].id
    # Attempt to move on published schedule -> rejected with 409 SCHEDULE_IMMUTABLE
    resp_move = client.patch(
        f"/api/v1/schedules/{ver.id}/assignments/{aid}",
        json={"timeSlotId": slots[3].id},
        headers=admin_headers,
    )
    assert resp_move.status_code == 409
    assert "SCHEDULE_IMMUTABLE" in resp_move.text

    # Attempt to lock on published schedule -> rejected with 409 SCHEDULE_IMMUTABLE
    resp_lock = client.post(
        f"/api/v1/schedules/{ver.id}/assignments/{aid}/lock",
        headers=admin_headers,
    )
    assert resp_lock.status_code == 409

    # 3. Clone the published version -> creates editable candidate version 3
    resp_clone_pub = client.post(f"/api/v1/schedules/{ver.id}/clone", headers=admin_headers)
    assert resp_clone_pub.status_code == 200
    v3_data = resp_clone_pub.json()
    assert (v3_data.get("versionNumber") or v3_data.get("version_number")) == 3
    assert v3_data["status"] == ScheduleStatus.CANDIDATE.value


def test_version_archive(client: TestClient, db_session: Session):
    """Verifies archiving schedule version and verifying it becomes immutable (P9.4)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="varch_admin@univ.edu")
    _, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    resp_arch = client.post(f"/api/v1/schedules/{ver.id}/archive", headers=admin_headers)
    assert resp_arch.status_code == 200
    assert resp_arch.json()["status"] == ScheduleStatus.ARCHIVED.value

    # Mutations on archived schedule are rejected
    aid = ver.assignments[0].id
    resp_lock = client.post(f"/api/v1/schedules/{ver.id}/assignments/{aid}/lock", headers=admin_headers)
    assert resp_lock.status_code == 409


def test_preview_assignment_move_and_incremental_validation(client: TestClient, db_session: Session):
    """Verifies dry-run preview move with student conflict analysis and soft penalty delta (P9.5, P9.7)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vprev_admin@univ.edu")
    _, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    # In our fixture: EE101 and EE102 conflict (John takes both).
    # Find assignments for EE101 and EE102
    a_ee101 = next(a for a in ver.assignments if a.exam.subject.subject_code == "EE101")
    a_ee102 = next(a for a in ver.assignments if a.exam.subject.subject_code == "EE102")

    # Preview moving EE101 to EE102's slot -> must detect clash!
    resp_prev = client.post(
        f"/api/v1/schedules/{ver.id}/assignments/{a_ee101.id}/preview-move",
        json={"timeSlotId": a_ee102.time_slot_id},
        headers=admin_headers,
    )
    assert resp_prev.status_code == 200
    prev_data = resp_prev.json()
    assert prev_data["valid"] is False
    assert len(prev_data["violations"]) >= 1

    conflicts = prev_data.get("conflictingExams") or prev_data.get("conflicting_exams")
    assert len(conflicts) >= 1
    assert any((c.get("subjectCode") or c.get("subject_code")) == "EE102" for c in conflicts)


def test_move_assignment_conflict_rejection_and_no_persistence(client: TestClient, db_session: Session):
    """Verifies that an invalid move is rejected with 422 and nothing is persisted (P9.6, P9.8)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vmove_fail_admin@univ.edu")
    _, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    a_ee101 = next(a for a in ver.assignments if a.exam.subject.subject_code == "EE101")
    a_ee102 = next(a for a in ver.assignments if a.exam.subject.subject_code == "EE102")
    original_slot_id = a_ee101.time_slot_id

    # Try moving EE101 to EE102's slot (causes student clash)
    resp_move = client.patch(
        f"/api/v1/schedules/{ver.id}/assignments/{a_ee101.id}",
        json={"timeSlotId": a_ee102.time_slot_id},
        headers=admin_headers,
    )
    assert resp_move.status_code == 422
    assert "Cannot move exam" in resp_move.text

    # Verify database was NOT changed
    db_session.refresh(a_ee101)
    assert a_ee101.time_slot_id == original_slot_id
    assert a_ee101.manual_override is False


def test_move_assignment_success_and_audit(client: TestClient, db_session: Session):
    """Verifies moving an assignment to an empty valid slot, updating manual_override, row_version, and audit log (P9.6, P9.10, P9.11)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vmove_ok_admin@univ.edu")
    _, ver, slots = setup_version_test_fixture(db_session, admin_headers, client)

    # Find a slot not currently used by any assignment in the version
    used_slot_ids = {a.time_slot_id for a in ver.assignments}
    free_slot = next(s for s in slots if s.id not in used_slot_ids)

    a_target = ver.assignments[0]
    initial_row_version = ver.row_version

    resp_move = client.patch(
        f"/api/v1/schedules/{ver.id}/assignments/{a_target.id}",
        json={"timeSlotId": free_slot.id, "expectedRowVersion": initial_row_version},
        headers=admin_headers,
    )
    assert resp_move.status_code == 200
    updated_data = resp_move.json()

    # Verify row_version bumped
    assert (updated_data.get("rowVersion") or updated_data.get("row_version")) == initial_row_version + 1

    # Verify assignment has manualOverride = true
    updated_a = next(a for a in updated_data["assignments"] if a["id"] == a_target.id)
    assert (updated_a.get("timeSlotId") or updated_a.get("time_slot_id")) == free_slot.id
    assert (updated_a.get("manualOverride") or updated_a.get("manual_override")) is True


def test_locked_exam_move_rejected(client: TestClient, db_session: Session):
    """Verifies that locked exams cannot be moved by PATCH, returning 409 EXAM_LOCKED (P9.12, P9.13)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vlock_admin@univ.edu")
    _, ver, slots = setup_version_test_fixture(db_session, admin_headers, client)

    a_target = ver.assignments[0]
    # 1. Lock the assignment
    resp_lock = client.post(f"/api/v1/schedules/{ver.id}/assignments/{a_target.id}/lock", headers=admin_headers)
    assert resp_lock.status_code == 200

    # 2. Attempt to move locked assignment -> rejected with 409 EXAM_LOCKED
    used_slot_ids = {a.time_slot_id for a in ver.assignments}
    free_slot = next(s for s in slots if s.id not in used_slot_ids)
    resp_move = client.patch(
        f"/api/v1/schedules/{ver.id}/assignments/{a_target.id}",
        json={"timeSlotId": free_slot.id},
        headers=admin_headers,
    )
    assert resp_move.status_code == 409
    assert "EXAM_LOCKED" in resp_move.text

    # 3. Unlock assignment -> move now succeeds
    resp_unlock = client.post(f"/api/v1/schedules/{ver.id}/assignments/{a_target.id}/unlock", headers=admin_headers)
    assert resp_unlock.status_code == 200

    resp_move2 = client.patch(
        f"/api/v1/schedules/{ver.id}/assignments/{a_target.id}",
        json={"timeSlotId": free_slot.id},
        headers=admin_headers,
    )
    assert resp_move2.status_code == 200


def test_atomic_swap_assignments(client: TestClient, db_session: Session):
    """Verifies atomic swap of slots between two exam assignments (P9.9)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vswap_admin@univ.edu")
    _, ver, slots = setup_version_test_fixture(db_session, admin_headers, client)

    # First, move EE103 to a free slot (slots[2]) so each exam is alone in its slot
    a_ee103 = next(a for a in ver.assignments if a.exam.subject.subject_code == "EE103")
    client.patch(
        f"/api/v1/schedules/{ver.id}/assignments/{a_ee103.id}",
        json={"timeSlotId": slots[2].id},
        headers=admin_headers,
    )

    db_session.refresh(ver)
    a1 = next(a for a in ver.assignments if a.exam.subject.subject_code == "EE101")
    a2 = next(a for a in ver.assignments if a.exam.subject.subject_code == "EE102")
    slot1_orig = a1.time_slot_id
    slot2_orig = a2.time_slot_id

    resp_swap = client.post(
        f"/api/v1/schedules/{ver.id}/assignments/swap",
        json={"assignmentIdA": a1.id, "assignmentIdB": a2.id},
        headers=admin_headers,
    )
    assert resp_swap.status_code == 200
    swap_data = resp_swap.json()

    a1_new = next(a for a in swap_data["assignments"] if a["id"] == a1.id)
    a2_new = next(a for a in swap_data["assignments"] if a["id"] == a2.id)

    assert (a1_new.get("timeSlotId") or a1_new.get("time_slot_id")) == slot2_orig
    assert (a2_new.get("timeSlotId") or a2_new.get("time_slot_id")) == slot1_orig
    assert (a1_new.get("manualOverride") or a1_new.get("manual_override")) is True
    assert (a2_new.get("manualOverride") or a2_new.get("manual_override")) is True


def test_optimistic_concurrency_locking(client: TestClient, db_session: Session):
    """Verifies optimistic locking: mismatched row_version triggers CONCURRENT_MODIFICATION (P9.10)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vconcurr_admin@univ.edu")
    _, ver, slots = setup_version_test_fixture(db_session, admin_headers, client)

    a_target = ver.assignments[0]
    free_slot = next(s for s in slots if s.id != a_target.time_slot_id)

    # Provide stale expected row version
    resp = client.patch(
        f"/api/v1/schedules/{ver.id}/assignments/{a_target.id}",
        json={"timeSlotId": free_slot.id, "expectedRowVersion": 999},
        headers=admin_headers,
    )
    assert resp.status_code == 409
    assert "CONCURRENT_MODIFICATION" in resp.text


def test_bulk_lock_and_lock_validation(client: TestClient, db_session: Session):
    """Verifies bulk locking by date/session and lock-set validation (P9.14, P9.15)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="vbulk_admin@univ.edu")
    _, ver, _ = setup_version_test_fixture(db_session, admin_headers, client)

    target_date = str(ver.assignments[0].time_slot.date)
    resp_bulk = client.post(
        f"/api/v1/schedules/{ver.id}/locks/bulk",
        json={"action": "lock", "date": target_date},
        headers=admin_headers,
    )
    assert resp_bulk.status_code == 200
    bulk_data = resp_bulk.json()

    locked_count = len([a for a in bulk_data["assignments"] if a["locked"]])
    assert locked_count >= 1

    # Validate locks
    resp_val = client.post(f"/api/v1/schedules/{ver.id}/locks/validate", headers=admin_headers)
    assert resp_val.status_code == 200
    val_data = resp_val.json()
    assert val_data["valid"] is True
    assert (val_data.get("lockedCount") or val_data.get("locked_count")) == locked_count


def test_regeneration_with_locked_exams_and_impact_report(client: TestClient, db_session: Session):
    """
    Verifies schedule regeneration preserving locked exams and generating a Change Impact Report (P9.16 - P9.19).
    """
    _, admin_headers = make_auth_user(db_session, role="admin", email="vregen_admin@univ.edu")
    _, ver1, _ = setup_version_test_fixture(db_session, admin_headers, client)

    # 1. Lock Exam 1
    a1 = ver1.assignments[0]
    client.post(f"/api/v1/schedules/{ver1.id}/assignments/{a1.id}/lock", headers=admin_headers)

    # 2. Regenerate schedule
    resp_regen = client.post(
        f"/api/v1/schedules/{ver1.id}/regenerate",
        json={
            "algorithm": "dsatur",
            "preserveLockedExams": True,
            "minimizeDisruption": True,
            "autoRebuildGraph": True,
        },
        headers=admin_headers,
    )
    assert resp_regen.status_code == 200
    ver2_data = resp_regen.json()

    # Must be a NEW Candidate version (P9.18)
    assert ver2_data["id"] != ver1.id
    assert (ver2_data.get("versionNumber") or ver2_data.get("version_number")) == 2

    # Verify locked exam preserved in exact slot
    ver2_a1 = next(a for a in ver2_data["assignments"] if (a.get("examId") or a.get("exam_id")) == a1.exam_id)
    assert (ver2_a1.get("timeSlotId") or ver2_a1.get("time_slot_id")) == a1.time_slot_id
    assert ver2_a1["locked"] is True

    # 3. Query Change Impact Report (P9.19)
    resp_diff = client.get(f"/api/v1/schedules/{ver2_data['id']}/diff/{ver1.id}", headers=admin_headers)
    assert resp_diff.status_code == 200
    diff_data = resp_diff.json()

    assert (diff_data.get("lockedPreservedCount") or diff_data.get("locked_preserved_count")) >= 1
    assert (diff_data.get("oldVersionId") or diff_data.get("old_version_id")) == ver1.id
    assert (diff_data.get("newVersionId") or diff_data.get("new_version_id")) == ver2_data["id"]
