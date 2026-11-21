import uuid
from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.enums import CycleStatus, EnrollmentStatus, EntityStatus

if TYPE_CHECKING:
    from app.models.academic import AcademicYear, Semester, Student, Subject
    from app.models.graph import ConflictGraphSnapshot
    from app.models.schedule import ExamAssignment, ScheduleRun, ScheduleVersion


class SchedulingCycle(Base):
    __tablename__ = "scheduling_cycles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    academic_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    semester_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Fall 2026 End-Term"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    status: Mapped[CycleStatus] = mapped_column(
        String(32), default=CycleStatus.DRAFT, nullable=False
    )

    # Configuration JSON: sessions, holidays, weekdays, bounds, weights (Task P5.2)
    configuration_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Staleness tracking counter (Task P3.16 / P6.6)
    data_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (CheckConstraint("end_date >= start_date", name="ck_cycle_dates"),)

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="cycles")
    semester: Mapped[Optional["Semester"]] = relationship("Semester", back_populates="cycles")
    exams: Mapped[list["Exam"]] = relationship(
        "Exam", back_populates="cycle", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment", back_populates="cycle", cascade="all, delete-orphan"
    )
    time_slots: Mapped[list["TimeSlot"]] = relationship(
        "TimeSlot", back_populates="cycle", cascade="all, delete-orphan"
    )
    graph_snapshots: Mapped[list["ConflictGraphSnapshot"]] = relationship(
        "ConflictGraphSnapshot", back_populates="cycle"
    )
    schedule_runs: Mapped[list["ScheduleRun"]] = relationship("ScheduleRun", back_populates="cycle")
    schedule_versions: Mapped[list["ScheduleVersion"]] = relationship(
        "ScheduleVersion", back_populates="cycle"
    )


class Exam(Base):
    """An examination event representing a vertex in the conflict graph (ADR-002)."""

    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheduling_cycle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scheduling_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    preferred_dates: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    restricted_dates: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)

    status: Mapped[EntityStatus] = mapped_column(
        String(32), default=EntityStatus.ACTIVE, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("scheduling_cycle_id", "subject_id", name="uq_exam_cycle_subject"),
        CheckConstraint("duration_minutes > 0", name="ck_exam_duration_positive"),
    )

    # Relationships
    cycle: Mapped["SchedulingCycle"] = relationship("SchedulingCycle", back_populates="exams")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="exams")
    assignments: Mapped[list["ExamAssignment"]] = relationship(
        "ExamAssignment", back_populates="exam"
    )


class Enrollment(Base):
    """Student enrollment scoped to a scheduling cycle (ADR-003)."""

    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cycle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scheduling_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        String(32), default=EnrollmentStatus.ACTIVE, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "subject_id", "cycle_id", name="uq_enrollment_student_subject_cycle"
        ),
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="enrollments")
    cycle: Mapped["SchedulingCycle"] = relationship("SchedulingCycle", back_populates="enrollments")


class TimeSlot(Base):
    """A concrete calendar window on a specific date with a daily session window (ADR-004)."""

    __tablename__ = "time_slots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheduling_cycle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scheduling_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    session_label: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # e.g., "Morning", "Afternoon"
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Stable calendar order index
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "scheduling_cycle_id", "date", "start_time", name="uq_slot_cycle_date_time"
        ),
        CheckConstraint("duration_minutes > 0", name="ck_slot_duration_positive"),
        CheckConstraint("end_time > start_time", name="ck_slot_end_after_start"),
    )

    # Relationships
    cycle: Mapped["SchedulingCycle"] = relationship("SchedulingCycle", back_populates="time_slots")
    assignments: Mapped[list["ExamAssignment"]] = relationship(
        "ExamAssignment", back_populates="time_slot"
    )
