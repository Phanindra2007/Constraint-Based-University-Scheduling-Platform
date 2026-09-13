from typing import Sequence

from ortools.sat.python import cp_model

from app.scheduler.constraints import add_hard_constraints
from app.scheduler.models import (
    SchedulingFacultyAvailability,
    SchedulingRoom,
    SchedulingRoomAvailability,
    SchedulingSession,
)
from app.scheduler.variables import SessionVariables, create_session_variables


def build_scheduling_model(
    sessions: Sequence[SchedulingSession],
    num_days: int,
    num_periods: int,
    rooms: list[SchedulingRoom],
    faculty_availability: list[SchedulingFacultyAvailability],
    room_availability: list[SchedulingRoomAvailability],
) -> tuple[cp_model.CpModel, list[SessionVariables]]:
    """Assemble a CP-SAT model from sessions, rooms, variables, and hard constraints."""

    model = cp_model.CpModel()
    session_variables = [
        create_session_variables(
            model,
            session,
            num_days,
            num_periods,
            rooms,
            faculty_availability,
            room_availability,
        )
        for session in sessions
    ]

    add_hard_constraints(model, sessions, session_variables)

    return model, session_variables
