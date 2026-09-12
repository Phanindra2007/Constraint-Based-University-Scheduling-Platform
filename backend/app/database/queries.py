from .connection import pool


def _fetch_all_as_dicts(conn, query):
    result = conn.execute(query)
    columns = [column[0] for column in result.description] if result.description else []
    return [dict(zip(columns, row)) for row in result.fetchall()]


def get_course_sections():
    with pool.connection() as conn:
        query = """
            SELECT
                id,
                course_id,
                semester_id,
                professor_id,
                section_name,
                duration_minutes
            FROM course_sections
            ORDER BY id;
        """
        return _fetch_all_as_dicts(conn, query)


def get_professors():
    with pool.connection() as conn:
        query = """
            SELECT
                id,
                name,
                email
            FROM professors
            ORDER BY id;
        """
        return _fetch_all_as_dicts(conn, query)


def get_rooms():
    with pool.connection() as conn:
        query = """
            SELECT
                id,
                name,
                capacity,
                room_type
            FROM rooms
            ORDER BY id;
        """
        return _fetch_all_as_dicts(conn, query)


def get_student_groups():
    with pool.connection() as conn:
        query = """
            SELECT
                id,
                name,
                size
            FROM student_groups
            ORDER BY id;
        """
        return _fetch_all_as_dicts(conn, query)


def get_section_student_groups():
    with pool.connection() as conn:
        query = """
            SELECT
                section_id,
                student_group_id
            FROM section_student_groups
            ORDER BY section_id, student_group_id;
        """
        return _fetch_all_as_dicts(conn, query)


def get_professor_availability():
    with pool.connection() as conn:
        query = """
            SELECT
                id,
                professor_id,
                day_of_week,
                start_time,
                end_time
            FROM professor_availability
            ORDER BY professor_id, day_of_week, start_time;
        """

        return _fetch_all_as_dicts(conn, query)


def get_room_availability():
    with pool.connection() as conn:
        query = """
            SELECT
                id,
                room_id,
                day_of_week,
                start_time,
                end_time
            FROM room_availability
            ORDER BY room_id, day_of_week, start_time;
        """

        return _fetch_all_as_dicts(conn, query)


def get_course_requirements():
    with pool.connection() as conn:
        query = """
            SELECT
                id,
                course_id,
                room_type,
                min_capacity
            FROM course_requirements
            ORDER BY course_id, id;
        """

        return _fetch_all_as_dicts(conn, query)


def get_equipment():
    with pool.connection() as conn:
        query = """
            SELECT
                id,
                name
            FROM equipment
            ORDER BY id;
        """

        return _fetch_all_as_dicts(conn, query)


def get_room_equipment():
    with pool.connection() as conn:
        query = """
            SELECT
                room_id,
                equipment_id,
                quantity
            FROM room_equipment
            ORDER BY room_id, equipment_id;
        """

        return _fetch_all_as_dicts(conn, query)


def get_course_required_equipment():
    with pool.connection() as conn:
        query = """
            SELECT
                course_id,
                equipment_id,
                quantity
            FROM course_required_equipment
            ORDER BY course_id, equipment_id;
        """

        return _fetch_all_as_dicts(conn, query)
