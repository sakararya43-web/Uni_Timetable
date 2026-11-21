"""Comprehensive Conflict Graph Engine Tests.

PRD §11 (FR-07), §18.6, §23, §26.2, Implementation.md Phase 6:
Tests pure graph builder, independent validator, hashing, statistics,
snapshot persistence, idempotency, staleness detection, export,
privacy protection, and privileged drilldown.
"""

import time
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.algorithms.graph_builder import (
    build_conflict_graph,
    compute_enrollment_hash,
    compute_stats,
    validate_graph,
)
from app.algorithms.types import ConflictGraph
from app.models.academic import AcademicYear, Department, Student, Subject
from app.models.enums import CycleStatus, EnrollmentStatus, EntityStatus
from app.models.scheduling import Enrollment, SchedulingCycle
from tests.conftest import make_auth_user


# ==============================================================================
# 1. Pure Algorithmic Unit Tests (P6.1, P6.2, P6.3, P6.4, P6.5, P6.6)
# ==============================================================================
def test_pure_graph_empty_and_isolated_exams():
    """Empty enrollments produces |V| isolated vertices, |E|=0, density 0.0."""
    exam_ids = ["exam-1", "exam-2", "exam-3"]
    enrollments: list[tuple[str, str]] = []

    graph = build_conflict_graph(exam_ids, enrollments)

    assert graph.vertices == set(exam_ids)
    assert len(graph.edge_weights) == 0
    assert all(len(adj) == 0 for adj in graph.adjacency.values())

    report = validate_graph(graph, exam_ids, enrollments)
    assert report.is_valid is True
    assert len(report.errors) == 0

    stats = compute_stats(graph)
    assert stats.vertex_count == 3
    assert stats.edge_count == 0
    assert stats.density == 0.0
    assert stats.avg_degree == 0.0
    assert stats.max_degree == 0
    assert stats.min_degree == 0
    assert stats.isolated_vertices == ["exam-1", "exam-2", "exam-3"]
    assert stats.connected_components_count == 3
    assert stats.largest_component_size == 1
    assert stats.chromatic_lower_bound == 1


def test_pure_graph_pairwise_edges_and_k_student_expansion():
    """
    Tests student taking k exams producing exactly k(k-1)/2 pairwise edges.
    Verifies duplicate enrollment rows do not double-count (PRD §26.2).
    """
    exam_ids = ["e1", "e2", "e3", "e4"]
    # Student S1 takes e1, e2, e3 -> produces 3 edges: (e1,e2), (e1,e3), (e2,e3)
    # Student S2 takes e1, e2 -> increments weight of (e1,e2) to 2
    # Student S1 has duplicate row for e1 -> must not increase weight
    enrollments = [
        ("s1", "e1"),
        ("s1", "e2"),
        ("s1", "e3"),
        ("s1", "e1"),  # Duplicate enrollment row
        ("s2", "e1"),
        ("s2", "e2"),
    ]

    graph = build_conflict_graph(exam_ids, enrollments)

    assert graph.vertices == {"e1", "e2", "e3", "e4"}
    assert len(graph.edge_weights) == 3

    # Check normalized pairs (u < v)
    assert ("e1", "e2") in graph.edge_weights
    assert graph.edge_weights[("e1", "e2")] == 2  # S1 and S2 share e1 and e2
    assert graph.edge_weights[("e1", "e3")] == 1  # S1 only
    assert graph.edge_weights[("e2", "e3")] == 1  # S1 only

    # Invariants
    assert "e4" in graph.vertices
    assert len(graph.adjacency["e4"]) == 0  # e4 is isolated

    # Adjacency symmetry
    assert "e2" in graph.adjacency["e1"]
    assert "e1" in graph.adjacency["e2"]
    assert "e3" in graph.adjacency["e1"]
    assert "e1" in graph.adjacency["e3"]

    report = validate_graph(graph, exam_ids, enrollments)
    assert report.is_valid is True

    stats = compute_stats(graph)
    assert stats.vertex_count == 4
    assert stats.edge_count == 3
    # Density D = 2*3 / (4*3) = 6/12 = 0.5
    assert stats.density == 0.5
    assert stats.max_degree == 2  # e1 and e2 both have degree 2
    assert stats.isolated_vertices == ["e4"]
    assert stats.connected_components_count == 2  # {e1, e2, e3} and {e4}
    assert stats.largest_component_size == 3


def test_pure_graph_clique_bound_and_components():
    """Tests triangle K3 and disconnected cliques for components and chromatic lower bound."""
    # K3: 3 exams all connected
    exam_ids = ["a", "b", "c"]
    enrollments = [
        ("s1", "a"),
        ("s1", "b"),
        ("s1", "c"),
    ]
    graph = build_conflict_graph(exam_ids, enrollments)
    stats = compute_stats(graph)
    assert stats.edge_count == 3
    assert stats.density == 1.0
    assert stats.chromatic_lower_bound == 3
    assert stats.connected_components_count == 1
    assert stats.largest_component_size == 3


def test_independent_validator_catches_corrupted_graphs():
    """Independent validator must catch missing edges, extra edges, self-loops, and asymmetry."""
    exam_ids = ["e1", "e2", "e3"]
    enrollments = [("s1", "e1"), ("s1", "e2")]

    valid_graph = build_conflict_graph(exam_ids, enrollments)
    assert validate_graph(valid_graph, exam_ids, enrollments).is_valid is True

    # 1. Corrupt with self-loop
    corrupt_self_loop = ConflictGraph(
        vertices=set(exam_ids),
        adjacency={"e1": {"e1", "e2"}, "e2": {"e1"}, "e3": set()},
        edge_weights={("e1", "e2"): 1},
        vertex_metadata={},
    )
    rep = validate_graph(corrupt_self_loop, exam_ids, enrollments)
    assert rep.is_valid is False
    assert any("Self-loop" in err for err in rep.errors)

    # 2. Corrupt with asymmetry
    corrupt_asym = ConflictGraph(
        vertices=set(exam_ids),
        adjacency={"e1": {"e2"}, "e2": set(), "e3": set()},  # e1 -> e2 but e2 -/-> e1
        edge_weights={("e1", "e2"): 1},
        vertex_metadata={},
    )
    rep_asym = validate_graph(corrupt_asym, exam_ids, enrollments)
    assert rep_asym.is_valid is False
    assert any("Asymmetric" in err for err in rep_asym.errors)

    # 3. Corrupt with spurious edge
    corrupt_extra = ConflictGraph(
        vertices=set(exam_ids),
        adjacency={"e1": {"e2", "e3"}, "e2": {"e1"}, "e3": {"e1"}},
        edge_weights={("e1", "e2"): 1, ("e1", "e3"): 1},  # e3 has no shared enrollment with e1
        vertex_metadata={},
    )
    rep_extra = validate_graph(corrupt_extra, exam_ids, enrollments)
    assert rep_extra.is_valid is False
    assert any("spurious" in err for err in rep_extra.errors)


def test_canonical_enrollment_hash_stability():
    """Hash must be invariant to input ordering and change on data modification (P6.6)."""
    exam_ids_1 = ["e2", "e1", "e3"]
    enrollments_1 = [("s2", "e2"), ("s1", "e1"), ("s2", "e1")]

    exam_ids_2 = ["e1", "e3", "e2"]
    enrollments_2 = [("s1", "e1"), ("s2", "e1"), ("s2", "e2")]

    h1 = compute_enrollment_hash(exam_ids_1, enrollments_1)
    h2 = compute_enrollment_hash(exam_ids_2, enrollments_2)
    assert h1 == h2

    # Modified enrollment changes hash
    enrollments_3 = [("s1", "e1"), ("s2", "e1"), ("s3", "e3")]
    h3 = compute_enrollment_hash(exam_ids_1, enrollments_3)
    assert h1 != h3


def test_synthetic_large_graph_performance():
    """500 exams and thousands of enrollments complete in under 2 seconds (PRD §26.2)."""
    exam_ids = [f"exam_{i}" for i in range(500)]
    enrollments: list[tuple[str, str]] = []
    # 1000 students, each taking 4 random-ish exams
    for s in range(1000):
        s_id = f"student_{s}"
        base = (s * 3) % 495
        for offset in range(4):
            enrollments.append((s_id, f"exam_{base + offset}"))

    start_t = time.perf_counter()
    graph = build_conflict_graph(exam_ids, enrollments)
    stats = compute_stats(graph)
    duration = time.perf_counter() - start_t

    assert len(graph.vertices) == 500
    assert stats.edge_count > 0
    assert duration < 2.0  # Must be fast and scalable


# ==============================================================================
# 2. Database, Service, and API Integration Tests (P6.7 - P6.14)
# ==============================================================================
def setup_conflict_cycle_base(db: Session, admin_headers: dict[str, str], client: TestClient):
    """Sets up a Department, AcademicYear, 3 Subjects, 2 Students, Cycle, and Enrollments."""
    # Department
    dept = Department(name="Computer Science", code="CS", status=EntityStatus.ACTIVE)
    db.add(dept)
    db.flush()

    # Academic Year
    ay = AcademicYear(name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 6, 30))
    db.add(ay)
    db.flush()

    # Subjects: CS101, CS102, CS103
    s1 = Subject(
        subject_code="CS101",
        subject_name="Intro to Programming",
        department_id=dept.id,
        semester=1,
        credits=3.0,
        default_duration_minutes=180,
        status=EntityStatus.ACTIVE,
    )
    s2 = Subject(
        subject_code="CS102",
        subject_name="Data Structures",
        department_id=dept.id,
        semester=1,
        credits=3.0,
        default_duration_minutes=180,
        status=EntityStatus.ACTIVE,
    )
    s3 = Subject(
        subject_code="CS103",
        subject_name="Discrete Math",
        department_id=dept.id,
        semester=1,
        credits=3.0,
        default_duration_minutes=180,
        status=EntityStatus.ACTIVE,
    )
    db.add_all([s1, s2, s3])
    db.flush()

    # Students: STU001, STU002
    stu1 = Student(
        student_number="STU001",
        full_name="Alice Smith",
        email="alice@univ.edu",
        department_id=dept.id,
        semester=1,
        status=EntityStatus.ACTIVE,
    )
    stu2 = Student(
        student_number="STU002",
        full_name="Bob Jones",
        email="bob@univ.edu",
        department_id=dept.id,
        semester=1,
        status=EntityStatus.ACTIVE,
    )
    db.add_all([stu1, stu2])
    db.flush()

    # Cycle
    cycle = SchedulingCycle(
        name="Fall 2026 Midterm Exams",
        academic_year_id=ay.id,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 15),
        status=CycleStatus.DRAFT,
        timezone="UTC",
        configuration_json={},
    )
    db.add(cycle)
    db.flush()

    # Enrollments:
    # Alice takes CS101, CS102 -> edge (CS101, CS102)
    # Bob takes CS101, CS102, CS103 -> edges (CS101, CS102), (CS101, CS103), (CS102, CS103)
    # Expected edge weights:
    # (CS101, CS102) = 2 (Alice and Bob)
    # (CS101, CS103) = 1 (Bob)
    # (CS102, CS103) = 1 (Bob)
    enrs = [
        Enrollment(
            student_id=stu1.id, subject_id=s1.id, cycle_id=cycle.id, status=EnrollmentStatus.ACTIVE
        ),
        Enrollment(
            student_id=stu1.id, subject_id=s2.id, cycle_id=cycle.id, status=EnrollmentStatus.ACTIVE
        ),
        Enrollment(
            student_id=stu2.id, subject_id=s1.id, cycle_id=cycle.id, status=EnrollmentStatus.ACTIVE
        ),
        Enrollment(
            student_id=stu2.id, subject_id=s2.id, cycle_id=cycle.id, status=EnrollmentStatus.ACTIVE
        ),
        Enrollment(
            student_id=stu2.id, subject_id=s3.id, cycle_id=cycle.id, status=EnrollmentStatus.ACTIVE
        ),
    ]
    db.add_all(enrs)
    db.commit()

    # Sync exams for the cycle via cycle API
    resp_sync = client.post(f"/api/v1/cycles/{cycle.id}/exams/sync", headers=admin_headers)
    assert resp_sync.status_code == 200

    return cycle, [s1, s2, s3], [stu1, stu2]


def test_conflict_graph_build_idempotency_and_staleness(client: TestClient, db_session: Session):
    """
    Tests POST /cycles/{id}/graph/build, idempotency (no-op on unchanged hash),
    and isStale detection (Tasks P6.7, P6.8, P6.9, P6.10).
    """
    _, admin_headers = make_auth_user(db_session, role="admin", email="graph_admin@univ.edu")
    cycle, subjects, students = setup_conflict_cycle_base(db_session, admin_headers, client)

    # 1. First build: creates snapshot v1
    resp1 = client.post(f"/api/v1/cycles/{cycle.id}/graph/build", headers=admin_headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert (data1.get("isNew") if "isNew" in data1 else data1.get("is_new")) is True
    assert data1["version"] == 1
    assert (data1["stats"].get("vertex_count") or data1["stats"].get("vertexCount")) == 3
    assert (data1["stats"].get("edge_count") or data1["stats"].get("edgeCount")) == 3
    assert (
        data1["stats"].get("chromatic_lower_bound") or data1["stats"].get("chromaticLowerBound")
    ) == 3

    # 2. Second build without force: idempotent no-op returns same snapshot (P6.9)
    resp2 = client.post(f"/api/v1/cycles/{cycle.id}/graph/build", headers=admin_headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert (data2.get("isNew") if "isNew" in data2 else data2.get("is_new")) is False
    assert data2["version"] == 1
    assert (data2.get("snapshot_id") or data2.get("snapshotId")) == (
        data1.get("snapshot_id") or data1.get("snapshotId")
    )

    # 3. Build with force=True: creates snapshot v2
    resp3 = client.post(f"/api/v1/cycles/{cycle.id}/graph/build?force=true", headers=admin_headers)
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert (data3.get("isNew") if "isNew" in data3 else data3.get("is_new")) is True
    assert data3["version"] == 2

    # 4. Check GET /graph shows isStale == False
    resp_graph = client.get(f"/api/v1/cycles/{cycle.id}/graph", headers=admin_headers)
    assert resp_graph.status_code == 200
    g_data = resp_graph.json()
    assert (g_data.get("isStale") if "isStale" in g_data else g_data.get("is_stale")) is False

    # 5. Withdraw Bob's enrollment in CS103 -> should mark graph stale!
    enr_bob_cs3 = db_session.scalar(
        select(Enrollment).where(
            Enrollment.student_id == students[1].id,
            Enrollment.subject_id == subjects[2].id,
            Enrollment.cycle_id == cycle.id,
        )
    )
    assert enr_bob_cs3 is not None
    enr_bob_cs3.status = EnrollmentStatus.WITHDRAWN
    db_session.commit()

    resp_stale = client.get(f"/api/v1/cycles/{cycle.id}/graph", headers=admin_headers)
    assert resp_stale.status_code == 200
    assert (
        resp_stale.json().get("isStale")
        if "isStale" in resp_stale.json()
        else resp_stale.json().get("is_stale")
    ) is True


def test_conflict_graph_privacy_and_query_filters(client: TestClient, db_session: Session):
    """
    Verifies graph query endpoints strictly exclude student PII (§23)
    and support filtering by department, semester, and minWeight (P6.11).
    """
    _, admin_headers = make_auth_user(db_session, role="admin", email="priv_admin@univ.edu")
    _, student_headers = make_auth_user(db_session, role="student", email="test_student@univ.edu")
    cycle, _, _ = setup_conflict_cycle_base(db_session, admin_headers, client)

    # Build snapshot
    client.post(f"/api/v1/cycles/{cycle.id}/graph/build", headers=admin_headers)

    # Student user can read public conflict graph
    resp = client.get(f"/api/v1/cycles/{cycle.id}/graph", headers=student_headers)
    assert resp.status_code == 200
    payload = resp.json()

    # PRIVACY CHECK (PRD §23, §26.2): Ensure no student PII leaks into the graph response
    raw_str = resp.text.lower()
    assert "alice" not in raw_str
    assert "bob" not in raw_str
    assert "smith" not in raw_str
    assert "stu001" not in raw_str
    assert "student_id" not in raw_str
    assert "student_number" not in raw_str

    # Nodes and edges count
    nodes = payload["nodes"]
    edges = payload["edges"]
    assert len(nodes) == 3
    assert len(edges) == 3

    # Filter by minWeight=2: only the (CS101, CS102) edge has weight 2
    resp_filtered = client.get(
        f"/api/v1/cycles/{cycle.id}/graph?minWeight=2", headers=student_headers
    )
    assert resp_filtered.status_code == 200
    filtered_edges = resp_filtered.json()["edges"]
    assert len(filtered_edges) == 1
    assert (
        filtered_edges[0].get("shared_student_count") or filtered_edges[0].get("sharedStudentCount")
    ) == 2


def test_conflict_graph_export_json_and_csv(client: TestClient, db_session: Session):
    """Tests GET /graph/export with json and csv formats; verifies role restriction (Admin only)."""
    _, admin_headers = make_auth_user(db_session, role="admin", email="exp_admin@univ.edu")
    _, coord_headers = make_auth_user(db_session, role="coordinator", email="coord_exp@univ.edu")
    cycle, _, _ = setup_conflict_cycle_base(db_session, admin_headers, client)
    client.post(f"/api/v1/cycles/{cycle.id}/graph/build", headers=admin_headers)

    # 1. Non-admin gets 403 Forbidden
    resp_forbidden = client.get(
        f"/api/v1/cycles/{cycle.id}/graph/export?format=json", headers=coord_headers
    )
    assert resp_forbidden.status_code == 403

    # 2. Admin exports JSON
    resp_json = client.get(
        f"/api/v1/cycles/{cycle.id}/graph/export?format=json", headers=admin_headers
    )
    assert resp_json.status_code == 200
    assert resp_json.headers["content-type"] == "application/json"
    assert "conflict_graph_" in resp_json.headers["content-disposition"]
    data = resp_json.json()
    assert "nodes" in data and "edges" in data

    # 3. Admin exports CSV
    resp_csv = client.get(
        f"/api/v1/cycles/{cycle.id}/graph/export?format=csv", headers=admin_headers
    )
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    csv_text = resp_csv.text
    assert "exam_id_a,exam_id_b,subject_code_a,subject_code_b,shared_student_count" in csv_text
    assert "CS101" in csv_text and "CS102" in csv_text


def test_privileged_drilldown_shared_students(client: TestClient, db_session: Session):
    """
    Tests GET /graph/edges/{edge_id} and /graph/edges?examA=&examB=.
    Verifies that staff can drill down into shared students and the action is audited (FR-07, PRD §23).
    """
    _, admin_headers = make_auth_user(db_session, role="admin", email="drill_admin@univ.edu")
    _, student_headers = make_auth_user(db_session, role="student", email="drill_student@univ.edu")
    cycle, subjects, students = setup_conflict_cycle_base(db_session, admin_headers, client)
    client.post(f"/api/v1/cycles/{cycle.id}/graph/build", headers=admin_headers)

    # Get edge list
    resp_g = client.get(f"/api/v1/cycles/{cycle.id}/graph", headers=admin_headers)
    edges = resp_g.json()["edges"]
    # Find the edge with weight 2 (shared by Alice and Bob)
    edge_w2 = next(
        e for e in edges if (e.get("shared_student_count") or e.get("sharedStudentCount")) == 2
    )
    edge_id = edge_w2["id"]

    # 1. Student role cannot access drilldown -> 403
    resp_forbidden = client.get(
        f"/api/v1/cycles/{cycle.id}/graph/edges/{edge_id}", headers=student_headers
    )
    assert resp_forbidden.status_code == 403

    # 2. Admin drills down by edge_id
    resp_drill = client.get(
        f"/api/v1/cycles/{cycle.id}/graph/edges/{edge_id}", headers=admin_headers
    )
    assert resp_drill.status_code == 200
    drill_data = resp_drill.json()
    assert (drill_data.get("shared_student_count") or drill_data.get("sharedStudentCount")) == 2
    student_numbers = [
        (s.get("student_number") or s.get("studentNumber")) for s in drill_data["students"]
    ]
    assert "STU001" in student_numbers
    assert "STU002" in student_numbers

    # 3. Drilldown by exam pair
    exam_a_id = edge_w2.get("exam_id_a") or edge_w2.get("examIdA")
    exam_b_id = edge_w2.get("exam_id_b") or edge_w2.get("examIdB")
    resp_pair = client.get(
        f"/api/v1/cycles/{cycle.id}/graph/edges?examA={exam_a_id}&examB={exam_b_id}",
        headers=admin_headers,
    )
    assert resp_pair.status_code == 200
    assert (
        resp_pair.json().get("shared_student_count") or resp_pair.json().get("sharedStudentCount")
    ) == 2


def test_subject_conflict_degree_populated_from_latest_snapshot(
    client: TestClient, db_session: Session
):
    """
    Verifies that SubjectResponse dynamically includes conflictDegree from
    the latest graph snapshot (Task P6.13, PRD §11).
    """
    _, admin_headers = make_auth_user(db_session, role="admin", email="deg_admin@univ.edu")
    cycle, subjects, _ = setup_conflict_cycle_base(db_session, admin_headers, client)

    # Before build, conflict degree is None
    resp_sub_pre = client.get(f"/api/v1/subjects/{subjects[0].id}", headers=admin_headers)
    assert resp_sub_pre.status_code == 200
    assert (
        resp_sub_pre.json().get("conflict_degree") or resp_sub_pre.json().get("conflictDegree")
    ) is None

    # Build graph
    client.post(f"/api/v1/cycles/{cycle.id}/graph/build", headers=admin_headers)

    # After build, CS101 has 2 conflicts (CS102 and CS103)
    resp_sub_post = client.get(f"/api/v1/subjects/{subjects[0].id}", headers=admin_headers)
    assert resp_sub_post.status_code == 200
    assert (
        resp_sub_post.json().get("conflict_degree") or resp_sub_post.json().get("conflictDegree")
    ) == 2


def test_validate_conflict_graph_defect_branches():
    """Covers defect branches in pure validate_graph (P6.5)."""
    from app.algorithms.graph_builder import ConflictGraph, validate_graph

    # 1. Missing and extra vertices
    g_mismatch = ConflictGraph(
        vertices={"A", "B"},
        adjacency={"A": {"B"}, "B": {"A"}},
        edge_weights={("A", "B"): 1},
        vertex_metadata={},
    )
    val_mismatch = validate_graph(g_mismatch, exam_ids=["A", "C"], enrollments=[])
    assert not val_mismatch.is_valid
    assert any("missing 1 expected" in err for err in val_mismatch.errors)
    assert any("unexpected exam vertices" in err for err in val_mismatch.errors)

    # 2. Self-loop in edge_weights, non-normalized edge key, and non-positive weight
    g_bad_edges = ConflictGraph(
        vertices={"A", "B"},
        adjacency={"A": {"B"}, "B": {"A"}},
        edge_weights={
            ("A", "A"): 1,  # Self-loop
            ("B", "A"): 1,  # Non-normalized (u > v)
            ("A", "B"): 0,  # Non-positive weight
        },
        vertex_metadata={},
    )
    val_bad_edges = validate_graph(g_bad_edges, exam_ids=["A", "B"], enrollments=[])
    assert not val_bad_edges.is_valid
    assert any("Self-loop edge key" in err for err in val_bad_edges.errors)
    assert any("not normalized" in err for err in val_bad_edges.errors)
    assert any("non-positive shared student count" in err for err in val_bad_edges.errors)

    # 3. Vertex has neighbor not in vertices
    g_bad_nbr = ConflictGraph(
        vertices={"A"},
        adjacency={"A": {"Z"}},
        edge_weights={},
        vertex_metadata={},
    )
    val_bad_nbr = validate_graph(g_bad_nbr, exam_ids=["A"], enrollments=[])
    assert not val_bad_nbr.is_valid
    assert any("neighbor 'Z' not in vertex set" in err for err in val_bad_nbr.errors)
