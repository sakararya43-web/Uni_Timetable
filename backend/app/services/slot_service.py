from datetime import date, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import DomainException
from app.models.enums import AuditAction, EntityStatus
from app.models.schedule import ExamAssignment
from app.models.scheduling import Exam, SchedulingCycle, TimeSlot
from app.models.user import User
from app.schemas.cycle import CapacitySummaryResponse, TimeSlotResponse
from app.services.audit_service import audit_service
from app.services.staleness_service import staleness_service


class SlotService:
    @staticmethod
    def fits(exam_duration_minutes: int, slot_duration_minutes: int) -> bool:
        """Duration compatibility helper (Task P5.12, PRD §13.4): ExamDuration <= SlotDuration."""
        return exam_duration_minutes <= slot_duration_minutes

    @staticmethod
    def generate_slots(
        start_date: date,
        end_date: date,
        config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Pure function slot generator (Task P5.6, P5.7, P5.8).
        Generates deterministic time slots from calendar dates, allowed weekdays, holidays,
        and daily session configurations. Per-date restrictions generate disabled slots.
        """
        if end_date < start_date:
            raise ValueError("end_date cannot be earlier than start_date.")

        exam_days: set[int] = set(
            config.get("examDaysOfWeek", config.get("exam_days_of_week", [1, 2, 3, 4, 5, 6]))
        )

        # Normalize holidays
        raw_holidays = config.get("holidays", [])
        holiday_dates: set[str] = set()
        for h in raw_holidays:
            if isinstance(h, str):
                holiday_dates.add(h)
            elif isinstance(h, dict) and "date" in h:
                holiday_dates.add(str(h["date"]))

        # Sessions configuration
        sessions = config.get("sessions", [])
        if not sessions:
            sessions = [
                {"label": "Morning", "startTime": "09:00", "endTime": "12:00", "enabled": True},
                {"label": "Afternoon", "startTime": "14:00", "endTime": "17:00", "enabled": True},
            ]

        # Special restrictions mapping: (date_str, session_label) -> restriction
        raw_restrictions = config.get("specialRestrictions", config.get("special_restrictions", []))
        restrictions_map: dict[tuple[str, str | None], dict[str, Any]] = {}
        for r in raw_restrictions:
            d_str = str(r.get("date", ""))
            s_label = r.get("sessionLabel") or r.get("session_label")
            restrictions_map[(d_str, s_label)] = r

        raw_slots: list[dict[str, Any]] = []
        current_date = start_date

        while current_date <= end_date:
            d_str = current_date.isoformat()
            is_allowed_weekday = current_date.isoweekday() in exam_days
            is_holiday = d_str in holiday_dates

            # If not allowed weekday or holiday, skip entire date (PRD §13.2)
            if is_allowed_weekday and not is_holiday:
                for sess in sessions:
                    s_label = sess.get("label", "Session")
                    start_str = sess.get("startTime") or sess.get("start_time", "09:00")
                    end_str = sess.get("endTime") or sess.get("end_time", "12:00")
                    sess_enabled = sess.get("enabled", True)

                    # Parse times
                    sh, sm = map(int, start_str.split(":"))
                    eh, em = map(int, end_str.split(":"))
                    st_time = time(sh, sm)
                    end_time_val = time(eh, em)
                    dur = (eh * 60 + em) - (sh * 60 + sm)

                    # Check per-date special restrictions (Task P5.7)
                    # Produce disabled slot rather than missing so UI can show it
                    slot_enabled = sess_enabled
                    restriction = restrictions_map.get((d_str, s_label)) or restrictions_map.get(
                        (d_str, None)
                    )
                    if restriction and not restriction.get("enabled", False):
                        slot_enabled = False

                    raw_slots.append(
                        {
                            "date": current_date,
                            "start_time": st_time,
                            "end_time": end_time_val,
                            "duration_minutes": dur,
                            "session_label": s_label,
                            "enabled": slot_enabled,
                            "capacity": config.get("maxExamsPerSession")
                            or config.get("max_exams_per_session"),
                        }
                    )

            current_date += timedelta(days=1)

        # Deterministic slot ordering (Task P5.8): by date ascending, then start_time ascending
        raw_slots.sort(key=lambda s: (s["date"], s["start_time"]))

        # Assign stable slot_index
        for idx, s in enumerate(raw_slots):
            s["slot_index"] = idx

        return raw_slots

    @classmethod
    def save_generated_slots(
        cls,
        db: Session,
        cycle_id: str,
        actor: User,
        force: bool = False,
        request_id: str | None = None,
    ) -> list[TimeSlotResponse]:
        """
        Generate and persist slots into the database (Task P5.9).
        Preserves slot IDs where (date, start_time) are unchanged so existing locks and
        assignments survive harmless config edits.
        """
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND",
                message=f"Scheduling cycle '{cycle_id}' was not found.",
                status_code=404,
            )

        # Check existing assignments
        existing_assignments_count = (
            db.scalar(
                select(func.count(ExamAssignment.id))
                .join(TimeSlot, TimeSlot.id == ExamAssignment.time_slot_id)
                .where(TimeSlot.scheduling_cycle_id == cycle_id)
            )
            or 0
        )
        if existing_assignments_count > 0 and not force:
            raise DomainException(
                code="ASSIGNMENTS_EXIST",
                message=(
                    f"Cannot regenerate slots: cycle has {existing_assignments_count} existing exam assignment(s). "
                    "Provide 'force=true' to confirm overwrite."
                ),
                status_code=409,
            )

        # Generate slots pure
        generated = cls.generate_slots(
            start_date=cycle.start_date,
            end_date=cycle.end_date,
            config=cycle.configuration_json,
        )

        # Reconcile with existing slots to preserve IDs (Task P5.9)
        existing_slots = list(
            db.scalars(select(TimeSlot).where(TimeSlot.scheduling_cycle_id == cycle_id)).all()
        )
        existing_map = {(s.date, s.start_time.strftime("%H:%M")): s for s in existing_slots}

        updated_slots: list[TimeSlot] = []
        seen_keys: set[tuple[date, str]] = set()

        for g in generated:
            key = (g["date"], g["start_time"].strftime("%H:%M"))
            seen_keys.add(key)
            existing = existing_map.get(key)

            if existing:
                # Update existing slot in place
                existing.end_time = g["end_time"]
                existing.duration_minutes = g["duration_minutes"]
                existing.session_label = g["session_label"]
                existing.slot_index = g["slot_index"]
                existing.enabled = g["enabled"]
                existing.capacity = g["capacity"]
                updated_slots.append(existing)
            else:
                # Create new slot
                new_slot = TimeSlot(
                    scheduling_cycle_id=cycle_id,
                    date=g["date"],
                    start_time=g["start_time"],
                    end_time=g["end_time"],
                    duration_minutes=g["duration_minutes"],
                    session_label=g["session_label"],
                    slot_index=g["slot_index"],
                    enabled=g["enabled"],
                    capacity=g["capacity"],
                )
                db.add(new_slot)
                updated_slots.append(new_slot)

        # Delete slots that no longer exist in the new schedule
        for key, s in existing_map.items():
            if key not in seen_keys:
                db.delete(s)

        # Staleness signaling (Task P5.9)
        staleness_service.bump_cycle_data_version(db, cycle_id)

        audit_service.record(
            db=db,
            action=AuditAction.SLOTS_GENERATE,
            entity_type="scheduling_cycle",
            actor_email=actor.email,
            actor_id=actor.id,
            entity_id=cycle_id,
            after={
                "total_slots": len(updated_slots),
                "enabled_slots": len([s for s in updated_slots if s.enabled]),
            },
            request_id=request_id,
        )
        db.commit()

        # Re-fetch sorted by slot_index
        all_slots = list(
            db.scalars(
                select(TimeSlot)
                .where(TimeSlot.scheduling_cycle_id == cycle_id)
                .order_by(TimeSlot.slot_index.asc())
            ).all()
        )

        return [
            TimeSlotResponse(
                id=s.id,
                scheduling_cycle_id=s.scheduling_cycle_id,
                date=s.date,
                start_time=s.start_time.strftime("%H:%M"),
                end_time=s.end_time.strftime("%H:%M"),
                duration_minutes=s.duration_minutes,
                session_label=s.session_label,
                slot_index=s.slot_index,
                enabled=s.enabled,
                capacity=s.capacity,
            )
            for s in all_slots
        ]

    @classmethod
    def get_capacity_summary(cls, db: Session, cycle_id: str) -> CapacitySummaryResponse:
        """
        Slot capacity summary & feasibility pre-check (Task P5.11, PRD §12, §13.4).
        """
        cycle = db.get(SchedulingCycle, cycle_id)
        if not cycle:
            raise DomainException(
                code="CYCLE_NOT_FOUND",
                message=f"Scheduling cycle '{cycle_id}' was not found.",
                status_code=404,
            )

        slots = list(
            db.scalars(
                select(TimeSlot)
                .where(TimeSlot.scheduling_cycle_id == cycle_id)
                .order_by(TimeSlot.slot_index.asc())
            ).all()
        )
        exams = list(
            db.scalars(
                select(Exam).where(
                    Exam.scheduling_cycle_id == cycle_id,
                    Exam.status == EntityStatus.ACTIVE,
                )
            ).all()
        )

        total_slots = len(slots)
        enabled_slots = [s for s in slots if s.enabled]
        enabled_count = len(enabled_slots)
        disabled_count = total_slots - enabled_count

        # Duration buckets
        buckets: dict[int, int] = {}
        for s in enabled_slots:
            buckets[s.duration_minutes] = buckets.get(s.duration_minutes, 0) + 1

        # Slots by day
        days_map: dict[date, dict[str, Any]] = {}
        for s in slots:
            if s.date not in days_map:
                days_map[s.date] = {"date": s.date.isoformat(), "totalSlots": 0, "enabledSlots": 0}
            days_map[s.date]["totalSlots"] += 1
            if s.enabled:
                days_map[s.date]["enabledSlots"] += 1

        slots_by_day = [days_map[d] for d in sorted(days_map.keys())]

        # Duration compatibility check (Task P5.12)
        max_slot_dur = max([s.duration_minutes for s in enabled_slots], default=0)
        incompatible_exams = [e for e in exams if e.duration_minutes > max_slot_dur]
        incompatible_count = len(incompatible_exams)

        # Feasibility Warnings
        warnings: list[str] = []
        if total_slots == 0:
            warnings.append("No time slots have been generated yet for this cycle.")
        elif enabled_count < len(exams):
            warnings.append(
                f"Insufficient slots: Cycle has {enabled_count} enabled slot(s), but requires "
                f"at least {len(exams)} slot(s) for the active exams."
            )

        if incompatible_count > 0:
            warnings.append(
                f"Infeasible: {incompatible_count} exam(s) have duration ({incompatible_exams[0].duration_minutes} min) "
                f"longer than every enabled slot (max available: {max_slot_dur} min)."
            )

        is_feasible = (
            (enabled_count >= len(exams)) and (incompatible_count == 0) and (total_slots > 0)
        )

        return CapacitySummaryResponse(
            cycle_id=cycle_id,
            total_slots=total_slots,
            enabled_slots=enabled_count,
            disabled_slots=disabled_count,
            slots_by_duration_bucket=buckets,
            slots_by_day=slots_by_day,
            exam_count=len(exams),
            duration_incompatible_exams_count=incompatible_count,
            is_feasible_pre_check=is_feasible,
            warnings=warnings,
        )


slot_service = SlotService()
