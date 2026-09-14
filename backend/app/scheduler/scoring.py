from dataclasses import dataclass


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
