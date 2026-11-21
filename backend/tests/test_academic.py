from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import EntityStatus
from tests.conftest import make_auth_user


def test_academic_departments_crud(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="dept_admin@univ.edu")
    _, coord_headers = make_auth_user(db_session, role="coordinator", email="dept_coord@univ.edu")

    # 1. Non-admin forbidden to create department
    resp = client.post(
        "/api/v1/academic/departments",
        json={"code": "PHY", "name": "Department of Physics"},
        headers=coord_headers,
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"

    # 2. Admin creates department
    resp = client.post(
        "/api/v1/academic/departments",
        json={"code": "PHY", "name": "Department of Physics"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    dept_id = resp.json()["id"]
    assert resp.json()["code"] == "PHY"
    assert resp.json()["status"] == EntityStatus.ACTIVE.value

    # 3. Duplicate department code rejected
    resp_dup = client.post(
        "/api/v1/academic/departments",
        json={"code": "phy", "name": "Duplicate Physics"},
        headers=admin_headers,
    )
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error"]["code"] == "DUPLICATE_DEPARTMENT_CODE"

    # 4. Get departments paginated & search
    resp_list = client.get("/api/v1/academic/departments?search=Physics", headers=coord_headers)
    assert resp_list.status_code == 200
    assert resp_list.json()["total"] >= 1
    assert any(d["id"] == dept_id for d in resp_list.json()["items"])

    # 5. Update department
    resp_update = client.patch(
        f"/api/v1/academic/departments/{dept_id}",
        json={"name": "Department of Applied Physics"},
        headers=admin_headers,
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["name"] == "Department of Applied Physics"

    # 6. Archive department
    resp_arch = client.delete(f"/api/v1/academic/departments/{dept_id}", headers=admin_headers)
    assert resp_arch.status_code == 200
    assert resp_arch.json()["status"] == EntityStatus.ARCHIVED.value


def test_academic_years_and_semesters_crud(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="ay_admin@univ.edu")

    # 1. Invalid date range (end_date < start_date) rejected by schema validation
    resp_invalid = client.post(
        "/api/v1/academic/years",
        json={"name": "2028-2029", "startDate": "2029-01-01", "endDate": "2028-01-01"},
        headers=admin_headers,
    )
    assert resp_invalid.status_code == 422

    # 2. Create valid academic year
    resp_ay = client.post(
        "/api/v1/academic/years",
        json={"name": "2028-2029", "startDate": "2028-08-01", "endDate": "2029-06-30"},
        headers=admin_headers,
    )
    assert resp_ay.status_code == 201
    ay_id = resp_ay.json()["id"]

    # 3. Duplicate academic year rejected
    resp_dup_ay = client.post(
        "/api/v1/academic/years",
        json={"name": "2028-2029", "startDate": "2028-08-01", "endDate": "2029-06-30"},
        headers=admin_headers,
    )
    assert resp_dup_ay.status_code == 409
    assert resp_dup_ay.json()["error"]["code"] == "DUPLICATE_ACADEMIC_YEAR"

    # 4. Create semester
    resp_sem = client.post(
        "/api/v1/academic/semesters",
        json={"academicYearId": ay_id, "name": "Term 1", "number": 1},
        headers=admin_headers,
    )
    assert resp_sem.status_code == 201
    sem_id = resp_sem.json()["id"]

    # 5. Duplicate semester number in same academic year rejected
    resp_dup_sem = client.post(
        "/api/v1/academic/semesters",
        json={"academicYearId": ay_id, "name": "Term 1 Alternate", "number": 1},
        headers=admin_headers,
    )
    assert resp_dup_sem.status_code == 409
    assert resp_dup_sem.json()["error"]["code"] == "DUPLICATE_SEMESTER"

    # 6. Get semesters filtered by academic year
    resp_sems = client.get(
        f"/api/v1/academic/semesters?academicYearId={ay_id}", headers=admin_headers
    )
    assert resp_sems.status_code == 200
    assert any(s["id"] == sem_id for s in resp_sems.json()["items"])


def test_programs_crud(client: TestClient, db_session: Session):
    _, admin_headers = make_auth_user(db_session, role="admin", email="prog_admin@univ.edu")

    # Create dept first
    resp_dept = client.post(
        "/api/v1/academic/departments",
        json={"code": "BIO", "name": "Biotechnology"},
        headers=admin_headers,
    )
    dept_id = resp_dept.json()["id"]

    # Create program
    resp_prog = client.post(
        "/api/v1/academic/programs",
        json={
            "departmentId": dept_id,
            "code": "BTECH-BIO",
            "name": "B.Tech in Biotechnology",
        },
        headers=admin_headers,
    )
    assert resp_prog.status_code == 201
    prog_id = resp_prog.json()["id"]

    # Duplicate program code rejected
    resp_dup = client.post(
        "/api/v1/academic/programs",
        json={
            "departmentId": dept_id,
            "code": "BTECH-BIO",
            "name": "Duplicate Bio",
        },
        headers=admin_headers,
    )
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error"]["code"] == "DUPLICATE_PROGRAM_CODE"

    # Get programs filtered by department
    resp_progs = client.get(
        f"/api/v1/academic/programs?departmentId={dept_id}", headers=admin_headers
    )
    assert resp_progs.status_code == 200
    assert any(p["id"] == prog_id for p in resp_progs.json()["items"])
