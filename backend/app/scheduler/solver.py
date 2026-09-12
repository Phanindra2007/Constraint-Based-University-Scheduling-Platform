from ortools.sat.python import cp_model
from .model import build_model


def solve():
    model, courses, start_time = build_model()

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("Schedule found!\n")
        for course in courses:
            print(f"{course}: " f"slot {solver.Value(start_time[course])}")
    else:
        print("No feasible schedule found.")


if __name__ == "__main__":
    solve()
