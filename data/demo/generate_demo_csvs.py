"""Generator for Phase 16 Synthetic Demo Datasets.

Creates deterministic, realistic CSV files for departments, subjects, students, and enrollments
demonstrating algorithmic conflict structures, dense hubs, isolated subjects, and cohort clustering.
PRD §32, Task P16.1, P16.2.
"""

from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parent

def generate_csvs() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    fixtures_dir = BASE_DIR / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Departments
    dept_file = BASE_DIR / "demo_departments.csv"
    with open(dept_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "name"])
        writer.writerow(["CS", "Department of Computer Science"])
        writer.writerow(["EE", "Department of Electrical Engineering"])

    # 2. Subjects (12 subjects, 2 departments, 4 semesters)
    # CS301 is designated as high-degree hub exam. CS401 is isolated (0 conflicts).
    sub_file = BASE_DIR / "demo_subjects.csv"
    subjects = [
        ("CS101", "Introduction to Programming", "CS", 1, 3.0),
        ("CS102", "Discrete Mathematics", "CS", 1, 3.0),
        ("CS201", "Data Structures & Algorithms", "CS", 2, 4.0),
        ("CS202", "Computer Organization & Architecture", "CS", 2, 3.0),
        ("CS301", "Operating Systems & Concurrency", "CS", 3, 4.0),
        ("CS302", "Database Management Systems", "CS", 3, 3.0),
        ("CS303", "Computer Networks & Protocols", "CS", 3, 3.0),
        ("CS401", "Advanced Machine Learning Capstone", "CS", 4, 3.0),
        ("EE101", "Linear Circuit Analysis", "EE", 1, 3.0),
        ("EE102", "Digital Logic & Microprocessors", "EE", 1, 3.0),
        ("EE201", "Signals and Linear Systems", "EE", 2, 3.0),
        ("EE202", "Electromagnetic Fields & Waves", "EE", 2, 3.0),
    ]
    with open(sub_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["subject_code", "subject_name", "department_code", "semester", "credits"])
        for s in subjects:
            writer.writerow(s)

    # 3. Students (50 students: 30 CS, 20 EE)
    students_file = BASE_DIR / "demo_students.csv"
    students = []
    for i in range(1, 31):
        num = f"CS-{i:03d}"
        name = f"Synthetic Student CS {i:02d}"
        email = f"student.cs{i:02d}@univ.edu"
        sem = 1 if i <= 10 else (2 if i <= 20 else 3)
        students.append((num, name, email, "CS", sem))

    for i in range(1, 21):
        num = f"EE-{i:03d}"
        name = f"Synthetic Student EE {i:02d}"
        email = f"student.ee{i:02d}@univ.edu"
        sem = 1 if i <= 10 else 2
        students.append((num, name, email, "EE", sem))

    with open(students_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_number", "full_name", "email", "department_code", "semester"])
        for st in students:
            writer.writerow(st)

    # 4. Enrollments (Reflecting realistic cohorts & cross-listed subjects)
    # CS Sem 1 cohort (students 1-10): CS101, CS102, EE102 (digital logic cross-department)
    # CS Sem 2 cohort (students 11-20): CS201, CS202, EE201 (signals cross-department)
    # CS Sem 3 cohort (students 21-30): CS301, CS302, CS303 + some taking CS101 (repeater)
    # EE Sem 1 cohort (students 31-40): EE101, EE102, CS101 (programming for engineers)
    # EE Sem 2 cohort (students 41-50): EE201, EE202, CS301 (repeater/cross-elective creating hub)
    # CS401 is taken exclusively by only 1 student (CS-001) alone, keeping it near-isolated.
    enrollment_file = BASE_DIR / "demo_enrollments.csv"
    enrollments = []

    # CS Cohort 1
    for i in range(1, 11):
        s_num = f"CS-{i:03d}"
        enrollments.extend([(s_num, "CS101"), (s_num, "CS102"), (s_num, "EE102")])

    # CS Cohort 2
    for i in range(11, 21):
        s_num = f"CS-{i:03d}"
        enrollments.extend([(s_num, "CS201"), (s_num, "CS202"), (s_num, "EE201")])

    # CS Cohort 3 (High-degree hub on CS301)
    for i in range(21, 31):
        s_num = f"CS-{i:03d}"
        enrollments.extend([(s_num, "CS301"), (s_num, "CS302"), (s_num, "CS303")])
        if i in [21, 22]:
            enrollments.append((s_num, "CS101"))  # Repeaters bridging Cohort 3 and Cohort 1

    # EE Cohort 1 (Cross-department enrollments bridging CS101 and EE101)
    for i in range(1, 11):
        s_num = f"EE-{i:03d}"
        enrollments.extend([(s_num, "EE101"), (s_num, "EE102"), (s_num, "CS101")])

    # EE Cohort 2 (Cross-department bridge to CS301)
    for i in range(11, 21):
        s_num = f"EE-{i:03d}"
        enrollments.extend([(s_num, "EE201"), (s_num, "EE202"), (s_num, "CS301")])

    with open(enrollment_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_number", "subject_code"])
        for enr in enrollments:
            writer.writerow(enr)

    # 5. Fixtures for Error Scenarios (P16.5)
    # Bad emails & malformed formats
    invalid_stu_file = fixtures_dir / "invalid_students_bad_email.csv"
    with open(invalid_stu_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_number", "full_name", "email", "department_code", "semester"])
        writer.writerow(["ERR-001", "Bad Email User", "not-an-email", "CS", "1"])
        writer.writerow(["ERR-002", "Missing Dept", "err2@univ.edu", "NON_EXISTENT_DEPT", "1"])
        writer.writerow(["ERR-003", "Negative Semester", "err3@univ.edu", "CS", "-2"])

    # Duplicate & non-existent enrollments
    invalid_enr_file = fixtures_dir / "invalid_enrollments_duplicate.csv"
    with open(invalid_enr_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_number", "subject_code"])
        writer.writerow(["CS-001", "CS101"])
        writer.writerow(["CS-001", "CS101"])  # Duplicate enrollment
        writer.writerow(["NON_EXISTENT_STUDENT", "CS101"])  # Unregistered student
        writer.writerow(["CS-001", "NON_EXISTENT_SUBJECT"])  # Unregistered subject

    print(f"Generated demo datasets in {BASE_DIR}")

if __name__ == "__main__":
    generate_csvs()
