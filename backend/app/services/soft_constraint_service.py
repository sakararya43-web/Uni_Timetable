"""Soft Constraint Penalty Scoring Engine.

PRD §14.3, Task P8.9:
Evaluates schedule quality based on configurable penalty weights:
- Multiple exams per student in a day (weight 10)
- Consecutive exam sessions on the same day (weight 5)
- Session load balance deviation (weight 3)
- Missed preferred exam dates (weight 2)
- Unlocked exam moved from baseline (weight 1)
"""

from datetime import date
from typing import Any


def evaluate_soft_constraints(
    assignments: list[dict[str, Any]],  # list of {exam_id, time_slot_id}
    slots: dict[str, Any],  # slot_id -> {id, date, start_time, end_time, slot_index, session_label}
    exams: dict[str, Any],  # exam_id -> {id, subject_code, preferred_dates}
    enrollments: list[tuple[str, str]],  # list of (student_id, exam_id)
    weights: dict[str, Any] | None = None,
    baseline_assignments: dict[str, str] | None = None,  # exam_id -> time_slot_id
) -> tuple[float, list[dict[str, Any]]]:
    """
    Computes total soft penalty score and granular breakdown across all soft rules (P8.9).
    Computed efficiently in O(total enrollments) using per-student slot timelines.
    """
    cfg_weights = weights or {}
    w_multi_day = cfg_weights.get("multipleExamsPerDay", cfg_weights.get("multiple_exams_per_day", 10.0))
    w_consecutive = cfg_weights.get("consecutiveSessions", cfg_weights.get("consecutive_sessions", 5.0))
    w_load_balance = cfg_weights.get("sessionLoadBalance", cfg_weights.get("session_load_balance", 3.0))
    w_pref_date = cfg_weights.get("preferredDateMissed", cfg_weights.get("preferred_date_missed", 2.0))
    w_moved = cfg_weights.get("unlockedExamMoved", cfg_weights.get("unlocked_exam_moved", 1.0))

    exam_to_slot = {a["exam_id"]: a["time_slot_id"] for a in assignments}
    breakdown: list[dict[str, Any]] = []
    total_penalty = 0.0

    # 1. Student-level timeline scans
    student_slots: dict[str, list[dict[str, Any]]] = {}
    for s_id, e_id in enrollments:
        if e_id in exam_to_slot:
            sid = exam_to_slot[e_id]
            slot = slots.get(sid)
            if slot:
                student_slots.setdefault(s_id, []).append({
                    "exam_id": e_id,
                    "slot_id": sid,
                    "date": slot.get("date"),
                    "slot_index": slot.get("slot_index", 0),
                    "start_time": slot.get("start_time"),
                })

    multi_day_count = 0
    consecutive_count = 0

    for _s_id, slot_list in student_slots.items():
        # Group by date
        by_date: dict[date, list[dict[str, Any]]] = {}
        for s in slot_list:
            d = s["date"]
            if d:
                by_date.setdefault(d, []).append(s)

        for _d, day_slots in by_date.items():
            # Rule: Multiple exams on same day
            if len(day_slots) > 1:
                multi_day_count += (len(day_slots) - 1)

            # Rule: Consecutive sessions on same day
            if len(day_slots) >= 2:
                sorted_day = sorted(day_slots, key=lambda x: x.get("start_time", ""))
                for i in range(len(sorted_day) - 1):
                    idx1 = sorted_day[i].get("slot_index", 0)
                    idx2 = sorted_day[i + 1].get("slot_index", 0)
                    if idx2 == idx1 + 1:
                        consecutive_count += 1

    if multi_day_count > 0:
        penalty = round(multi_day_count * w_multi_day, 2)
        total_penalty += penalty
        breakdown.append({
            "rule": "multipleExamsPerDay",
            "weight": w_multi_day,
            "count": multi_day_count,
            "penalty": penalty,
            "message": f"{multi_day_count} instances of students taking multiple exams on the same day.",
        })

    if consecutive_count > 0:
        penalty = round(consecutive_count * w_consecutive, 2)
        total_penalty += penalty
        breakdown.append({
            "rule": "consecutiveSessions",
            "weight": w_consecutive,
            "count": consecutive_count,
            "penalty": penalty,
            "message": f"{consecutive_count} instances of students scheduled for back-to-back consecutive sessions.",
        })

    # 2. Preferred dates missed
    pref_missed_count = 0
    for a in assignments:
        eid = a["exam_id"]
        sid = a["time_slot_id"]
        exam = exams.get(eid, {})
        slot = slots.get(sid, {})
        pref_dates = exam.get("preferred_dates", [])
        if pref_dates:
            slot_date_str = str(slot.get("date"))
            if slot_date_str not in pref_dates:
                pref_missed_count += 1

    if pref_missed_count > 0:
        penalty = round(pref_missed_count * w_pref_date, 2)
        total_penalty += penalty
        breakdown.append({
            "rule": "preferredDateMissed",
            "weight": w_pref_date,
            "count": pref_missed_count,
            "penalty": penalty,
            "message": f"{pref_missed_count} exams scheduled on non-preferred dates.",
        })

    # 3. Session load balance deviation
    session_counts: dict[str, int] = {}
    for a in assignments:
        sid = a["time_slot_id"]
        session_counts[sid] = session_counts.get(sid, 0) + 1

    if session_counts:
        counts = list(session_counts.values())
        mean_c = sum(counts) / len(counts)
        variance = sum((c - mean_c) ** 2 for c in counts) / len(counts)
        penalty = round(variance * w_load_balance, 2)
        total_penalty += penalty
        breakdown.append({
            "rule": "sessionLoadBalance",
            "weight": w_load_balance,
            "count": len(session_counts),
            "penalty": penalty,
            "message": f"Session load balance variance across {len(session_counts)} slots is {variance:.2f}.",
        })

    # 4. Movement from baseline
    if baseline_assignments:
        moved_count = 0
        for a in assignments:
            eid = a["exam_id"]
            if eid in baseline_assignments and baseline_assignments[eid] != a["time_slot_id"]:
                if not a.get("locked", False):
                    moved_count += 1
        if moved_count > 0:
            penalty = round(moved_count * w_moved, 2)
            total_penalty += penalty
            breakdown.append({
                "rule": "unlockedExamMoved",
                "weight": w_moved,
                "count": moved_count,
                "penalty": penalty,
                "message": f"{moved_count} unlocked exams moved from baseline schedule.",
            })

    return round(total_penalty, 2), breakdown
