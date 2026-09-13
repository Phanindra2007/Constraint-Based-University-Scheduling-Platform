from dataclasses import dataclass


@dataclass
class SchedulingSession:
    """
    Represents one actual class session that needs to be scheduled.

    A course offering can require multiple sessions per week.
    Each of those sessions is represented by one SchedulingSession.
    """

    offering_id: int
    session_number: int
    course_id: int
    faculty_id: int
    batch_id: int
    duration_periods: int
    # Number of students in the batch attending this session.
    student_count: int
    # Room type required by the course/session, such as CLASSROOM or LAB.
    required_room_type: str


@dataclass
class SchedulingRoom:
    """Room information needed when creating scheduler placement variables."""

    id: int
    capacity: int
    room_type: str


@dataclass
class SchedulingFacultyAvailability:
    """Teaching periods when a faculty member is available on a day."""

    faculty_id: int
    day: int
    available_periods: set[int]


@dataclass
class SchedulingRoomAvailability:
    """Teaching periods when a room is available on a day."""

    room_id: int
    day: int
    available_periods: set[int]
