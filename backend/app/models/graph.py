import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base

if TYPE_CHECKING:
    from app.models.schedule import ScheduleRun
    from app.models.scheduling import Exam, SchedulingCycle


class ConflictGraphSnapshot(Base):
    """Immutable point-in-time snapshot of the conflict graph G=(V,E) (ADR-006)."""

    __tablename__ = "conflict_graph_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheduling_cycle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scheduling_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    vertex_count: Mapped[int] = mapped_column(Integer, nullable=False)
    edge_count: Mapped[int] = mapped_column(Integer, nullable=False)
    density: Mapped[float] = mapped_column(Float, nullable=False)
    avg_degree: Mapped[float] = mapped_column(Float, nullable=False)
    max_degree: Mapped[int] = mapped_column(Integer, nullable=False)
    chromatic_lower_bound: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Cryptographic SHA-256 hash of canonical sorted enrollments (PRD §11, Task P6.6)
    enrollment_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Full serialized JSON adjacency for instant visualizer and algorithm loading
    graph_data_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("scheduling_cycle_id", "version", name="uq_graph_snapshot_cycle_version"),
    )

    # Relationships
    cycle: Mapped["SchedulingCycle"] = relationship(
        "SchedulingCycle", back_populates="graph_snapshots"
    )
    edges: Mapped[list["ConflictEdge"]] = relationship(
        "ConflictEdge", back_populates="graph_snapshot", cascade="all, delete-orphan"
    )
    schedule_runs: Mapped[list["ScheduleRun"]] = relationship(
        "ScheduleRun", back_populates="graph_snapshot"
    )


class ConflictEdge(Base):
    """Normalized edge record storing shared student conflict counts (ADR-006)."""

    __tablename__ = "conflict_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_snapshot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conflict_graph_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_id_a: Mapped[str] = mapped_column(
        String(36), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exam_id_b: Mapped[str] = mapped_column(
        String(36), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shared_student_count: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        # Enforces exam_id_a < exam_id_b: guarantees no self-loops and no mirror duplicates (Task P2.3)
        CheckConstraint("exam_id_a < exam_id_b", name="ck_edge_normalized_order"),
        CheckConstraint("shared_student_count >= 1", name="ck_edge_positive_weight"),
        UniqueConstraint(
            "graph_snapshot_id", "exam_id_a", "exam_id_b", name="uq_edge_pair_per_snapshot"
        ),
    )

    # Relationships
    graph_snapshot: Mapped["ConflictGraphSnapshot"] = relationship(
        "ConflictGraphSnapshot", back_populates="edges"
    )
    exam_a: Mapped["Exam"] = relationship("Exam", foreign_keys=[exam_id_a])
    exam_b: Mapped["Exam"] = relationship("Exam", foreign_keys=[exam_id_b])
