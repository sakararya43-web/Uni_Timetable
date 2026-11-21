"""Publishing, Student Timetables, Master Timetables, PDF/Excel Exports, and Reports Service.

PRD §16, §18.7, §20, §21, §23, §26.5, Tasks P10.1 - P10.21.
"""

import csv
from datetime import UTC, date, datetime
from io import BytesIO, StringIO
from typing import Any

import openpyxl  # type: ignore[import-untyped]
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # type: ignore[import-untyped]
from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import landscape, letter  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # type: ignore[import-untyped]
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.middleware.error_handler import DomainException
from app.models.academic import Student, Subject
from app.models.audit import AuditLog
from app.models.enums import (
    AuditAction,
    CycleStatus,
    EnrollmentStatus,
    RoleEnum,
    ScheduleStatus,
    enum_val,
)
from app.models.schedule import ExamAssignment, ScheduleVersion
from app.models.scheduling import Enrollment, Exam, SchedulingCycle, TimeSlot
from app.models.user import User
from app.schemas.publishing_reporting import (
    AuditLogListItem,
    AuditLogListResponse,
    CycleReportSummaryResponse,
    DateDistributionItem,
    MasterTimetableEntry,
    MasterTimetableResponse,
    MultiExamStudentItem,
    PublishScheduleRequest,
    ScheduleDistributionResponse,
    SessionDistributionItem,
    StudentTimetableEntry,
    StudentTimetableResponse,
)
from app.services.audit_service import audit_service
from app.services.graph_service import graph_service
from app.services.schedule_validator import validate_schedule


def sanitize_csv_cell(val: Any) -> str:
    """Neutralizes formula injection for CSV export (P10.9)."""
    s = "" if val is None else str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


class PublishingService:
    """Orchestrates timetable publishing, student views, document export, and audit queries."""

    @staticmethod
    def publish_schedule(
        db: Session,
        version_id: str,
        req: PublishScheduleRequest,
        actor: User,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Atomically publishes a schedule version with definitive validation and immutability (P10.1 - P10.4)."""
        ver = db.get(ScheduleVersion, version_id)
        if not ver:
            raise DomainException(code="SCHEDULE_VERSION_NOT_FOUND", message="Schedule version not found.", status_code=404)

        current_status = enum_val(ver.status)
        if current_status == enum_val(ScheduleStatus.ARCHIVED):
            raise DomainException(
                code="CANNOT_PUBLISH_ARCHIVED",
                message="Cannot publish an archived schedule version.",
                status_code=400,
            )

        cycle = db.get(SchedulingCycle, ver.scheduling_cycle_id)
        if not cycle:
            raise DomainException(code="CYCLE_NOT_FOUND", message="Cycle not found.", status_code=404)

        # 1. Ensure not stale relative to enrollments/graph
        is_stale, _, _ = graph_service.is_cycle_graph_stale(db, cycle.id)
        if is_stale:
            raise DomainException(
                code="SCHEDULE_STALE",
                message="Academic or enrollment data has changed since this version was generated. Regenerate before publishing.",
                status_code=409,
            )

        # 2. Run final validation recomputed directly from DB enrollments (P10.2)
        exams_list = list(
            db.scalars(select(Exam).where(Exam.scheduling_cycle_id == cycle.id).options(joinedload(Exam.subject))).all()
        )
        slots_list = list(db.scalars(select(TimeSlot).where(TimeSlot.scheduling_cycle_id == cycle.id)).all())
        assignments_list = list(
            db.scalars(select(ExamAssignment).where(ExamAssignment.schedule_version_id == ver.id)).all()
        )

        exams_dict = {
            e.id: {
                "id": e.id,
                "subject_code": e.subject.subject_code,
                "duration_minutes": e.duration_minutes,
                "restricted_dates": e.restricted_dates or [],
                "preferred_dates": e.preferred_dates or [],
                "cycle_id": e.scheduling_cycle_id,
                "locked_slot_id": None,
            }
            for e in exams_list
        }
        slots_dict = {
            s.id: {
                "id": s.id,
                "date": s.date,
                "start_time": s.start_time.strftime("%H:%M") if hasattr(s.start_time, "strftime") else str(s.start_time),
                "end_time": s.end_time.strftime("%H:%M") if hasattr(s.end_time, "strftime") else str(s.end_time),
                "duration_minutes": s.duration_minutes,
                "is_enabled": s.enabled,
                "slot_index": s.slot_index,
                "session_label": s.session_label,
                "cycle_id": s.scheduling_cycle_id,
            }
            for s in slots_list
        }

        assignments_payload = [
            {
                "exam_id": a.exam_id,
                "time_slot_id": a.time_slot_id,
                "color_id": a.color_id,
                "locked": a.locked,
            }
            for a in assignments_list
        ]

        enrollments = list(
            db.execute(
                select(Enrollment.student_id, Exam.id)
                .join(Exam, Exam.subject_id == Enrollment.subject_id)
                .where(
                    Enrollment.cycle_id == cycle.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                    Exam.scheduling_cycle_id == cycle.id,
                )
            ).all()
        )
        enrollments_tuples = [(str(r[0]), str(r[1])) for r in enrollments]

        validation_report = validate_schedule(
            exams=exams_dict,
            slots=slots_dict,
            assignments=assignments_payload,
            enrollments=enrollments_tuples,
            cycle_id=cycle.id,
        )

        if not validation_report.valid:
            msg = validation_report.hard_violations[0].message if validation_report.hard_violations else "Hard constraint violation."
            raise DomainException(
                code="PUBLISH_FAILED_INVALID_SCHEDULE",
                message=f"Cannot publish schedule with hard constraint violations: {msg}",
                status_code=422,
            )

        # 3. Archive / supersede any previously published version for this cycle (P10.3)
        prev_published = list(
            db.scalars(
                select(ScheduleVersion).where(
                    ScheduleVersion.scheduling_cycle_id == cycle.id,
                    ScheduleVersion.status == ScheduleStatus.PUBLISHED,
                    ScheduleVersion.id != ver.id,
                )
            ).all()
        )
        for prev in prev_published:
            prev.status = ScheduleStatus.ARCHIVED
        if prev_published:
            db.flush()

        # 4. Mark version Published
        ver.status = ScheduleStatus.PUBLISHED
        ver.published_at = datetime.now(UTC)
        ver.published_by = actor.id

        # 5. Advance cycle status to Published
        cycle.status = CycleStatus.PUBLISHED

        # 6. Audit
        audit_service.record(
            db=db,
            action=AuditAction.SCHEDULE_PUBLISH,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="schedule_version",
            entity_id=ver.id,
            after={
                "versionNumber": ver.version_number,
                "cycleId": cycle.id,
                "publishedAt": ver.published_at.isoformat(),
                "notes": req.notes,
                "supersededVersions": [p.id for p in prev_published],
            },
            request_id=request_id,
        )

        db.commit()
        db.refresh(ver)
        return ver

    @staticmethod
    def get_student_timetable(
        db: Session,
        student_id: str,
        cycle_id: str | None = None,
        actor: User | None = None,
    ) -> StudentTimetableResponse:
        """Fetches a privacy-compliant individual timetable for a student (P10.5, P10.8)."""
        student = db.get(Student, student_id)
        if not student:
            raise DomainException(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=404)

        # Student self-access check
        if actor and enum_val(actor.role) == enum_val(RoleEnum.STUDENT):
            if student.user_id != actor.id and student.email != actor.email:
                raise DomainException(code="FORBIDDEN", message="Students may only access their own timetable.", status_code=403)

        # Find target cycle
        if cycle_id:
            cycle = db.get(SchedulingCycle, cycle_id)
        else:
            cycle = db.scalar(
                select(SchedulingCycle)
                .where(SchedulingCycle.status == CycleStatus.PUBLISHED)
                .order_by(SchedulingCycle.created_at.desc())
                .limit(1)
            )

        if not cycle:
            raise DomainException(code="PUBLISHED_SCHEDULE_NOT_FOUND", message="No published timetable cycle found.", status_code=404)

        # Find active published schedule version
        published_version = db.scalar(
            select(ScheduleVersion)
            .where(
                ScheduleVersion.scheduling_cycle_id == cycle.id,
                ScheduleVersion.status == ScheduleStatus.PUBLISHED,
            )
            .order_by(ScheduleVersion.version_number.desc())
            .limit(1)
        )
        if not published_version:
            raise DomainException(code="PUBLISHED_SCHEDULE_NOT_FOUND", message="No published schedule version found for this cycle.", status_code=404)

        # Load student's enrolled subjects
        enrolled_subject_ids = list(
            db.scalars(
                select(Enrollment.subject_id).where(
                    Enrollment.student_id == student.id,
                    Enrollment.cycle_id == cycle.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            ).all()
        )

        # Fetch assignments for enrolled subjects
        assignments = list(
            db.scalars(
                select(ExamAssignment)
                .join(Exam, Exam.id == ExamAssignment.exam_id)
                .where(
                    ExamAssignment.schedule_version_id == published_version.id,
                    Exam.subject_id.in_(enrolled_subject_ids),
                )
                .options(
                    joinedload(ExamAssignment.exam).joinedload(Exam.subject).joinedload(Subject.department),
                    joinedload(ExamAssignment.time_slot),
                )
            ).all()
        )

        entries: list[StudentTimetableEntry] = []
        for a in assignments:
            slot = a.time_slot
            sub = a.exam.subject
            start_str = slot.start_time.strftime("%H:%M") if hasattr(slot.start_time, "strftime") else str(slot.start_time)
            end_str = slot.end_time.strftime("%H:%M") if hasattr(slot.end_time, "strftime") else str(slot.end_time)

            entries.append(
                StudentTimetableEntry(
                    subject_code=sub.subject_code,
                    subject_name=sub.subject_name,
                    department_code=sub.department.code if sub.department else None,
                    exam_date=slot.date,
                    start_time=start_str,
                    end_time=end_str,
                    duration_minutes=a.exam.duration_minutes,
                    session_label=slot.session_label or "",
                )
            )

        # Sort chronologically by date and start time
        entries.sort(key=lambda x: (x.examDate, x.startTime))

        return StudentTimetableResponse(
            student_id=student.id,
            student_number=student.student_number,
            student_name=student.full_name,
            cycle_id=cycle.id,
            cycle_name=cycle.name,
            schedule_version_id=published_version.id,
            version_number=published_version.version_number,
            published_at=published_version.published_at,
            exams=entries,
        )

    @staticmethod
    def get_my_timetable(db: Session, actor: User, cycle_id: str | None = None) -> StudentTimetableResponse:
        """Student convenience endpoint GET /me/timetable (P10.6)."""
        student = db.scalar(
            select(Student).where(
                (Student.user_id == actor.id) | (Student.email == actor.email)
            ).limit(1)
        )
        if not student:
            raise DomainException(code="STUDENT_PROFILE_NOT_FOUND", message="No linked student profile found for your account.", status_code=404)
        return PublishingService.get_student_timetable(db, student.id, cycle_id=cycle_id, actor=actor)

    @staticmethod
    def get_master_timetable(
        db: Session,
        version_id: str,
        department_id: str | None = None,
        date_filter: str | None = None,
        session_label: str | None = None,
        actor: User | None = None,
    ) -> MasterTimetableResponse:
        """Fetches master examination timetable with role-based filtering (P10.7, P10.12)."""
        ver = db.get(ScheduleVersion, version_id)
        if not ver:
            raise DomainException(code="SCHEDULE_VERSION_NOT_FOUND", message="Schedule version not found.", status_code=404)

        cycle = ver.cycle

        stmt = (
            select(ExamAssignment)
            .where(ExamAssignment.schedule_version_id == ver.id)
            .options(
                joinedload(ExamAssignment.exam).joinedload(Exam.subject).joinedload(Subject.department),
                joinedload(ExamAssignment.time_slot),
            )
        )
        assignments = list(db.scalars(stmt).all())

        exam_student_counts = dict(
            db.execute(
                select(Exam.id, func.count(Enrollment.id))
                .join(Enrollment, (Enrollment.subject_id == Exam.subject_id) & (Enrollment.cycle_id == Exam.scheduling_cycle_id))
                .where(
                    Exam.scheduling_cycle_id == cycle.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
                .group_by(Exam.id)
            ).all()
        )

        entries: list[MasterTimetableEntry] = []
        for a in assignments:
            sub = a.exam.subject
            dept = sub.department if sub else None
            slot = a.time_slot

            # Department filter & role scoping
            if department_id and sub.department_id != department_id:
                continue
            if actor and enum_val(actor.role) in (enum_val(RoleEnum.COORDINATOR), enum_val(RoleEnum.FACULTY)):
                if actor.department_id and sub.department_id != actor.department_id:
                    continue

            if date_filter and str(slot.date) != str(date_filter):
                continue
            if session_label and slot.session_label != session_label:
                continue

            start_str = slot.start_time.strftime("%H:%M") if hasattr(slot.start_time, "strftime") else str(slot.start_time)
            end_str = slot.end_time.strftime("%H:%M") if hasattr(slot.end_time, "strftime") else str(slot.end_time)

            entries.append(
                MasterTimetableEntry(
                    assignment_id=a.id,
                    exam_id=a.exam_id,
                    subject_code=sub.subject_code,
                    subject_name=sub.subject_name,
                    department_code=dept.code if dept else None,
                    department_name=dept.name if dept else None,
                    slot_date=slot.date,
                    start_time=start_str,
                    end_time=end_str,
                    duration_minutes=a.exam.duration_minutes,
                    session_label=slot.session_label or "",
                    student_count=exam_student_counts.get(a.exam_id, 0),
                    locked=a.locked,
                    manual_override=a.manual_override,
                )
            )

        entries.sort(key=lambda x: (x.slotDate, x.startTime, x.subjectCode))

        return MasterTimetableResponse(
            schedule_version_id=ver.id,
            version_number=ver.version_number,
            cycle_id=cycle.id,
            cycle_name=cycle.name,
            status=ver.status,
            published_at=ver.published_at,
            total_exams=len(entries),
            entries=entries,
        )

    @staticmethod
    def generate_csv_export(
        db: Session,
        version_id: str,
        actor: User,
    ) -> str:
        """Generates formula-injection sanitized RFC 4180 CSV export of timetable (P10.9, P10.13)."""
        master = PublishingService.get_master_timetable(db, version_id, actor=actor)

        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Headers
        writer.writerow([
            "Subject Code",
            "Subject Name",
            "Department",
            "Exam Date",
            "Start Time",
            "End Time",
            "Duration (Min)",
            "Session",
            "Students Enrolled",
            "Locked",
            "Manual Override",
        ])

        for e in master.entries:
            writer.writerow([
                sanitize_csv_cell(e.subjectCode),
                sanitize_csv_cell(e.subjectName),
                sanitize_csv_cell(e.departmentCode or ""),
                sanitize_csv_cell(str(e.slotDate)),
                sanitize_csv_cell(e.startTime),
                sanitize_csv_cell(e.endTime),
                sanitize_csv_cell(e.durationMinutes),
                sanitize_csv_cell(e.sessionLabel),
                sanitize_csv_cell(e.studentCount),
                sanitize_csv_cell("Yes" if e.locked else "No"),
                sanitize_csv_cell("Yes" if e.manualOverride else "No"),
            ])

        audit_service.record(
            db=db,
            action=AuditAction.EXPORT,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="schedule_version",
            entity_id=version_id,
            after={"exportType": "csv", "totalExams": master.totalExams},
        )
        db.commit()
        return output.getvalue()

    @staticmethod
    def generate_pdf_export(
        db: Session,
        version_id: str,
        actor: User,
    ) -> bytes:
        """Generates formatted publication-grade PDF timetable using ReportLab (P10.10)."""
        master = PublishingService.get_master_timetable(db, version_id, actor=actor)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        elements: list[Any] = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1e293b"),
        )
        sub_style = ParagraphStyle(
            "SubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
        )
        cell_style = ParagraphStyle(
            "CellText",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
        )
        header_style = ParagraphStyle(
            "HeaderCell",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.white,
            fontName="Helvetica-Bold",
        )

        elements.append(Paragraph(f"<b>University Examination Timetable</b> — {master.cycleName}", title_style))
        status_txt = f"Version: {master.versionNumber} ({master.status.value}) | Total Examinations: {master.totalExams}"
        if master.publishedAt:
            status_txt += f" | Published: {master.publishedAt.strftime('%Y-%m-%d %H:%M UTC')}"
        elements.append(Paragraph(status_txt, sub_style))
        elements.append(Spacer(1, 14))

        # Table data
        data = [[
            Paragraph("Subject", header_style),
            Paragraph("Title", header_style),
            Paragraph("Dept", header_style),
            Paragraph("Date", header_style),
            Paragraph("Time", header_style),
            Paragraph("Dur", header_style),
            Paragraph("Session", header_style),
            Paragraph("Students", header_style),
        ]]

        for e in master.entries:
            data.append([
                Paragraph(f"<b>{e.subjectCode}</b>", cell_style),
                Paragraph(e.subjectName[:30], cell_style),
                Paragraph(e.departmentCode or "", cell_style),
                Paragraph(str(e.slotDate), cell_style),
                Paragraph(f"{e.startTime} - {e.endTime}", cell_style),
                Paragraph(f"{e.durationMinutes}m", cell_style),
                Paragraph(e.sessionLabel, cell_style),
                Paragraph(str(e.studentCount), cell_style),
            ])

        col_widths = [70, 190, 50, 70, 90, 45, 65, 55]
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ])
        )
        elements.append(t)

        doc.build(elements)
        audit_service.record(
            db=db,
            action=AuditAction.EXPORT,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="schedule_version",
            entity_id=version_id,
            after={"exportType": "pdf", "totalExams": master.totalExams},
        )
        db.commit()
        return buffer.getvalue()

    @staticmethod
    def generate_excel_export(
        db: Session,
        version_id: str,
        actor: User,
    ) -> bytes:
        """Generates structured multi-tab Excel workbook using OpenPyXL (P10.11)."""
        master = PublishingService.get_master_timetable(db, version_id, actor=actor)

        wb = openpyxl.Workbook()

        # Styles
        hdr_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        # Tab 1: All Examinations
        ws1 = wb.active
        ws1.title = "Master Timetable"

        headers = [
            "Subject Code", "Subject Name", "Department", "Exam Date",
            "Start Time", "End Time", "Duration (Min)", "Session",
            "Students Enrolled", "Locked", "Manual Override"
        ]
        ws1.append(headers)
        for col_num in range(1, len(headers) + 1):
            cell = ws1.cell(row=1, column=col_num)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for e in master.entries:
            row = [
                e.subjectCode, e.subjectName, e.departmentCode or "", str(e.slotDate),
                e.startTime, e.endTime, e.durationMinutes, e.sessionLabel,
                e.studentCount, "Yes" if e.locked else "No", "Yes" if e.manualOverride else "No"
            ]
            ws1.append(row)
            for col_num in range(1, len(row) + 1):
                c = ws1.cell(row=ws1.max_row, column=col_num)
                c.border = border

        for col in ws1.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws1.column_dimensions[col_letter].width = max(max_len + 3, 12)

        # Tab 2: By Department Summary
        ws2 = wb.create_sheet(title="By Department")
        ws2.append(["Department Code", "Department Name", "Exams Scheduled", "Student Sessions"])
        for col_num in range(1, 5):
            c = ws2.cell(row=1, column=col_num)
            c.fill = hdr_fill
            c.font = hdr_font

        dept_summary: dict[str, dict[str, Any]] = {}
        for e in master.entries:
            key = e.departmentCode or "GEN"
            if key not in dept_summary:
                dept_summary[key] = {"name": e.departmentName or "General", "exams": 0, "sessions": 0}
            dept_summary[key]["exams"] += 1
            dept_summary[key]["sessions"] += e.studentCount

        for dcode, ddata in sorted(dept_summary.items()):
            ws2.append([dcode, ddata["name"], ddata["exams"], ddata["sessions"]])
            for col_num in range(1, 5):
                ws2.cell(row=ws2.max_row, column=col_num).border = border

        for col in ws2.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws2.column_dimensions[col_letter].width = max(max_len + 3, 14)

        buf = BytesIO()
        wb.save(buf)
        audit_service.record(
            db=db,
            action=AuditAction.EXPORT,
            actor_email=actor.email,
            actor_id=actor.id,
            entity_type="schedule_version",
            entity_id=version_id,
            after={"exportType": "excel", "totalExams": master.totalExams},
        )
        db.commit()
        return buf.getvalue()

    @staticmethod
    def get_cycle_summary_report(db: Session, cycle_id: str) -> CycleReportSummaryResponse:
        """Computes summary statistics for a cycle (P10.15)."""
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(code="CYCLE_NOT_FOUND", message="Cycle not found.", status_code=404)

        total_subjects = db.scalar(select(func.count(Subject.id))) or 0
        total_exams = db.scalar(select(func.count(Exam.id)).where(Exam.scheduling_cycle_id == cycle.id)) or 0
        total_students = db.scalar(select(func.count(Student.id))) or 0
        total_enrollments = db.scalar(
            select(func.count(Enrollment.id)).where(
                Enrollment.cycle_id == cycle.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        ) or 0
        total_slots = db.scalar(select(func.count(TimeSlot.id)).where(TimeSlot.scheduling_cycle_id == cycle.id)) or 0

        latest_snapshot = graph_service.get_latest_snapshot(db, cycle.id)
        vertices = latest_snapshot.vertex_count if latest_snapshot else 0
        edges = latest_snapshot.edge_count if latest_snapshot else 0
        avg_deg = latest_snapshot.avg_degree if latest_snapshot else 0.0

        latest_pub = db.scalar(
            select(ScheduleVersion)
            .where(
                ScheduleVersion.scheduling_cycle_id == cycle.id,
                ScheduleVersion.status == ScheduleStatus.PUBLISHED,
            )
            .order_by(ScheduleVersion.version_number.desc())
            .limit(1)
        )

        # Count slots used in latest version
        slots_used = 0
        if latest_pub:
            slots_used = db.scalar(
                select(func.count(func.distinct(ExamAssignment.time_slot_id)))
                .where(ExamAssignment.schedule_version_id == latest_pub.id)
            ) or 0

        return CycleReportSummaryResponse(
            cycle_id=cycle.id,
            cycle_name=cycle.name,
            exam_start_date=cycle.start_date,
            exam_end_date=cycle.end_date,
            total_subjects=total_subjects,
            total_exams=total_exams,
            total_students=total_students,
            total_enrollments=total_enrollments,
            total_slots=total_slots,
            slots_used=slots_used,
            graph_vertices=vertices,
            graph_edges=edges,
            average_degree=round(avg_deg, 2),
            latest_published_version=latest_pub.version_number if latest_pub else None,
            latest_published_at=latest_pub.published_at if latest_pub else None,
        )

    @staticmethod
    def get_schedule_distribution_report(db: Session, version_id: str) -> ScheduleDistributionResponse:
        """Computes workload distribution across dates, sessions, and multi-exam days (P10.16)."""
        ver = db.get(ScheduleVersion, version_id)
        if not ver:
            raise DomainException(code="SCHEDULE_VERSION_NOT_FOUND", message="Schedule version not found.", status_code=404)

        assignments = list(
            db.scalars(
                select(ExamAssignment)
                .where(ExamAssignment.schedule_version_id == ver.id)
                .options(joinedload(ExamAssignment.time_slot), joinedload(ExamAssignment.exam))
            ).all()
        )

        exam_student_counts = dict(
            db.execute(
                select(Exam.id, func.count(Enrollment.id))
                .join(Enrollment, (Enrollment.subject_id == Exam.subject_id) & (Enrollment.cycle_id == Exam.scheduling_cycle_id))
                .where(
                    Exam.scheduling_cycle_id == ver.scheduling_cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
                .group_by(Exam.id)
            ).all()
        )

        by_date: dict[date, dict[str, int]] = {}
        by_session: dict[str, dict[str, int]] = {}

        for a in assignments:
            slot = a.time_slot
            d = slot.date
            sess = slot.session_label or "Standard"
            count = exam_student_counts.get(a.exam_id, 0)

            by_date.setdefault(d, {"examCount": 0, "studentSessions": 0})
            by_date[d]["examCount"] += 1
            by_date[d]["studentSessions"] += count

            by_session.setdefault(sess, {"examCount": 0, "studentSessions": 0})
            by_session[sess]["examCount"] += 1
            by_session[sess]["studentSessions"] += count

        date_items = [
            DateDistributionItem(date=d, exam_count=v["examCount"], student_sessions=v["studentSessions"])
            for d, v in sorted(by_date.items())
        ]
        session_items = [
            SessionDistributionItem(session_label=s, exam_count=v["examCount"], student_sessions=v["studentSessions"])
            for s, v in sorted(by_session.items())
        ]

        # Multi-exam days calculation
        enrollments = list(
            db.execute(
                select(Enrollment.student_id, Exam.id)
                .join(Exam, Exam.subject_id == Enrollment.subject_id)
                .where(
                    Enrollment.cycle_id == ver.scheduling_cycle_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                    Exam.scheduling_cycle_id == ver.scheduling_cycle_id,
                )
            ).all()
        )
        exam_date_map: dict[str, date] = {a.exam_id: a.time_slot.date for a in assignments}
        student_days: dict[str, dict[date, int]] = {}
        for sid, eid in enrollments:
            slot_date: date | None = exam_date_map.get(str(eid))
            if slot_date is not None:
                student_days.setdefault(str(sid), {}).setdefault(slot_date, 0)
                student_days[str(sid)][slot_date] += 1

        histogram: dict[int, int] = {}
        for _sid, dmap in student_days.items():
            for _d, count in dmap.items():
                histogram[count] = histogram.get(count, 0) + 1

        multi_exam_items = [
            MultiExamStudentItem(exams_per_day=k, student_count=v)
            for k, v in sorted(histogram.items())
        ]

        return ScheduleDistributionResponse(
            schedule_version_id=ver.id,
            version_number=ver.version_number,
            by_date=date_items,
            by_session=session_items,
            multi_exam_days=multi_exam_items,
        )

    @staticmethod
    def get_audit_logs(
        db: Session,
        action: AuditAction | None = None,
        entity_type: str | None = None,
        actor_email: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogListResponse:
        """Queries tamper-evident audit records with administrative filters (P10.20)."""
        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if actor_email:
            stmt = stmt.where(AuditLog.actor_email.ilike(f"%{actor_email}%"))
        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(db.scalars(stmt.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)).all())

        items = [
            AuditLogListItem(
                id=r.id,
                actor_id=r.actor_id,
                actor_email=r.actor_email,
                action=r.action,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                before_state=r.before_state,
                after_state=r.after_state,
                request_id=r.request_id,
                timestamp=r.timestamp,
            )
            for r in rows
        ]

        return AuditLogListResponse(total=total, items=items)


publishing_service = PublishingService()
