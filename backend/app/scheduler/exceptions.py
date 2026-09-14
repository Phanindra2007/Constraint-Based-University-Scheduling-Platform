class SchedulingError(Exception):
    """Base exception for scheduler errors."""


class InfeasibleScheduleError(SchedulingError):
    """Raised when no timetable satisfies all hard constraints."""
