from ortools.sat.python import cp_model


def create_variables(model: cp_model.CpModel):
    courses = ["Math", "Physics", "Progamming"]
    time_slots = range(4)
    start_time = {}

    for course in courses:
        start_time[course] = model.new_int_var(
            0, 3, f"{course}_start"
        )  # Start time for each course

    return courses, start_time
