from ortools.sat.python import cp_model

from .variables import create_variables
from .constraints import add_constraints
from .objectives import add_objective


def build_model():

    model = cp_model.CpModel()

    courses, start_time = create_variables(model)

    add_constraints(model, courses, start_time)

    add_objective(model, courses, start_time)

    return model, courses, start_time
