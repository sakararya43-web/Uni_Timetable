import csv
import hashlib
import io
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import DomainException
from app.models.academic import Department, Program, Student, Subject
from app.models.audit import ImportBatch
from app.models.enums import (
    AuditAction,
    EnrollmentStatus,
    EntityStatus,
    ImportStatus,
    ImportType,
    enum_val,
)
from app.models.scheduling import Enrollment, SchedulingCycle
from app.models.user import User
from app.schemas.import_csv import (
    ImportCommitResponse,
    ImportPreviewResponse,
    RowValidationError,
)
from app.services.audit_service import audit_service
from app.services.staleness_service import staleness_service
from app.utils.csv_parser import decode_csv_bytes, parse_csv_text, sanitize_formula_injection

# Identifier Regex
STUDENT_NUMBER_REGEX = re.compile(r"^[A-Za-z0-9_-]{2,64}$")
SUBJECT_CODE_REGEX = re.compile(r"^[A-Za-z0-9_-]{2,32}$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Header Aliases Mapping (Task P4.3)
STUDENT_ALIASES: dict[str, list[str]] = {
    "student_id": ["student_id", "student_number", "studentid", "roll_no", "rollno", "id"],
    "student_name": ["student_name", "name", "full_name", "studentname"],
    "department": ["department", "department_code", "dept", "dept_code"],
    "semester": ["semester", "sem", "term"],
    "email": ["email", "student_email"],
    "program": ["program", "program_code"],
}

SUBJECT_ALIASES: dict[str, list[str]] = {
    "subject_code": ["subject_code", "course_code", "code", "subjectcode"],
    "subject_name": ["subject_name", "course_name", "name", "subjectname"],
    "department": ["department", "department_code", "dept", "dept_code"],
    "semester": ["semester", "sem", "term"],
    "duration_minutes": ["duration_minutes", "duration", "exam_duration"],
    "credits": ["credits"],
    "priority": ["priority"],
    "program": ["program", "program_code"],
}

ENROLLMENT_ALIASES: dict[str, list[str]] = {
    "student_id": ["student_id", "student_number", "studentid", "roll_no"],
    "subject_code": ["subject_code", "course_code", "code", "subjectcode"],
    "cycle_id": ["cycle_id", "cycle", "scheduling_cycle"],
}


class ImportService:
    @staticmethod
    def _resolve_headers(
        found_headers: list[str], alias_map: dict[str, list[str]], required_keys: list[str]
    ) -> dict[str, str]:
        """Maps canonical field name to found header in CSV. Raises error if required keys missing."""
        resolved: dict[str, str] = {}
        header_set = set(found_headers)

        for canonical, aliases in alias_map.items():
            for a in aliases:
                if a in header_set:
                    resolved[canonical] = a
                    break

        missing = [k for k in required_keys if k not in resolved]
        if missing:
            raise DomainException(
                code="MISSING_REQUIRED_COLUMNS",
                message=(
                    f"CSV is missing required columns: {', '.join(missing)}. "
                    f"Found columns: {', '.join(found_headers)}."
                ),
                status_code=422,
            )
        return resolved

    # ==========================================================================
    # Validation per Import Type (Tasks P4.4, P4.5, P4.12, P4.13)
    # ==========================================================================
    @staticmethod
    def _validate_students(
        db: Session, raw_rows: list[dict[str, str]], header_map: dict[str, str]
    ) -> tuple[list[dict[str, Any]], list[RowValidationError], int, int]:
        valid_rows: list[dict[str, Any]] = []
        errors: list[RowValidationError] = []
        seen_in_file: set[str] = set()

        # Preloaded lookups to prevent N+1 queries (Task P4.13)
        dept_lookup = {
            d.code.upper(): d.id
            for d in db.scalars(
                select(Department).where(Department.status == EntityStatus.ACTIVE)
            ).all()
        }
        existing_numbers = set(db.scalars(select(Student.student_number)).all())
        prog_lookup = {
            (p.department_id, p.code.upper()): p.id
            for p in db.scalars(select(Program).where(Program.status == EntityStatus.ACTIVE)).all()
        }

        dup_count = 0
        unknown_ref_count = 0

        for r in raw_rows:
            row_num = int(r["_row_num"])
            st_id_raw = r.get(header_map["student_id"], "").strip()
            st_name_raw = r.get(header_map["student_name"], "").strip()
            dept_raw = r.get(header_map["department"], "").strip()
            sem_raw = r.get(header_map["semester"], "").strip()
            email_raw = r.get(header_map["email"], "").strip() if "email" in header_map else ""
            prog_raw = r.get(header_map["program"], "").strip() if "program" in header_map else ""

            row_has_error = False

            # Student ID Validation
            if not st_id_raw:
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="student_id",
                        value=st_id_raw,
                        errorCode="EMPTY_REQUIRED_FIELD",
                        message=f"Row {row_num}, field student_id: Student ID cannot be empty.",
                        suggestion="Provide a unique student ID such as S001.",
                    )
                )
                row_has_error = True
            elif not STUDENT_NUMBER_REGEX.match(st_id_raw):
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="student_id",
                        value=st_id_raw,
                        errorCode="INVALID_STUDENT_ID_FORMAT",
                        message=(
                            f"Row {row_num}, field student_id: '{st_id_raw}' does not match "
                            "allowed alphanumeric format (2-64 chars)."
                        ),
                        suggestion="Use alphanumeric characters, hyphens, or underscores (e.g. STU-101).",
                    )
                )
                row_has_error = True
            elif st_id_raw.upper() in seen_in_file:
                dup_count += 1
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="student_id",
                        value=st_id_raw,
                        errorCode="DUPLICATE_IN_FILE",
                        message=f"Row {row_num}, field student_id: Duplicate student ID '{st_id_raw}' in this CSV file.",
                        suggestion="Remove the duplicate row from the CSV.",
                    )
                )
                row_has_error = True
            elif st_id_raw.upper() in existing_numbers:
                dup_count += 1
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="student_id",
                        value=st_id_raw,
                        errorCode="DUPLICATE_IN_DATABASE",
                        message=f"Row {row_num}, field student_id: Student ID '{st_id_raw}' already exists in the system.",
                        suggestion="Provide a different student ID or manage the existing student record.",
                    )
                )
                row_has_error = True
            else:
                seen_in_file.add(st_id_raw.upper())

            # Student Name Validation
            if not st_name_raw or len(st_name_raw) < 2:
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="student_name",
                        value=st_name_raw,
                        errorCode="INVALID_NAME",
                        message=f"Row {row_num}, field student_name: Name must be between 2 and 255 characters.",
                        suggestion="Provide the student's full name (e.g. John Doe).",
                    )
                )
                row_has_error = True

            # Department Validation
            dept_id = dept_lookup.get(dept_raw.upper())
            if not dept_id:
                unknown_ref_count += 1
                sample_depts = ", ".join(sorted(dept_lookup.keys())[:5]) or "None"
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="department",
                        value=dept_raw,
                        errorCode="UNKNOWN_DEPARTMENT",
                        message=f"Row {row_num}, field department: Department '{dept_raw}' does not exist or is inactive.",
                        suggestion=f"Use a valid active department code such as: {sample_depts}.",
                    )
                )
                row_has_error = True

            # Semester Validation
            try:
                sem_val = int(sem_raw)
                if not (1 <= sem_val <= 16):
                    raise ValueError()
            except ValueError:
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="semester",
                        value=sem_raw,
                        errorCode="INVALID_SEMESTER",
                        message=f"Row {row_num}, field semester: '{sem_raw}' is not a valid semester number (1-16).",
                        suggestion="Use an integer between 1 and 16, e.g. 5.",
                    )
                )
                row_has_error = True
                sem_val = 1

            # Optional Email Validation
            if email_raw and not EMAIL_REGEX.match(email_raw):
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="email",
                        value=email_raw,
                        errorCode="INVALID_EMAIL_FORMAT",
                        message=f"Row {row_num}, field email: '{email_raw}' is not a valid email address.",
                        suggestion="Use a standard email format, e.g. student@univ.edu.",
                    )
                )
                row_has_error = True

            # Optional Program Validation
            prog_id: str | None = None
            if prog_raw and dept_id:
                prog_id = prog_lookup.get((dept_id, prog_raw.upper()))
                if not prog_id:
                    errors.append(
                        RowValidationError(
                            row=row_num,
                            field="program",
                            value=prog_raw,
                            errorCode="UNKNOWN_PROGRAM",
                            message=f"Row {row_num}, field program: Program '{prog_raw}' not found for department '{dept_raw}'.",
                            suggestion="Check the program code or omit this field.",
                        )
                    )
                    row_has_error = True

            if not row_has_error:
                valid_rows.append(
                    {
                        "student_number": sanitize_formula_injection(st_id_raw.upper()),
                        "full_name": sanitize_formula_injection(st_name_raw),
                        "department_id": dept_id,
                        "program_id": prog_id,
                        "semester": sem_val,
                        "email": sanitize_formula_injection(email_raw) if email_raw else None,
                    }
                )

        return valid_rows, errors, dup_count, unknown_ref_count

    @staticmethod
    def _validate_subjects(
        db: Session, raw_rows: list[dict[str, str]], header_map: dict[str, str]
    ) -> tuple[list[dict[str, Any]], list[RowValidationError], int, int]:
        valid_rows: list[dict[str, Any]] = []
        errors: list[RowValidationError] = []
        seen_in_file: set[str] = set()

        dept_lookup = {
            d.code.upper(): d.id
            for d in db.scalars(
                select(Department).where(Department.status == EntityStatus.ACTIVE)
            ).all()
        }
        existing_codes = set(db.scalars(select(Subject.subject_code)).all())

        dup_count = 0
        unknown_ref_count = 0

        for r in raw_rows:
            row_num = int(r["_row_num"])
            sub_code_raw = r.get(header_map["subject_code"], "").strip()
            sub_name_raw = r.get(header_map["subject_name"], "").strip()
            dept_raw = r.get(header_map["department"], "").strip()
            sem_raw = r.get(header_map["semester"], "").strip()
            duration_raw = (
                r.get(header_map["duration_minutes"], "").strip()
                if "duration_minutes" in header_map
                else "180"
            )
            credits_raw = (
                r.get(header_map["credits"], "").strip() if "credits" in header_map else "3.0"
            )
            priority_raw = (
                r.get(header_map["priority"], "").strip() if "priority" in header_map else "1"
            )

            row_has_error = False

            # Subject Code Validation
            if not sub_code_raw:
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="subject_code",
                        value=sub_code_raw,
                        errorCode="EMPTY_REQUIRED_FIELD",
                        message=f"Row {row_num}, field subject_code: Subject code cannot be empty.",
                        suggestion="Provide a subject code such as CS301.",
                    )
                )
                row_has_error = True
            elif not SUBJECT_CODE_REGEX.match(sub_code_raw):
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="subject_code",
                        value=sub_code_raw,
                        errorCode="INVALID_SUBJECT_CODE_FORMAT",
                        message=f"Row {row_num}, field subject_code: '{sub_code_raw}' does not match allowed format (2-32 chars).",
                        suggestion="Use alphanumeric characters, dashes, or underscores, e.g. CS301.",
                    )
                )
                row_has_error = True
            elif sub_code_raw.upper() in seen_in_file:
                dup_count += 1
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="subject_code",
                        value=sub_code_raw,
                        errorCode="DUPLICATE_IN_FILE",
                        message=f"Row {row_num}, field subject_code: Duplicate subject code '{sub_code_raw}' in this CSV.",
                        suggestion="Remove the duplicate row from the CSV.",
                    )
                )
                row_has_error = True
            elif sub_code_raw.upper() in existing_codes:
                dup_count += 1
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="subject_code",
                        value=sub_code_raw,
                        errorCode="DUPLICATE_IN_DATABASE",
                        message=f"Row {row_num}, field subject_code: Subject code '{sub_code_raw}' already exists.",
                        suggestion="Use an unused subject code or manage the existing subject.",
                    )
                )
                row_has_error = True
            else:
                seen_in_file.add(sub_code_raw.upper())

            # Subject Name Validation
            if not sub_name_raw or len(sub_name_raw) < 2:
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="subject_name",
                        value=sub_name_raw,
                        errorCode="INVALID_NAME",
                        message=f"Row {row_num}, field subject_name: Name must be between 2 and 255 characters.",
                        suggestion="Provide a descriptive subject name (e.g. Operating Systems).",
                    )
                )
                row_has_error = True

            # Department Validation
            dept_id = dept_lookup.get(dept_raw.upper())
            if not dept_id:
                unknown_ref_count += 1
                sample_depts = ", ".join(sorted(dept_lookup.keys())[:5]) or "None"
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="department",
                        value=dept_raw,
                        errorCode="UNKNOWN_DEPARTMENT",
                        message=f"Row {row_num}, field department: Department '{dept_raw}' does not exist or is inactive.",
                        suggestion=f"Use a valid active department code such as: {sample_depts}.",
                    )
                )
                row_has_error = True

            # Semester Validation
            try:
                sem_val = int(sem_raw)
                if not (1 <= sem_val <= 16):
                    raise ValueError()
            except ValueError:
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="semester",
                        value=sem_raw,
                        errorCode="INVALID_SEMESTER",
                        message=f"Row {row_num}, field semester: '{sem_raw}' is not an integer between 1 and 16.",
                        suggestion="Use an integer between 1 and 16, e.g. 5.",
                    )
                )
                row_has_error = True
                sem_val = 1

            # Duration Minutes Validation
            try:
                dur_val = int(duration_raw) if duration_raw else 180
                if not (30 <= dur_val <= 360):
                    raise ValueError()
            except ValueError:
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="duration_minutes",
                        value=duration_raw,
                        errorCode="INVALID_DURATION",
                        message=f"Row {row_num}, field duration_minutes: '{duration_raw}' is not between 30 and 360 minutes.",
                        suggestion="Provide duration in minutes (e.g. 180 for a 3-hour exam).",
                    )
                )
                row_has_error = True
                dur_val = 180

            # Credits Validation
            try:
                cred_val = float(credits_raw) if credits_raw else 3.0
                if cred_val < 0.0:
                    raise ValueError()
            except ValueError:
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="credits",
                        value=credits_raw,
                        errorCode="INVALID_CREDITS",
                        message=f"Row {row_num}, field credits: '{credits_raw}' must be a non-negative number.",
                        suggestion="Provide a positive number such as 3.0.",
                    )
                )
                row_has_error = True
                cred_val = 3.0

            # Priority Validation
            try:
                prio_val = int(priority_raw) if priority_raw else 1
                if not (1 <= prio_val <= 10):
                    raise ValueError()
            except ValueError:
                prio_val = 1

            if not row_has_error:
                valid_rows.append(
                    {
                        "subject_code": sanitize_formula_injection(sub_code_raw.upper()),
                        "subject_name": sanitize_formula_injection(sub_name_raw),
                        "department_id": dept_id,
                        "semester": sem_val,
                        "credits": cred_val,
                        "default_duration_minutes": dur_val,
                        "priority": prio_val,
                    }
                )

        return valid_rows, errors, dup_count, unknown_ref_count

    @staticmethod
    def _validate_enrollments(
        db: Session,
        raw_rows: list[dict[str, str]],
        header_map: dict[str, str],
        target_cycle_id: str,
    ) -> tuple[list[dict[str, Any]], list[RowValidationError], int, int]:
        # Order dependency check (Task P4.12)
        total_students = (
            db.scalar(select(func.count(Student.id)).where(Student.status == EntityStatus.ACTIVE))
            or 0
        )
        total_subjects = (
            db.scalar(select(func.count(Subject.id)).where(Subject.status == EntityStatus.ACTIVE))
            or 0
        )
        if total_students == 0 or total_subjects == 0:
            raise DomainException(
                code="PREREQUISITES_MISSING",
                message=(
                    "Cannot import enrollments: prerequisite subjects or students are missing in the database. "
                    "Please import Subjects and Students before importing Enrollments."
                ),
                status_code=422,
            )

        valid_rows: list[dict[str, Any]] = []
        errors: list[RowValidationError] = []
        seen_pairs_in_file: set[tuple[str, str]] = set()

        # Preloaded lookups (Task P4.13)
        student_lookup = {
            s.student_number.upper(): s.id
            for s in db.scalars(select(Student).where(Student.status == EntityStatus.ACTIVE)).all()
        }
        subject_lookup = {
            s.subject_code.upper(): s.id
            for s in db.scalars(select(Subject).where(Subject.status == EntityStatus.ACTIVE)).all()
        }
        existing_enr_pairs = set(
            db.execute(
                select(Enrollment.student_id, Enrollment.subject_id).where(
                    Enrollment.cycle_id == target_cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            ).all()
        )

        dup_count = 0
        unknown_ref_count = 0

        for r in raw_rows:
            row_num = int(r["_row_num"])
            st_id_raw = r.get(header_map["student_id"], "").strip()
            sub_code_raw = r.get(header_map["subject_code"], "").strip()

            row_has_error = False

            # Student existence
            st_id = student_lookup.get(st_id_raw.upper())
            if not st_id:
                unknown_ref_count += 1
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="student_id",
                        value=st_id_raw,
                        errorCode="UNKNOWN_STUDENT",
                        message=f"Row {row_num}, field student_id: Student '{st_id_raw}' does not exist or is inactive.",
                        suggestion="Ensure this student ID exists in the student catalog.",
                    )
                )
                row_has_error = True

            # Subject existence
            sub_id = subject_lookup.get(sub_code_raw.upper())
            if not sub_id:
                unknown_ref_count += 1
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="subject_code",
                        value=sub_code_raw,
                        errorCode="UNKNOWN_SUBJECT",
                        message=f"Row {row_num}, field subject_code: Subject '{sub_code_raw}' does not exist or is inactive.",
                        suggestion="Ensure this subject code exists in the course catalog.",
                    )
                )
                row_has_error = True

            # Duplicate pair in CSV
            pair_key = (st_id_raw.upper(), sub_code_raw.upper())
            if pair_key in seen_pairs_in_file:
                dup_count += 1
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="student_id,subject_code",
                        value=f"{st_id_raw},{sub_code_raw}",
                        errorCode="DUPLICATE_IN_FILE",
                        message=f"Row {row_num}: Duplicate enrollment pair ({st_id_raw}, {sub_code_raw}) in CSV file.",
                        suggestion="Remove duplicate enrollment rows from the CSV.",
                    )
                )
                row_has_error = True
            else:
                seen_pairs_in_file.add(pair_key)

            # Already enrolled in cycle in DB
            if st_id and sub_id and (st_id, sub_id) in existing_enr_pairs:
                dup_count += 1
                errors.append(
                    RowValidationError(
                        row=row_num,
                        field="student_id,subject_code",
                        value=f"{st_id_raw},{sub_code_raw}",
                        errorCode="DUPLICATE_IN_DATABASE",
                        message=f"Row {row_num}: Student '{st_id_raw}' is already enrolled in '{sub_code_raw}' for this cycle.",
                        suggestion="Skip this row or withdraw existing enrollment.",
                    )
                )
                row_has_error = True

            if not row_has_error and st_id and sub_id:
                valid_rows.append(
                    {
                        "student_id": st_id,
                        "subject_id": sub_id,
                        "cycle_id": target_cycle_id,
                        "student_number": st_id_raw.upper(),
                        "subject_code": sub_code_raw.upper(),
                    }
                )

        return valid_rows, errors, dup_count, unknown_ref_count

    # ==========================================================================
    # Main Preview & Stage Flow (Task P4.1, P4.6, P4.9)
    # ==========================================================================
    @classmethod
    def preview_import(
        cls,
        db: Session,
        import_type: ImportType,
        raw_bytes: bytes,
        file_name: str,
        actor: User,
        cycle_id: str | None = None,
        max_size_bytes: int = 10 * 1024 * 1024,
        max_rows: int = 50000,
        request_id: str | None = None,
    ) -> ImportPreviewResponse:
        # 1. File Safety & Decoding (Task P4.2)
        content = decode_csv_bytes(raw_bytes, max_size_bytes=max_size_bytes)
        file_hash = hashlib.sha256(raw_bytes).hexdigest()

        # Idempotency check: Has this exact file been committed before? (Task P4.9)
        already_committed = db.scalar(
            select(ImportBatch).where(
                ImportBatch.file_hash == file_hash,
                ImportBatch.status == ImportStatus.COMMITTED,
            )
        )
        already_imported = already_committed is not None
        warning_msg = (
            "Warning: An identical file was already imported previously."
            if already_imported
            else None
        )

        # 2. Parse CSV
        headers, rows = parse_csv_text(content, max_rows=max_rows)

        # 3. Resolve Headers & Validate Rows
        valid_rows: list[dict[str, Any]] = []
        errors: list[RowValidationError] = []
        dup_count = 0
        unknown_ref_count = 0

        if import_type == ImportType.STUDENTS:
            header_map = cls._resolve_headers(
                headers,
                STUDENT_ALIASES,
                ["student_id", "student_name", "department", "semester"],
            )
            valid_rows, errors, dup_count, unknown_ref_count = cls._validate_students(
                db, rows, header_map
            )
        elif import_type == ImportType.SUBJECTS:
            header_map = cls._resolve_headers(
                headers,
                SUBJECT_ALIASES,
                ["subject_code", "subject_name", "department", "semester"],
            )
            valid_rows, errors, dup_count, unknown_ref_count = cls._validate_subjects(
                db, rows, header_map
            )
        elif import_type == ImportType.ENROLLMENTS:
            if not cycle_id:
                raise DomainException(
                    code="CYCLE_REQUIRED",
                    message="A valid cycle_id is required to import enrollments (ADR-003).",
                    status_code=422,
                )
            cycle = db.get(SchedulingCycle, cycle_id)
            if not cycle:
                raise DomainException(
                    code="UNKNOWN_CYCLE",
                    message=f"Scheduling cycle '{cycle_id}' was not found.",
                    status_code=404,
                )

            header_map = cls._resolve_headers(
                headers, ENROLLMENT_ALIASES, ["student_id", "subject_code"]
            )
            valid_rows, errors, dup_count, unknown_ref_count = cls._validate_enrollments(
                db, rows, header_map, cycle_id
            )
        else:
            raise DomainException(
                code="INVALID_IMPORT_TYPE",
                message=f"Unsupported import type '{import_type}'.",
                status_code=422,
            )

        total_rows = len(rows)
        valid_count = len(valid_rows)
        invalid_count = len({e.row for e in errors})

        # 4. Save Staged ImportBatch (Task P4.6)
        batch = ImportBatch(
            import_type=import_type,
            cycle_id=cycle_id,
            file_name=file_name,
            file_hash=file_hash,
            total_rows=total_rows,
            valid_rows=valid_count,
            invalid_rows=invalid_count,
            status=ImportStatus.PREVIEW,
            errors_json={
                "errors": [err.model_dump() for err in errors],
                "staged_rows": valid_rows,
            },
            created_by=actor.id,
            created_at=datetime.now(UTC),
        )
        db.add(batch)
        db.flush()

        audit_service.record(
            db=db,
            action=AuditAction.IMPORT_PREVIEW,
            entity_type="import_batch",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=batch.id,
            after={
                "import_type": import_type.value,
                "total_rows": total_rows,
                "valid_rows": valid_count,
                "invalid_rows": invalid_count,
                "file_hash": file_hash,
            },
            request_id=request_id,
        )
        db.commit()
        db.refresh(batch)

        return ImportPreviewResponse(
            batch_id=batch.id,
            import_type=batch.import_type,
            cycle_id=batch.cycle_id,
            file_name=batch.file_name,
            total_rows=batch.total_rows,
            valid_rows=batch.valid_rows,
            invalid_rows=batch.invalid_rows,
            duplicate_count=dup_count,
            unknown_reference_count=unknown_ref_count,
            already_imported=already_imported,
            warning_message=warning_msg,
            errors=errors,
            sample_valid_rows=valid_rows[:10],
            status=batch.status,
        )

    # ==========================================================================
    # Confirm & Commit Staged Batch (Tasks P4.7, P4.8, P4.10, P4.14)
    # ==========================================================================
    @classmethod
    def confirm_import(
        cls,
        db: Session,
        batch_id: str,
        actor: User,
        skip_invalid: bool = False,
        request_id: str | None = None,
    ) -> ImportCommitResponse:
        batch = db.get(ImportBatch, batch_id)
        if not batch:
            raise DomainException(
                code="IMPORT_BATCH_NOT_FOUND",
                message=f"Import batch '{batch_id}' was not found.",
                status_code=404,
            )

        if batch.status != ImportStatus.PREVIEW:
            raise DomainException(
                code="INVALID_BATCH_STATUS",
                message=f"Import batch is in '{enum_val(batch.status)}' state and cannot be confirmed.",
                status_code=422,
            )

        # Enforce all-or-nothing unless skip_invalid=True (Task P4.7)
        if batch.invalid_rows > 0 and not skip_invalid:
            raise DomainException(
                code="BATCH_HAS_ERRORS",
                message=(
                    f"Batch has {batch.invalid_rows} invalid row(s). "
                    "Confirmation rejected. Correct the CSV or explicitly set skip_invalid=true to proceed."
                ),
                status_code=422,
            )

        staged_rows: list[dict[str, Any]] = batch.errors_json.get("staged_rows", [])
        if not staged_rows:
            raise DomainException(
                code="NO_VALID_ROWS_TO_COMMIT",
                message="There are no valid staged rows in this batch to commit.",
                status_code=422,
            )

        stale_cycles: list[str] = []

        # Bulk Insert execution in a single atomic transaction
        try:
            if batch.import_type == ImportType.STUDENTS:
                students_to_add = [
                    Student(
                        student_number=r["student_number"],
                        full_name=r["full_name"],
                        department_id=r["department_id"],
                        program_id=r.get("program_id"),
                        semester=r["semester"],
                        email=r.get("email"),
                        status=EntityStatus.ACTIVE,
                    )
                    for r in staged_rows
                ]
                db.add_all(students_to_add)

            elif batch.import_type == ImportType.SUBJECTS:
                subjects_to_add = [
                    Subject(
                        subject_code=r["subject_code"],
                        subject_name=r["subject_name"],
                        department_id=r["department_id"],
                        semester=r["semester"],
                        credits=r.get("credits", 3.0),
                        default_duration_minutes=r.get("default_duration_minutes", 180),
                        priority=r.get("priority", 1),
                        status=EntityStatus.ACTIVE,
                    )
                    for r in staged_rows
                ]
                db.add_all(subjects_to_add)

            elif batch.import_type == ImportType.ENROLLMENTS:
                enrollments_to_add = [
                    Enrollment(
                        student_id=r["student_id"],
                        subject_id=r["subject_id"],
                        cycle_id=r["cycle_id"],
                        status=EnrollmentStatus.ACTIVE,
                    )
                    for r in staged_rows
                ]
                db.add_all(enrollments_to_add)

                # Staleness signaling (Task P4.10)
                if batch.cycle_id:
                    staleness_service.bump_cycle_data_version(db, batch.cycle_id)
                    stale_cycles.append(batch.cycle_id)

            batch.status = ImportStatus.COMMITTED
            batch.committed_at = datetime.now(UTC)

            # Audit record (Task P4.14)
            audit_service.record(
                db=db,
                action=AuditAction.IMPORT_COMMIT,
                entity_type="import_batch",
                actor_email=actor.email,
                actor_id=actor.id,
                entity_id=batch.id,
                after={
                    "import_type": enum_val(batch.import_type),
                    "committed_rows": len(staged_rows),
                    "skipped_rows": batch.invalid_rows if skip_invalid else 0,
                    "stale_cycles": stale_cycles,
                },
                request_id=request_id,
            )
            db.commit()
            db.refresh(batch)

        except Exception as e:
            import logging

            logging.getLogger("exam_scheduler").error(
                f"Commit error: {type(e)}: {e}", exc_info=True
            )
            db.rollback()
            raise DomainException(
                code="IMPORT_COMMIT_FAILED",
                message=f"Database transaction failed during bulk insert: {e}",
                status_code=500,
            ) from e

        return ImportCommitResponse(
            batch_id=batch.id,
            import_type=batch.import_type,
            status=batch.status,
            committed_rows=len(staged_rows),
            skipped_rows=batch.invalid_rows if skip_invalid else 0,
            stale_cycles=stale_cycles,
            message=f"Successfully committed {len(staged_rows)} records for {enum_val(batch.import_type)}.",
        )

    # ==========================================================================
    # Cancellation (Task P4.11)
    # ==========================================================================
    @staticmethod
    def cancel_batch(
        db: Session, batch_id: str, actor: User, request_id: str | None = None
    ) -> ImportCommitResponse:
        batch = db.get(ImportBatch, batch_id)
        if not batch:
            raise DomainException(
                code="IMPORT_BATCH_NOT_FOUND",
                message=f"Import batch '{batch_id}' was not found.",
                status_code=404,
            )

        if batch.status != ImportStatus.PREVIEW:
            raise DomainException(
                code="INVALID_BATCH_STATUS",
                message=f"Cannot cancel import batch in '{enum_val(batch.status)}' state.",
                status_code=422,
            )

        batch.status = ImportStatus.CANCELLED
        audit_service.record(
            db=db,
            action=AuditAction.IMPORT_CANCEL,
            entity_type="import_batch",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=batch.id,
            after={"status": "cancelled"},
            request_id=request_id,
        )
        db.commit()
        db.refresh(batch)

        return ImportCommitResponse(
            batch_id=batch.id,
            import_type=batch.import_type,
            status=batch.status,
            committed_rows=0,
            skipped_rows=0,
            stale_cycles=[],
            message="Import batch has been cancelled.",
        )

    # ==========================================================================
    # Diagnostic Error CSV & Templates (Tasks P4.6, P4.15)
    # ==========================================================================
    @staticmethod
    def generate_error_csv(db: Session, batch_id: str) -> str:
        batch = db.get(ImportBatch, batch_id)
        if not batch:
            raise DomainException(
                code="IMPORT_BATCH_NOT_FOUND",
                message=f"Import batch '{batch_id}' was not found.",
                status_code=404,
            )

        errors = batch.errors_json.get("errors", [])
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Row", "Field", "Value", "Error Code", "Error Message", "Suggestion"])

        for e in errors:
            writer.writerow(
                [
                    e.get("row", ""),
                    e.get("field", ""),
                    sanitize_formula_injection(str(e.get("value", ""))),
                    e.get("errorCode", ""),
                    e.get("message", ""),
                    e.get("suggestion", ""),
                ]
            )

        return output.getvalue()

    @staticmethod
    def get_csv_template(import_type: ImportType) -> str:
        """Returns downloadable sample CSV template matching PRD §FR-05."""
        if import_type == ImportType.STUDENTS:
            return "student_id,student_name,department,semester\nS001,Student One,CSE,5\nS002,Student Two,CSE,5\nS003,Student Three,IT,5\n"
        elif import_type == ImportType.SUBJECTS:
            return "subject_code,subject_name,department,semester,duration_minutes\nCS301,Data Structures,CSE,5,180\nCS302,Operating Systems,CSE,5,180\nCS303,Database Systems,CSE,5,180\n"
        elif import_type == ImportType.ENROLLMENTS:
            return "student_id,subject_code\nS001,CS301\nS001,CS302\nS002,CS301\nS002,CS303\nS003,CS302\nS003,CS303\n"
        else:
            raise DomainException(
                code="INVALID_IMPORT_TYPE",
                message=f"No template available for '{import_type}'.",
                status_code=422,
            )


import_service = ImportService()
