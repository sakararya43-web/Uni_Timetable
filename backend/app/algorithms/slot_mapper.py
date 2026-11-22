"""Color Class to Calendar Slot Mapping Engine.

PRD §13.3, §13.5, ADR-004, ADR-005, Tasks P8.1, P8.2, P8.3, P8.4, P8.5, P8.6:
Maps abstract color classes from graph coloring to concrete calendar time slots
using two-stage maximum bipartite matching and soft quality placement.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class SlotInfo:
    """Lightweight slot representation for pure mapping algorithms."""

    id: str
    date: date
    start_time: str
    end_time: str
    duration_minutes: int
    session_label: str
    slot_index: int
    is_enabled: bool = True


@dataclass
class ExamInfo:
    """Lightweight exam representation for pure mapping algorithms."""

    id: str
    subject_code: str
    duration_minutes: int
    preferred_dates: list[str]
    restricted_dates: list[str]
    locked_slot_id: str | None = None
    prior_slot_id: str | None = None


@dataclass
class MappingResult:
    """Result of color-to-slot mapping."""

    is_feasible: bool
    color_to_slot: dict[int, str]  # color_id -> slot_id
    slot_to_color: dict[str, int]  # slot_id -> color_id
    unmapped_colors: list[int]
    unmapped_exam_ids: list[str]
    bottlenecks: list[str]
    recommendations: list[str]
    message: str | None = None


def _find_augmenting_path(
    u: int,
    adj_graph: dict[int, list[str]],
    match_r: dict[str, int],
    visited: set[int],
) -> bool:
    """DFS augmenting path search for maximum bipartite matching."""
    for v in adj_graph.get(u, []):
        if v not in match_r:
            match_r[v] = u
            return True
        prev_u = match_r[v]
        if prev_u not in visited:
            visited.add(prev_u)
            if _find_augmenting_path(prev_u, adj_graph, match_r, visited):
                match_r[v] = u
                return True
    return False


def maximum_bipartite_matching(
    left_nodes: list[int],
    adj_graph: dict[int, list[str]],
) -> dict[int, str]:
    """
    Computes maximum bipartite matching between left nodes (color classes)
    and right nodes (slots) using augmenting path search (Task P8.3).
    """
    match_r: dict[str, int] = {}  # right_node -> left_node

    for u in left_nodes:
        visited: set[int] = {u}
        _find_augmenting_path(u, adj_graph, match_r, visited)

    return {u: v for v, u in match_r.items()}


def map_colors_to_slots(
    color_classes: dict[int, list[str]],
    slots: list[SlotInfo],
    exams: dict[str, ExamInfo],
    max_exams_per_session: int | None = None,
    preferred_weights: dict[str, Any] | None = None,
) -> MappingResult:
    """
    Maps color classes to concrete time slots (Tasks P8.1 - P8.6).

    Rules:
    1. A color class maps to exactly one slot (ADR-004).
    2. Locked exams are bound directly to their locked slot first (ADR-005, P8.4).
    3. Eligible slots respect enabled status, restricted dates, and duration fit (P8.2).
    4. Two-stage assignment: maximum bipartite matching ensures feasibility (P8.3).
    5. Infeasibility produces detailed bottleneck diagnostic report (P8.6).
    """
    if not color_classes:
        return MappingResult(
            is_feasible=True,
            color_to_slot={},
            slot_to_color={},
            unmapped_colors=[],
            unmapped_exam_ids=[],
            bottlenecks=[],
            recommendations=[],
        )

    enabled_slots = [s for s in slots if s.is_enabled]
    slot_map = {s.id: s for s in slots}

    # 1. Process locked exams and bind precolored classes (P8.4)
    color_to_slot: dict[int, str] = {}
    used_slot_ids: set[str] = set()
    unlocked_colors: list[int] = []

    for color_id, exam_ids in color_classes.items():
        locked_slots = {
            exams[eid].locked_slot_id
            for eid in exam_ids
            if eid in exams and exams[eid].locked_slot_id
        }

        if len(locked_slots) > 1:
            return MappingResult(
                is_feasible=False,
                color_to_slot={},
                slot_to_color={},
                unmapped_colors=list(color_classes.keys()),
                unmapped_exam_ids=[eid for eids in color_classes.values() for eid in eids],
                bottlenecks=[
                    f"Color class {color_id} contains exams locked to different slots: {locked_slots}."
                ],
                recommendations=[
                    "Unlock one of the conflicting exams or place them in separate cycles."
                ],
                message=f"Contradictory slot locks in color class {color_id}.",
            )

        if len(locked_slots) == 1:
            locked_sid = next(iter(locked_slots))
            if locked_sid not in slot_map or not slot_map[locked_sid].is_enabled:
                return MappingResult(
                    is_feasible=False,
                    color_to_slot={},
                    slot_to_color={},
                    unmapped_colors=[color_id],
                    unmapped_exam_ids=exam_ids,
                    bottlenecks=[f"Locked slot '{locked_sid}' is disabled or does not exist."],
                    recommendations=[
                        "Enable the locked slot or change the exam lock to an active slot."
                    ],
                    message=f"Locked slot '{locked_sid}' is unavailable.",
                )
            color_to_slot[color_id] = locked_sid
            used_slot_ids.add(locked_sid)
        else:
            unlocked_colors.append(color_id)

    # 2. Build eligibility graph for unlocked color classes (P8.2)
    available_slots = [s for s in enabled_slots if s.id not in used_slot_ids]
    eligibility_graph: dict[int, list[str]] = {}

    for c_id in unlocked_colors:
        exam_ids = color_classes[c_id]
        class_exams = [exams[eid] for eid in exam_ids if eid in exams]
        max_duration = max((e.duration_minutes for e in class_exams), default=180)

        # Collect restricted dates
        restricted_dates: set[str] = set()
        for e in class_exams:
            restricted_dates.update(e.restricted_dates)

        # Find eligible slots
        eligible_for_c: list[SlotInfo] = []
        for s in available_slots:
            # Duration check (ADR-004: exam_dur <= slot_dur)
            if s.duration_minutes < max_duration:
                continue
            # Restricted date check
            if str(s.date) in restricted_dates:
                continue
            # Capacity check
            if max_exams_per_session and len(class_exams) > max_exams_per_session:
                continue
            eligible_for_c.append(s)

        # Quality sorting: prefer prior slots (disruption minimization), preferred dates, then optimal spread across date range (P8.3, P9.17)
        preferred_dates: set[str] = set()
        prior_slots: set[str] = set()
        for e in class_exams:
            preferred_dates.update(e.preferred_dates)
            if e.prior_slot_id:
                prior_slots.add(e.prior_slot_id)

        pref_set = set(preferred_dates)
        prior_set = set(prior_slots)

        min_date = min((s.date for s in available_slots), default=date.min)
        max_date = max((s.date for s in available_slots), default=date.max)
        date_span = (max_date - min_date).days

        # Target date ratio for this color class to spread across the cycle from start to end
        color_idx_pos = unlocked_colors.index(c_id) if c_id in unlocked_colors else 0
        target_ratio = (
            color_idx_pos / (len(unlocked_colors) - 1) if len(unlocked_colors) > 1 else 0.0
        )

        def slot_preference_key(
            s: SlotInfo,
            _pref: set[str] = pref_set,
            _priors: set[str] = prior_set,
            _min_date: date = min_date,
            _date_span: int = date_span,
            _target_ratio: float = target_ratio,
        ) -> tuple[int, int, float, int, str]:
            prior_match = 0 if s.id in _priors else 1
            is_pref = 0 if str(s.date) in _pref else 1
            slot_ratio = (s.date - _min_date).days / _date_span if _date_span > 0 else 0.0
            spread_dist = abs(slot_ratio - _target_ratio)
            return (prior_match, is_pref, spread_dist, s.slot_index, s.start_time)

        eligible_for_c.sort(key=slot_preference_key)
        eligibility_graph[c_id] = [s.id for s in eligible_for_c]

    # 3. Execute maximum bipartite matching (P8.3)
    matched = maximum_bipartite_matching(unlocked_colors, eligibility_graph)
    color_to_slot.update(matched)

    # 4. Infeasibility analysis (P8.6)
    unmapped = [c for c in color_classes if c not in color_to_slot]
    if unmapped:
        unmapped_eids = [eid for c in unmapped for eid in color_classes[c]]
        bottlenecks: list[str] = []
        recommendations: list[str] = []

        total_req = len(color_classes)
        total_avail = len(enabled_slots)
        bottlenecks.append(
            f"Insufficient slots: required {total_req} slots, but only {total_avail} enabled slots exist."
        )

        # Analyze why unmapped classes failed
        for c in unmapped:
            exam_ids = color_classes[c]
            max_dur = max(
                (exams[eid].duration_minutes for eid in exam_ids if eid in exams), default=180
            )
            slots_with_dur = [s for s in enabled_slots if s.duration_minutes >= max_dur]
            if len(slots_with_dur) < total_req:
                bottlenecks.append(
                    f"Duration bottleneck: color class {c} has {max_dur}-minute exam; only {len(slots_with_dur)} slots support this duration."
                )
                recommendations.append(
                    "Extend slot durations or configure longer exam sessions in cycle settings."
                )

        if total_req > total_avail:
            recommendations.append(
                "Add more exam dates or add an additional session (e.g. Evening) to the cycle configuration."
            )

        return MappingResult(
            is_feasible=False,
            color_to_slot=color_to_slot,
            slot_to_color={s: c for c, s in color_to_slot.items()},
            unmapped_colors=unmapped,
            unmapped_exam_ids=unmapped_eids,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            message=(
                f"Schedule infeasible: {len(unmapped)} of {len(color_classes)} color classes could not be mapped to slots."
            ),
        )

    slot_to_color = {s: c for c, s in color_to_slot.items()}
    return MappingResult(
        is_feasible=True,
        color_to_slot=color_to_slot,
        slot_to_color=slot_to_color,
        unmapped_colors=[],
        unmapped_exam_ids=[],
        bottlenecks=[],
        recommendations=[],
    )
