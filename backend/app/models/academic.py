import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.enums import EntityStatus

if TYPE_CHECKING:
    from app.models.scheduling import Enrollment, Exam, SchedulingCycle
    from app.models.user import User


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="department")
    programs: Mapped[list["Program"]] = relationship("Program", back_populates="department")
    subjects: Mapped[list["Subject"]] = relationship("Subject", back_populates="department")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="department")


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # e.g., "2026-2027"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
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

    __table_args__ = (CheckConstraint("end_date >= start_date", name="ck_academic_year_dates"),)

    # Relationships
    semesters: Mapped[list["Semester"]] = relationship("Semester", back_populates="academic_year")
    cycles: Mapped[list["SchedulingCycle"]] = relationship(
        "SchedulingCycle", back_populates="academic_year"
    )


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    academic_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "Fall Semester", "Sem 5"
    number: Mapped[int] = mapped_column(Integer, nullable=False)
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
        UniqueConstraint("academic_year_id", "number", name="uq_semester_year_number"),
        CheckConstraint("number >= 1 AND number <= 16", name="ck_semester_number_range"),
    )

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="semesters")
    cycles: Mapped[list["SchedulingCycle"]] = relationship(
        "SchedulingCycle", back_populates="semester"
    )


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="programs")
    subjects: Mapped[list["Subject"]] = relationship("Subject", back_populates="program")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="program")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    program_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
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
        CheckConstraint("semester >= 1 AND semester <= 16", name="ck_student_semester_range"),
    )

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="students")
    program: Mapped[Optional["Program"]] = relationship("Program", back_populates="students")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="student_profile")
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="student")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Natural institution-wide unique code (ADR-009)
    subject_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    program_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    credits: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)
    default_duration_minutes: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
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
        CheckConstraint("default_duration_minutes > 0", name="ck_subject_duration_positive"),
        CheckConstraint("semester >= 1 AND semester <= 16", name="ck_subject_semester_range"),
    )

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="subjects")
    program: Mapped[Optional["Program"]] = relationship("Program", back_populates="subjects")
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="subject")
    exams: Mapped[list["Exam"]] = relationship("Exam", back_populates="subject")
