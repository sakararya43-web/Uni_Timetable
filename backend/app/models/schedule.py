import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.enums import ScheduleRunStatus, ScheduleStatus

if TYPE_CHECKING:
    from app.models.graph import ConflictGraphSnapshot
    from app.models.scheduling import Exam, SchedulingCycle, TimeSlot


class ScheduleRun(Base):
    """An audited execution record of an algorithm on a graph snapshot (PRD §17.13, Task P8.11)."""

    __tablename__ = "schedule_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheduling_cycle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scheduling_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    graph_snapshot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conflict_graph_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    algorithm: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # dsatur, welsh_powell, greedy
    algorithm_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    colors_used: Mapped[int] = mapped_column(Integer, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    soft_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[ScheduleRunStatus] = mapped_column(
        String(64), default=ScheduleRunStatus.RUNNING, nullable=False
    )

    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    result_summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    cycle: Mapped["SchedulingCycle"] = relationship(
        "SchedulingCycle", back_populates="schedule_runs"
    )
    graph_snapshot: Mapped["ConflictGraphSnapshot"] = relationship(
        "ConflictGraphSnapshot", back_populates="schedule_runs"
    )
    versions: Mapped[list["ScheduleVersion"]] = relationship(
        "ScheduleVersion", back_populates="schedule_run"
    )


class ScheduleVersion(Base):
    """A persisted timetable version with a defined lifecycle state (ADR-010)."""

    __tablename__ = "schedule_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheduling_cycle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scheduling_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    schedule_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("schedule_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[ScheduleStatus] = mapped_column(
        String(32), default=ScheduleStatus.CANDIDATE, nullable=False, index=True
    )

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    validation_report_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    soft_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Optimistic concurrency lock counter (Task P9.10)
    row_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
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
        UniqueConstraint("scheduling_cycle_id", "version_number", name="uq_version_cycle_number"),
        Index(
            "uq_cycle_single_published",
            "scheduling_cycle_id",
            unique=True,
            sqlite_where=(status == ScheduleStatus.PUBLISHED),
            postgresql_where=(status == ScheduleStatus.PUBLISHED),
        ),
    )

    # Relationships
    cycle: Mapped["SchedulingCycle"] = relationship(
        "SchedulingCycle", back_populates="schedule_versions"
    )
    schedule_run: Mapped[Optional["ScheduleRun"]] = relationship(
        "ScheduleRun", back_populates="versions"
    )
    assignments: Mapped[list["ExamAssignment"]] = relationship(
        "ExamAssignment", back_populates="schedule_version", cascade="all, delete-orphan"
    )


class ExamAssignment(Base):
    """A concrete assignment of an examination to a time slot within a version (PRD §17.15)."""

    __tablename__ = "exam_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("schedule_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("exams.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    time_slot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("time_slots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    color_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Locking & Manual override flags (Task P9.6, P9.12)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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
        # Hard constraint 3 & 7: prevents duplicate assignments within the same schedule version
        UniqueConstraint("schedule_version_id", "exam_id", name="uq_assignment_version_exam"),
    )

    # Relationships
    schedule_version: Mapped["ScheduleVersion"] = relationship(
        "ScheduleVersion", back_populates="assignments"
    )
    exam: Mapped["Exam"] = relationship("Exam", back_populates="assignments")
    time_slot: Mapped["TimeSlot"] = relationship("TimeSlot", back_populates="assignments")
