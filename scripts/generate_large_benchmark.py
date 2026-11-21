"""Synthetic Large-Scale Dataset Generator for Performance Profiling.

PRD §19, Tasks P14.13, P14.19.
Generates 500 exams, 15,000 student enrollments, and 5,000 students.
Strictly labeled with [SYNTHETIC] identifiers to ensure zero confusion with real data.
"""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticExam:
    id: str
    code: str
    name: str
    department: str
    duration_minutes: int


@dataclass(frozen=True)
class SyntheticStudent:
    id: str
    student_number: str
    name: str
    email: str


@dataclass(frozen=True)
class SyntheticEnrollment:
    student_id: str
    exam_id: str


@dataclass(frozen=True)
class SyntheticSlot:
    id: str
    date: str
    session: str
    start_time: str
    end_time: str


@dataclass
class SyntheticBenchmarkDataset:
    exams: list[SyntheticExam]
    students: list[SyntheticStudent]
    enrollments: list[SyntheticEnrollment]
    slots: list[SyntheticSlot]
    enrollments_by_exam: dict[str, set[str]]
    conflict_adjacency: dict[str, set[str]]


def generate_synthetic_benchmark(
    num_exams: int = 500,
    num_students: int = 5000,
    target_enrollments: int = 15000,
    seed: int = 42,
) -> SyntheticBenchmarkDataset:
    """Generates synthetic multi-department benchmark data labeled [SYNTHETIC]."""
    rng = random.Random(seed)

    departments = ["CS", "EE", "ME", "CE", "MATH", "PHYS", "CHEM", "BIO", "ECON", "MGMT"]

    exams: list[SyntheticExam] = []
    for i in range(num_exams):
        dept = departments[i % len(departments)]
        code = f"[SYNTHETIC]-{dept}{100 + (i // len(departments)) * 10 + (i % 10)}"
        exams.append(
            SyntheticExam(
                id=f"syn_exam_{i:04d}",
                code=code,
                name=f"[SYNTHETIC] Course {code}",
                department=dept,
                duration_minutes=180,
            )
        )

    students: list[SyntheticStudent] = []
    for i in range(num_students):
        stu_num = f"[SYNTHETIC]-STU-{i:05d}"
        students.append(
            SyntheticStudent(
                id=f"syn_stu_{i:05d}",
                student_number=stu_num,
                name=f"[SYNTHETIC] Student {i}",
                email=f"syn.student.{i}@synthetic.university.edu",
            )
        )

    # Distribute ~15,000 enrollments
    # Real students typically enroll in 3-5 courses in their department + 1-2 electives
    enrollments: list[SyntheticEnrollment] = []
    enrollments_by_exam: dict[str, set[str]] = {e.id: set() for e in exams}
    exams_by_dept: dict[str, list[SyntheticExam]] = {d: [] for d in departments}
    for e in exams:
        exams_by_dept[e.department].append(e)

    for stu in students:
        primary_dept = rng.choice(departments)
        dept_pool = exams_by_dept[primary_dept]
        other_pool = [e for d, el in exams_by_dept.items() if d != primary_dept for e in el]

        # 2-3 core courses
        k_core = min(rng.randint(2, 3), len(dept_pool))
        chosen_exams = set(rng.sample(dept_pool, k_core))

        # 0-1 elective
        if other_pool and rng.random() > 0.4:
            chosen_exams.add(rng.choice(other_pool))

        for exam in chosen_exams:
            enrollments.append(SyntheticEnrollment(student_id=stu.id, exam_id=exam.id))
            enrollments_by_exam[exam.id].add(stu.id)

            if len(enrollments) >= target_enrollments:
                break
        if len(enrollments) >= target_enrollments:
            break

    # Build conflict adjacency: E1 conflicts with E2 if they share >= 1 student
    conflict_adjacency: dict[str, set[str]] = {e.id: set() for e in exams}

    # Invert mapping: student -> exams
    student_exams: dict[str, set[str]] = {s.id: set() for s in students}
    for enr in enrollments:
        student_exams[enr.student_id].add(enr.exam_id)

    for ex_set in student_exams.values():
        ex_list = list(ex_set)
        for i in range(len(ex_list)):
            for j in range(i + 1, len(ex_list)):
                u, v = ex_list[i], ex_list[j]
                conflict_adjacency[u].add(v)
                conflict_adjacency[v].add(u)

    # 40 Slots (20 Days x 2 sessions)
    slots: list[SyntheticSlot] = []
    for day in range(1, 21):
        d_str = f"2026-12-{day:02d}"
        slots.append(SyntheticSlot(f"syn_slot_{day}_M", d_str, "Morning", "09:00", "12:00"))
        slots.append(SyntheticSlot(f"syn_slot_{day}_A", d_str, "Afternoon", "14:00", "17:00"))

    return SyntheticBenchmarkDataset(
        exams=exams,
        students=students,
        enrollments=enrollments,
        slots=slots,
        enrollments_by_exam=enrollments_by_exam,
        conflict_adjacency=conflict_adjacency,
    )


if __name__ == "__main__":
    data = generate_synthetic_benchmark()
    edge_count = sum(len(adj) for adj in data.conflict_adjacency.values()) // 2
    avg_deg = sum(len(adj) for adj in data.conflict_adjacency.values()) / len(data.exams)
    print("=== SYNTHETIC BENCHMARK DATASET GENERATED ===")
    print(f"Total Exams (|V|):       {len(data.exams)}")
    print(f"Total Students:          {len(data.students)}")
    print(f"Total Enrollments:       {len(data.enrollments)}")
    print(f"Total Conflict Edges:    {edge_count}")
    print(f"Average Degree:          {avg_deg:.2f}")
    print(f"Available Slots:         {len(data.slots)}")
