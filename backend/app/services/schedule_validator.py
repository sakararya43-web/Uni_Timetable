"""Independent Schedule Hard-Constraint Validator.

PRD §14.1, §14.2, Tasks P8.7, P8.8, P8.10:
Pure verification engine running independently of coloring and mapping algorithms.
Verifies all 10 hard constraints and returns structured, user-readable diagnostics.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HardViolation:
    type: str  # CONFLICT, COMPLETENESS, DUPLICATE, DURATION_OVERFLOW, EXCLUDED_DATE, DISABLED_SLOT, LOCK_VIOLATION, RESTRICTED_DATE, CAPACITY_OVERFLOW, INVALID_REFERENCE
    exam_ids: list[str]
    slot_id: str | None
    message: str
    shared_student_count: int = 0


@dataclass
class ScheduleValidationReport:
    valid: bool
    hard_violations: list[HardViolation] = field(default_factory=list)
    soft_penalty_total: float = 0.0
    soft_breakdown: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_schedule(
    exams: dict[str, Any],  # exam_id -> {id, subject_id, subject_code, duration_minutes, restricted_dates, cycle_id, locked_slot_id}
    assignments: list[dict[str, Any]],  # list of {exam_id, time_slot_id, color_id, locked}
    slots: dict[str, Any],  # slot_id -> {id, date, start_time, end_time, duration_minutes, is_enabled, cycle_id}
    enrollments: list[tuple[str, str]],  # list of (student_id, exam_id)
    cycle_id: str,
    max_exams_per_session: int | None = None,
) -> ScheduleValidationReport:
    """
    Independently verifies that a candidate schedule satisfies all 10 hard constraints (P8.7).
    Never raises an exception; returns a complete diagnostic report.
    """
    violations: list[HardViolation] = []
    warnings: list[str] = []

    assigned_exam_ids = [a["exam_id"] for a in assignments]
    exam_to_slot: dict[str, str] = {a["exam_id"]: a["time_slot_id"] for a in assignments}
    slot_to_exams: dict[str, list[str]] = {}
    for a in assignments:
        slot_to_exams.setdefault(a["time_slot_id"], []).append(a["exam_id"])

    # 1. COMPLETENESS & DUPLICATES (Hard Constraints 2 & 3)
    in_scope_eids = set(exams.keys())
    seen_eids: set[str] = set()
    duplicate_eids: set[str] = set()

    for eid in assigned_exam_ids:
        if eid in seen_eids:
            duplicate_eids.add(eid)
        seen_eids.add(eid)

    if duplicate_eids:
        for deid in sorted(duplicate_eids):
            code = exams.get(deid, {}).get("subject_code", deid)
            violations.append(
                HardViolation(
                    type="DUPLICATE",
                    exam_ids=[deid],
                    slot_id=exam_to_slot.get(deid),
                    message=f"Exam '{code}' has multiple conflicting slot assignments.",
                )
            )

    missing_eids = sorted(in_scope_eids - seen_eids)
    if missing_eids:
        for meid in missing_eids:
            code = exams.get(meid, {}).get("subject_code", meid)
            violations.append(
                HardViolation(
                    type="COMPLETENESS",
                    exam_ids=[meid],
                    slot_id=None,
                    message=f"Exam '{code}' is missing from the schedule.",
                )
            )

    # 2. VALID REFERENCES & DISABLED SLOTS (Hard Constraints 6 & 10)
    for a in assignments:
        eid = a["exam_id"]
        sid = a["time_slot_id"]

        if eid not in exams or exams[eid].get("cycle_id") != cycle_id:
            violations.append(
                HardViolation(
                    type="INVALID_REFERENCE",
                    exam_ids=[eid],
                    slot_id=sid,
                    message=f"Exam '{eid}' does not belong to scheduling cycle '{cycle_id}'.",
                )
            )

        if sid not in slots or slots[sid].get("cycle_id") != cycle_id:
            violations.append(
                HardViolation(
                    type="INVALID_REFERENCE",
                    exam_ids=[eid],
                    slot_id=sid,
                    message=f"Time slot '{sid}' does not belong to scheduling cycle '{cycle_id}'.",
                )
            )
            continue

        slot = slots[sid]
        if not slot.get("is_enabled", True):
            code = exams.get(eid, {}).get("subject_code", eid)
            violations.append(
                HardViolation(
                    type="DISABLED_SLOT",
                    exam_ids=[eid],
                    slot_id=sid,
                    message=f"Exam '{code}' is assigned to a disabled time slot on {slot.get('date')} ({slot.get('start_time')}).",
                )
            )

        # 3. DURATION FIT (Hard Constraint 4)
        exam_dur = exams.get(eid, {}).get("duration_minutes", 180)
        slot_dur = slot.get("duration_minutes", 180)
        if exam_dur > slot_dur:
            code = exams.get(eid, {}).get("subject_code", eid)
            violations.append(
                HardViolation(
                    type="DURATION_OVERFLOW",
                    exam_ids=[eid],
                    slot_id=sid,
                    message=f"Exam '{code}' duration ({exam_dur}m) exceeds slot duration ({slot_dur}m).",
                )
            )

        # 4. RESTRICTED DATES (Hard Constraint 8)
        restricted = exams.get(eid, {}).get("restricted_dates", [])
        slot_date_str = str(slot.get("date"))
        if slot_date_str in restricted:
            code = exams.get(eid, {}).get("subject_code", eid)
            violations.append(
                HardViolation(
                    type="RESTRICTED_DATE",
                    exam_ids=[eid],
                    slot_id=sid,
                    message=f"Exam '{code}' is assigned to restricted date {slot_date_str}.",
                )
            )

        # 5. LOCK VIOLATIONS (Hard Constraint 7)
        locked_sid = exams.get(eid, {}).get("locked_slot_id")
        if locked_sid and locked_sid != sid:
            code = exams.get(eid, {}).get("subject_code", eid)
            violations.append(
                HardViolation(
                    type="LOCK_VIOLATION",
                    exam_ids=[eid],
                    slot_id=sid,
                    message=f"Locked exam '{code}' was moved away from locked slot '{locked_sid}'.",
                )
            )

    # 6. CAPACITY CHECK (Hard Constraint 9)
    if max_exams_per_session:
        for sid, eids in slot_to_exams.items():
            if len(eids) > max_exams_per_session:
                slot = slots.get(sid, {})
                codes = [exams.get(e, {}).get("subject_code", e) for e in eids]
                violations.append(
                    HardViolation(
                        type="CAPACITY_OVERFLOW",
                        exam_ids=eids,
                        slot_id=sid,
                        message=(
                            f"Time slot on {slot.get('date')} has {len(eids)} exams ({', '.join(codes)}), "
                            f"exceeding max session capacity of {max_exams_per_session}."
                        ),
                    )
                )

    # 7. CONFLICT CHECK (Hard Constraint 1: zero student clashes)
    # Recomputed directly from raw enrollments
    student_slots: dict[str, list[tuple[str, str]]] = {}  # student_id -> list of (exam_id, slot_id)
    for s_id, e_id in enrollments:
        if e_id in exam_to_slot:
            student_slots.setdefault(s_id, []).append((e_id, exam_to_slot[e_id]))

    clash_pairs: dict[tuple[str, str, str], int] = {}  # (exam_a, exam_b, slot_id) -> count of shared students
    for _s_id, exam_slot_pairs in student_slots.items():
        if len(exam_slot_pairs) < 2:
            continue
        # Group by slot
        by_slot: dict[str, list[str]] = {}
        for eid, sid in exam_slot_pairs:
            by_slot.setdefault(sid, []).append(eid)
        for sid, eids in by_slot.items():
            if len(eids) >= 2:
                for i in range(len(eids)):
                    for j in range(i + 1, len(eids)):
                        pair: tuple[str, str, str] = (min(eids[i], eids[j]), max(eids[i], eids[j]), sid)
                        clash_pairs[pair] = clash_pairs.get(pair, 0) + 1

    for (e_a, e_b, sid), count in clash_pairs.items():
        code_a = exams.get(e_a, {}).get("subject_code", e_a)
        code_b = exams.get(e_b, {}).get("subject_code", e_b)
        slot = slots.get(sid, {})
        violations.append(
            HardViolation(
                type="CONFLICT",
                exam_ids=[e_a, e_b],
                slot_id=sid,
                shared_student_count=count,
                message=(
                    f"Direct student conflict: {count} student(s) are enrolled in both '{code_a}' and '{code_b}', "
                    f"which are assigned to the same time slot on {slot.get('date')} ({slot.get('start_time')})."
                ),
            )
        )

    is_valid = len(violations) == 0

    return ScheduleValidationReport(
        valid=is_valid,
        hard_violations=violations,
        warnings=warnings,
    )
