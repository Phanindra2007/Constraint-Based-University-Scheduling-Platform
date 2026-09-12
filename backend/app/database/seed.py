from app.database.connection import pool


def _insert_rows(conn, query, rows):
    conn.executemany(query, rows)


def seed_database():
    """Insert the sample scheduling data in one transaction."""
    with pool.connection() as conn:
        with conn.transaction():
            _insert_rows(
                conn,
                "INSERT INTO departments (code, name) VALUES (%s, %s)",
                [
                    ("CSE", "Computer Science and Engineering"),
                    ("ECE", "Electronics and Communication Engineering"),
                ],
            )
            _insert_rows(
                conn,
                "INSERT INTO semesters (name, start_date, end_date) VALUES (%s, %s, %s)",
                [("Odd Semester 2026", "2026-07-01", "2026-11-30")],
            )
            _insert_rows(
                conn,
                "INSERT INTO faculty (department_id, name, email) VALUES (%s, %s, %s)",
                [
                    (1, "Dr. Ravi Kumar", "ravi.kumar@university.edu"),
                    (1, "Dr. Ananya Rao", "ananya.rao@university.edu"),
                    (1, "Dr. Kiran Sharma", "kiran.sharma@university.edu"),
                    (2, "Dr. Meera Nair", "meera.nair@university.edu"),
                    (2, "Dr. Arjun Menon", "arjun.menon@university.edu"),
                    (2, "Dr. Priya Das", "priya.das@university.edu"),
                ],
            )
            _insert_rows(
                conn,
                "INSERT INTO batches (department_id, name, student_count) VALUES (%s, %s, %s)",
                [
                    (1, "CSE-A", 60),
                    (1, "CSE-B", 55),
                    (2, "ECE-A", 58),
                    (2, "ECE-B", 52),
                ],
            )
            _insert_rows(
                conn,
                """INSERT INTO courses
					(department_id, code, name, duration_minutes, sessions_per_week,
					 required_room_type, min_capacity)
					VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                [
                    (1, "CS301", "Database Systems", 60, 3, "CLASSROOM", 50),
                    (1, "CS302", "Operating Systems", 60, 3, "CLASSROOM", 50),
                    (1, "CS303", "Computer Networks", 60, 3, "CLASSROOM", 50),
                    (1, "CS304", "Database Systems Lab", 120, 1, "LAB", 30),
                    (2, "EC301", "Digital Signal Processing", 60, 3, "CLASSROOM", 50),
                    (2, "EC302", "Digital Electronics", 60, 3, "CLASSROOM", 50),
                    (2, "EC303", "Embedded Systems", 60, 2, "CLASSROOM", 40),
                    (2, "EC304", "Embedded Systems Lab", 120, 1, "LAB", 25),
                ],
            )
            _insert_rows(
                conn,
                "INSERT INTO rooms (name, capacity, room_type) VALUES (%s, %s, %s)",
                [
                    ("LH-101", 80, "CLASSROOM"),
                    ("LH-102", 70, "CLASSROOM"),
                    ("LH-201", 60, "CLASSROOM"),
                    ("LH-202", 50, "CLASSROOM"),
                    ("CS-LAB-1", 40, "LAB"),
                    ("ECE-LAB-1", 35, "LAB"),
                ],
            )
            _insert_rows(
                conn,
                """INSERT INTO course_offerings
					(course_id, faculty_id, batch_id, semester_id)
					VALUES (%s, %s, %s, %s)""",
                [
                    (1, 1, 1, 1),
                    (2, 2, 1, 1),
                    (3, 3, 1, 1),
                    (4, 1, 1, 1),
                    (1, 1, 2, 1),
                    (2, 2, 2, 1),
                    (3, 3, 2, 1),
                    (5, 4, 3, 1),
                    (6, 5, 3, 1),
                    (7, 6, 3, 1),
                    (8, 6, 3, 1),
                ],
            )

            faculty_availability = []
            faculty_hours = {
                1: [
                    (1, "09:00", "13:00"),
                    (2, "09:00", "13:00"),
                    (3, "10:00", "14:00"),
                    (4, "09:00", "13:00"),
                    (5, "09:00", "12:00"),
                ],
                2: [
                    (1, "10:00", "14:00"),
                    (2, "09:00", "13:00"),
                    (3, "09:00", "13:00"),
                    (4, "10:00", "14:00"),
                    (5, "09:00", "13:00"),
                ],
                3: [
                    (1, "09:00", "13:00"),
                    (2, "10:00", "14:00"),
                    (3, "09:00", "13:00"),
                    (4, "09:00", "13:00"),
                    (5, "10:00", "14:00"),
                ],
                4: [
                    (1, "09:00", "13:00"),
                    (2, "09:00", "13:00"),
                    (3, "10:00", "14:00"),
                    (4, "09:00", "13:00"),
                    (5, "09:00", "13:00"),
                ],
                5: [
                    (1, "10:00", "14:00"),
                    (2, "09:00", "13:00"),
                    (3, "09:00", "13:00"),
                    (4, "10:00", "14:00"),
                    (5, "09:00", "13:00"),
                ],
                6: [
                    (1, "09:00", "13:00"),
                    (2, "10:00", "14:00"),
                    (3, "09:00", "13:00"),
                    (4, "09:00", "13:00"),
                    (5, "10:00", "14:00"),
                ],
            }
            for faculty_id, availability in faculty_hours.items():
                faculty_availability.extend(
                    (faculty_id, 1, day, start, end) for day, start, end in availability
                )
            _insert_rows(
                conn,
                """INSERT INTO faculty_availability
					(faculty_id, semester_id, day_of_week, start_time, end_time)
					VALUES (%s, %s, %s, %s, %s)""",
                faculty_availability,
            )

            room_availability = [
                (room_id, 1, day, "09:00", "17:00")
                for room_id in range(1, 7)
                for day in range(1, 6)
            ]
            _insert_rows(
                conn,
                """INSERT INTO room_availability
					(room_id, semester_id, day_of_week, start_time, end_time)
					VALUES (%s, %s, %s, %s, %s)""",
                room_availability,
            )

            _insert_rows(
                conn,
                """INSERT INTO faculty_preferences
					(faculty_id, semester_id, day_of_week, start_time, end_time, preference_score)
					VALUES (%s, %s, %s, %s, %s, %s)""",
                [
                    (1, 1, 1, "09:00", "10:00", 10),
                    (1, 1, 2, "09:00", "10:00", 10),
                    (1, 1, 3, "10:00", "11:00", 8),
                    (2, 1, 1, "10:00", "11:00", 8),
                    (2, 1, 3, "09:00", "10:00", 10),
                    (2, 1, 5, "09:00", "10:00", 9),
                    (3, 1, 2, "10:00", "11:00", 9),
                    (3, 1, 4, "09:00", "10:00", 10),
                    (4, 1, 1, "09:00", "10:00", 10),
                    (4, 1, 3, "10:00", "11:00", 8),
                    (5, 1, 2, "09:00", "10:00", 10),
                    (5, 1, 4, "10:00", "11:00", 9),
                    (6, 1, 1, "09:00", "10:00", 8),
                    (6, 1, 3, "09:00", "10:00", 10),
                ],
            )
            _insert_rows(
                conn,
                "INSERT INTO timetables (semester_id, version_number, score, status) VALUES (%s, %s, %s, %s)",
                [(1, 1, 82.5000, "ARCHIVED"), (1, 2, 91.7500, "ACTIVE")],
            )
            _insert_rows(
                conn,
                """INSERT INTO timetable_slots
					(timetable_id, course_offering_id, room_id, day_of_week, start_time, end_time)
					VALUES (%s, %s, %s, %s, %s, %s)""",
                [
                    (2, 1, 1, 1, "09:00", "10:00"),
                    (2, 1, 1, 3, "10:00", "11:00"),
                    (2, 1, 1, 5, "09:00", "10:00"),
                    (2, 2, 2, 1, "10:00", "11:00"),
                    (2, 2, 2, 3, "09:00", "10:00"),
                    (2, 2, 2, 5, "10:00", "11:00"),
                    (2, 3, 3, 2, "10:00", "11:00"),
                    (2, 3, 3, 4, "09:00", "10:00"),
                    (2, 3, 3, 5, "11:00", "12:00"),
                    (2, 4, 5, 4, "11:00", "13:00"),
                    (2, 5, 1, 1, "11:00", "12:00"),
                    (2, 5, 1, 3, "11:00", "12:00"),
                    (2, 5, 1, 5, "11:00", "12:00"),
                    (2, 6, 2, 1, "12:00", "13:00"),
                    (2, 6, 2, 3, "12:00", "13:00"),
                    (2, 6, 2, 5, "12:00", "13:00"),
                    (2, 7, 3, 2, "11:00", "12:00"),
                    (2, 7, 3, 4, "10:00", "11:00"),
                    (2, 7, 3, 5, "12:00", "13:00"),
                    (2, 8, 1, 1, "09:00", "10:00"),
                    (2, 8, 1, 3, "10:00", "11:00"),
                    (2, 8, 1, 5, "09:00", "10:00"),
                    (2, 9, 2, 1, "10:00", "11:00"),
                    (2, 9, 2, 3, "09:00", "10:00"),
                    (2, 9, 2, 5, "10:00", "11:00"),
                    (2, 10, 3, 2, "10:00", "11:00"),
                    (2, 10, 3, 4, "10:00", "11:00"),
                    (2, 11, 6, 4, "13:00", "15:00"),
                ],
            )


if __name__ == "__main__":
    seed_database()
