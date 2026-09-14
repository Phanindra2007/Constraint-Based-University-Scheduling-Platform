from dataclasses import dataclass
from collections.abc import Sequence

from app.scheduler.config import MAX_PREFERENCE_SCORE
from app.scheduler.models import SchedulingSession


@dataclass
class SchedulingFacultyPreference:
    """A faculty preference window represented by scheduler period indexes."""

    faculty_id: int
    day: int
    preferred_periods: set[int]
    preference_score: int


@dataclass
class ScheduleScore:
    """Penalty components for a scheduled timetable."""

    batch_gap_penalty: int
    faculty_idle_penalty: int
    faculty_preference_penalty: int
    room_waste_penalty: int
    total_penalty: int


@dataclass
class ScheduleResult:
    """The selected placements and their scoring result."""

    placements: list[dict]
    score: ScheduleScore


def calculate_faculty_preference_penalty(
    sessions: Sequence[SchedulingSession],
    placements: Sequence[dict],
    preferences: Sequence[SchedulingFacultyPreference],
) -> int:
    """Calculate the faculty preference penalty for selected placements."""

    sessions_by_key = {
        (session.offering_id, session.session_number): session for session in sessions
    }
    scores_by_faculty_day_period: dict[tuple[int, int, int], int] = {}
    for preference in preferences:
        for period in preference.preferred_periods:
            key = (preference.faculty_id, preference.day, period)
            existing_score = scores_by_faculty_day_period.get(key)
            scores_by_faculty_day_period[key] = (
                preference.preference_score
                if existing_score is None
                else max(existing_score, preference.preference_score)
            )

    penalty = 0
    for placement in placements:
        session_key = (placement["offering_id"], placement["session_number"])
        try:
            session = sessions_by_key[session_key]
        except KeyError as error:
            raise ValueError(
                "Placement does not match a scheduling session: "
                f"offering_id={session_key[0]}, session_number={session_key[1]}."
            ) from error

        day = placement["day"]
        start_period = placement["start_period"]
        occupied_periods = range(
            start_period,
            start_period + session.duration_periods,
        )
        for period in occupied_periods:
            matched_score = scores_by_faculty_day_period.get(
                (session.faculty_id, day, period)
            )
            if matched_score is not None:
                penalty += MAX_PREFERENCE_SCORE - matched_score

    return penalty
