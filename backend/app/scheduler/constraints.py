def add_constraints(model, courses, start_time):
    for i in range(len(courses)):
        for j in range(i + 1, len(courses)):
            model.Add(start_time[courses[i]] != start_time[courses[j]])
