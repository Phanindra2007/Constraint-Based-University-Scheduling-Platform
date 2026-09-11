BEGIN;

-- ============================================================
-- 1. SEMESTERS
-- ============================================================

INSERT INTO semesters (name, start_date, end_date)
VALUES
    ('2026 Spring', '2026-01-05', '2026-05-15'),
    ('2026 Fall',   '2026-08-03', '2026-12-11');


-- ============================================================
-- 2. PROFESSORS
-- ============================================================

INSERT INTO professors (name, email)
VALUES
    ('Dr. Ravi Kumar',   'ravi.kumar@university.edu'),
    ('Dr. Ananya Rao',   'ananya.rao@university.edu'),
    ('Dr. Suresh Reddy', 'suresh.reddy@university.edu'),
    ('Dr. Priya Sharma', 'priya.sharma@university.edu'),
    ('Dr. Arjun Mehta',  'arjun.mehta@university.edu'),
    ('Dr. Neha Kapoor',  'neha.kapoor@university.edu');


-- ============================================================
-- 3. STUDENT GROUPS
-- ============================================================

INSERT INTO student_groups (name, size)
VALUES
    ('CSE-A-3', 60),
    ('CSE-B-3', 55),
    ('CSE-A-4', 50),
    ('CSE-B-4', 45),
    ('ECE-A-3', 50),
    ('ECE-B-3', 40);


-- ============================================================
-- 4. COURSES
-- ============================================================

INSERT INTO courses
    (code, name, description, duration_minutes)
VALUES
    ('CS301',
     'Database Management Systems',
     'Relational databases, SQL, transactions and database design.',
     60),

    ('CS302',
     'Operating Systems',
     'Processes, threads, memory management and file systems.',
     60),

    ('CS303',
     'Computer Networks',
     'Networking fundamentals, protocols, routing and TCP/IP.',
     60),

    ('CS304',
     'Data Structures',
     'Arrays, linked lists, trees, graphs and hash tables.',
     60),

    ('CS305',
     'Algorithms',
     'Algorithm design, complexity analysis and optimization.',
     90),

    ('CS306',
     'Database Systems Lab',
     'Practical database design and SQL laboratory.',
     120),

    ('CS307',
     'Computer Networks Lab',
     'Practical networking and packet analysis laboratory.',
     120),

    ('CS308',
     'Artificial Intelligence',
     'Search, knowledge representation and machine learning basics.',
     90),

    ('EC301',
     'Digital Electronics',
     'Digital logic, circuits and electronic systems.',
     60),

    ('EC302',
     'Embedded Systems Lab',
     'Microcontrollers and embedded programming laboratory.',
     120);


-- ============================================================
-- 5. COURSE SECTIONS
-- ============================================================

INSERT INTO course_sections
    (course_id, semester_id, professor_id, section_name, duration_minutes)

SELECT
    c.id,
    s.id,
    p.id,
    x.section_name,
    x.duration_minutes
FROM (
    VALUES
        ('CS301', '2026 Fall', 'ravi.kumar@university.edu',   'A', NULL::INTEGER),
        ('CS301', '2026 Fall', 'ananya.rao@university.edu',   'B', NULL::INTEGER),
        ('CS302', '2026 Fall', 'suresh.reddy@university.edu', 'A', NULL::INTEGER),
        ('CS303', '2026 Fall', 'priya.sharma@university.edu', 'A', NULL::INTEGER),
        ('CS304', '2026 Fall', 'arjun.mehta@university.edu',  'A', NULL::INTEGER),
        ('CS305', '2026 Fall', 'arjun.mehta@university.edu',  'A', NULL::INTEGER),
        ('CS306', '2026 Fall', 'ravi.kumar@university.edu',   'A', NULL::INTEGER),
        ('CS307', '2026 Fall', 'priya.sharma@university.edu', 'A', NULL::INTEGER),
        ('CS308', '2026 Fall', 'neha.kapoor@university.edu',  'A', NULL::INTEGER),
        ('EC301', '2026 Fall', 'suresh.reddy@university.edu', 'A', NULL::INTEGER),
        ('EC302', '2026 Fall', 'neha.kapoor@university.edu',  'A', NULL::INTEGER)
) AS x(code, semester_name, professor_email, section_name, duration_minutes)

JOIN courses c
    ON c.code = x.code

JOIN semesters s
    ON s.name = x.semester_name

JOIN professors p
    ON p.email = x.professor_email;


-- ============================================================
-- 6. SECTION ↔ STUDENT GROUPS
-- ============================================================

INSERT INTO section_student_groups
    (section_id, student_group_id)

SELECT
    cs.id,
    sg.id
FROM (
    VALUES
        ('CS301', 'A', 'CSE-A-3'),
        ('CS302', 'A', 'CSE-A-3'),
        ('CS304', 'A', 'CSE-A-3'),
        ('CS306', 'A', 'CSE-A-3'),

        ('CS301', 'B', 'CSE-B-3'),
        ('CS303', 'A', 'CSE-B-3'),

        ('CS305', 'A', 'CSE-A-4'),
        ('CS308', 'A', 'CSE-A-4'),

        ('CS305', 'A', 'CSE-B-4'),

        ('EC301', 'A', 'ECE-A-3'),
        ('EC302', 'A', 'ECE-A-3'),

        ('EC301', 'A', 'ECE-B-3')
) AS x(course_code, section_name, group_name)

JOIN courses c
    ON c.code = x.course_code

JOIN course_sections cs
    ON cs.course_id = c.id
    AND cs.section_name = x.section_name

JOIN semesters s
    ON s.id = cs.semester_id
    AND s.name = '2026 Fall'

JOIN student_groups sg
    ON sg.name = x.group_name;


-- ============================================================
-- 7. ROOMS
-- ============================================================

INSERT INTO rooms
    (name, capacity, room_type)
VALUES
    ('Room 101',      60,  'CLASSROOM'),
    ('Room 102',      40,  'CLASSROOM'),
    ('Room 201',      100, 'CLASSROOM'),
    ('Lab 301',       40,  'LAB'),
    ('Lab 302',       60,  'LAB'),
    ('Auditorium A',  200, 'AUDITORIUM');


-- ============================================================
-- 8. EQUIPMENT
-- ============================================================

INSERT INTO equipment (name)
VALUES
    ('Projector'),
    ('Computers'),
    ('GPU Machines'),
    ('Networking Equipment'),
    ('Microcontroller Kits'),
    ('Oscilloscope');


-- ============================================================
-- 9. ROOM ↔ EQUIPMENT
-- ============================================================

INSERT INTO room_equipment
    (room_id, equipment_id, quantity)

SELECT
    r.id,
    e.id,
    x.quantity
FROM (
    VALUES
        ('Room 101', 'Projector',              1),
        ('Room 102', 'Projector',              1),
        ('Room 201', 'Projector',              1),

        ('Lab 301',  'Computers',             40),
        ('Lab 301',  'Networking Equipment',   1),
        ('Lab 301',  'Projector',              1),

        ('Lab 302',  'Computers',             60),
        ('Lab 302',  'GPU Machines',          20),
        ('Lab 302',  'Projector',              1)
) AS x(room_name, equipment_name, quantity)

JOIN rooms r
    ON r.name = x.room_name

JOIN equipment e
    ON e.name = x.equipment_name;


-- ============================================================
-- 10. PROFESSOR AVAILABILITY
-- ============================================================

INSERT INTO professor_availability
    (professor_id, day_of_week, start_time, end_time)

SELECT
    p.id,
    x.day_of_week,
    x.start_time,
    x.end_time
FROM (
    VALUES
        ('ravi.kumar@university.edu',   1, '09:00'::TIME, '17:00'::TIME),
        ('ravi.kumar@university.edu',   2, '09:00'::TIME, '13:00'::TIME),
        ('ravi.kumar@university.edu',   4, '10:00'::TIME, '17:00'::TIME),

        ('ananya.rao@university.edu',   1, '10:00'::TIME, '17:00'::TIME),
        ('ananya.rao@university.edu',   3, '09:00'::TIME, '16:00'::TIME),
        ('ananya.rao@university.edu',   5, '09:00'::TIME, '15:00'::TIME),

        ('suresh.reddy@university.edu', 1, '09:00'::TIME, '15:00'::TIME),
        ('suresh.reddy@university.edu', 2, '10:00'::TIME, '17:00'::TIME),
        ('suresh.reddy@university.edu', 4, '09:00'::TIME, '16:00'::TIME),

        ('priya.sharma@university.edu', 2, '09:00'::TIME, '17:00'::TIME),
        ('priya.sharma@university.edu', 3, '10:00'::TIME, '17:00'::TIME),
        ('priya.sharma@university.edu', 5, '09:00'::TIME, '17:00'::TIME),

        ('arjun.mehta@university.edu',  1, '09:00'::TIME, '17:00'::TIME),
        ('arjun.mehta@university.edu',  3, '09:00'::TIME, '17:00'::TIME),
        ('arjun.mehta@university.edu',  5, '10:00'::TIME, '17:00'::TIME),

        ('neha.kapoor@university.edu',  2, '09:00'::TIME, '16:00'::TIME),
        ('neha.kapoor@university.edu',  4, '09:00'::TIME, '17:00'::TIME),
        ('neha.kapoor@university.edu',  5, '09:00'::TIME, '13:00'::TIME)
) AS x(email, day_of_week, start_time, end_time)

JOIN professors p
    ON p.email = x.email;


-- ============================================================
-- 11. ROOM AVAILABILITY
-- ============================================================

INSERT INTO room_availability
    (room_id, day_of_week, start_time, end_time)

SELECT
    r.id,
    x.day_of_week,
    x.start_time,
    x.end_time
FROM (
    VALUES

        -- Room 101
        ('Room 101', 1, '09:00'::TIME, '17:00'::TIME),
        ('Room 101', 2, '09:00'::TIME, '17:00'::TIME),
        ('Room 101', 3, '09:00'::TIME, '17:00'::TIME),
        ('Room 101', 4, '09:00'::TIME, '17:00'::TIME),
        ('Room 101', 5, '09:00'::TIME, '17:00'::TIME),

        -- Room 102
        ('Room 102', 1, '09:00'::TIME, '17:00'::TIME),
        ('Room 102', 2, '09:00'::TIME, '17:00'::TIME),
        ('Room 102', 3, '09:00'::TIME, '17:00'::TIME),
        ('Room 102', 4, '09:00'::TIME, '17:00'::TIME),
        ('Room 102', 5, '09:00'::TIME, '17:00'::TIME),

        -- Room 201
        ('Room 201', 1, '09:00'::TIME, '17:00'::TIME),
        ('Room 201', 2, '09:00'::TIME, '17:00'::TIME),
        ('Room 201', 3, '09:00'::TIME, '17:00'::TIME),
        ('Room 201', 4, '09:00'::TIME, '17:00'::TIME),
        ('Room 201', 5, '09:00'::TIME, '17:00'::TIME),

        -- Lab 301
        ('Lab 301', 1, '09:00'::TIME, '17:00'::TIME),
        ('Lab 301', 2, '09:00'::TIME, '17:00'::TIME),
        ('Lab 301', 3, '09:00'::TIME, '17:00'::TIME),
        ('Lab 301', 4, '09:00'::TIME, '17:00'::TIME),
        ('Lab 301', 5, '09:00'::TIME, '17:00'::TIME),

        -- Lab 302
        ('Lab 302', 1, '09:00'::TIME, '17:00'::TIME),
        ('Lab 302', 2, '09:00'::TIME, '17:00'::TIME),
        ('Lab 302', 3, '09:00'::TIME, '17:00'::TIME),
        ('Lab 302', 4, '09:00'::TIME, '17:00'::TIME),
        ('Lab 302', 5, '09:00'::TIME, '17:00'::TIME),

        -- Auditorium
        ('Auditorium A', 1, '09:00'::TIME, '17:00'::TIME),
        ('Auditorium A', 2, '09:00'::TIME, '17:00'::TIME),
        ('Auditorium A', 3, '09:00'::TIME, '17:00'::TIME),
        ('Auditorium A', 4, '09:00'::TIME, '17:00'::TIME),
        ('Auditorium A', 5, '09:00'::TIME, '17:00'::TIME)
) AS x(room_name, day_of_week, start_time, end_time)

JOIN rooms r
    ON r.name = x.room_name;


-- ============================================================
-- 12. PROFESSOR PREFERENCES
-- ============================================================

INSERT INTO professor_preferences
    (professor_id, day_of_week, start_time, end_time, preference_score)

SELECT
    p.id,
    x.day_of_week,
    x.start_time,
    x.end_time,
    x.preference_score
FROM (
    VALUES
        ('ravi.kumar@university.edu',   1, '09:00'::TIME, '12:00'::TIME,  10),
        ('ravi.kumar@university.edu',   2, '12:00'::TIME, '17:00'::TIME, -10),

        ('ananya.rao@university.edu',   3, '09:00'::TIME, '12:00'::TIME,  10),

        ('suresh.reddy@university.edu', 2, '10:00'::TIME, '14:00'::TIME,   8),

        ('priya.sharma@university.edu', 5, '09:00'::TIME, '12:00'::TIME,  10),

        ('arjun.mehta@university.edu',  1, '09:00'::TIME, '12:00'::TIME,   7),

        ('neha.kapoor@university.edu',  4, '13:00'::TIME, '17:00'::TIME,  10)
) AS x(email, day_of_week, start_time, end_time, preference_score)

JOIN professors p
    ON p.email = x.email;


-- ============================================================
-- 13. COURSE PREREQUISITES
-- ============================================================

INSERT INTO course_prerequisites
    (course_id, prerequisite_course_id)

SELECT
    c.id,
    p.id
FROM (
    VALUES
        ('CS305', 'CS304'),
        ('CS308', 'CS305')
) AS x(course_code, prerequisite_code)

JOIN courses c
    ON c.code = x.course_code

JOIN courses p
    ON p.code = x.prerequisite_code;


-- ============================================================
-- 14. COURSE REQUIREMENTS
-- ============================================================

INSERT INTO course_requirements
    (course_id, room_type, min_capacity)

SELECT
    c.id,
    x.room_type,
    x.min_capacity
FROM (
    VALUES
        ('CS301', 'CLASSROOM', 55),
        ('CS302', 'CLASSROOM', 55),
        ('CS303', 'CLASSROOM', 40),
        ('CS304', 'CLASSROOM', 45),
        ('CS305', 'CLASSROOM', 45),
        ('CS306', 'LAB',       30),
        ('CS307', 'LAB',       30),
        ('CS308', 'CLASSROOM', 45),
        ('EC301', 'CLASSROOM', 40),
        ('EC302', 'LAB',       30)
) AS x(course_code, room_type, min_capacity)

JOIN courses c
    ON c.code = x.course_code;


-- ============================================================
-- 15. COURSE REQUIRED EQUIPMENT
-- ============================================================

INSERT INTO course_required_equipment
    (course_id, equipment_id, quantity)

SELECT
    c.id,
    e.id,
    x.quantity
FROM (
    VALUES
        ('CS306', 'Computers',             30),
        ('CS307', 'Computers',             30),
        ('CS307', 'Networking Equipment',   1),
        ('CS308', 'GPU Machines',          10),
        ('EC302', 'Microcontroller Kits',  30),
        ('EC302', 'Oscilloscope',           5)
) AS x(course_code, equipment_name, quantity)

JOIN courses c
    ON c.code = x.course_code

JOIN equipment e
    ON e.name = x.equipment_name;


-- ============================================================
-- 16. SCHEDULE VERSION
-- ============================================================

INSERT INTO schedule_versions
    (semester_id, version_number, objective_score, status)

SELECT
    id,
    1,
    125.5000,
    'ACTIVE'
FROM semesters
WHERE name = '2026 Fall';


-- ============================================================
-- 17. SAMPLE SCHEDULE ENTRIES
-- ============================================================

INSERT INTO schedule_entries
    (
        schedule_version_id,
        section_id,
        room_id,
        day_of_week,
        start_time,
        end_time
    )

SELECT
    sv.id,
    cs.id,
    r.id,
    x.day_of_week,
    x.start_time,
    x.end_time

FROM (
    VALUES
        ('CS301', 'A', 'Room 101', 1, '09:00'::TIME, '10:00'::TIME),
        ('CS302', 'A', 'Room 201', 1, '10:00'::TIME, '11:00'::TIME),
        ('CS304', 'A', 'Room 101', 1, '11:00'::TIME, '12:00'::TIME),
        ('CS306', 'A', 'Lab 301', 2, '10:00'::TIME, '12:00'::TIME),
        ('CS305', 'A', 'Room 201', 3, '09:00'::TIME, '10:30'::TIME)
) AS x(
    course_code,
    section_name,
    room_name,
    day_of_week,
    start_time,
    end_time
)

JOIN courses c
    ON c.code = x.course_code

JOIN course_sections cs
    ON cs.course_id = c.id
    AND cs.section_name = x.section_name

JOIN semesters s
    ON s.id = cs.semester_id
    AND s.name = '2026 Fall'

JOIN schedule_versions sv
    ON sv.semester_id = s.id
    AND sv.version_number = 1

JOIN rooms r
    ON r.name = x.room_name;


-- ============================================================
-- FINISH TRANSACTION
-- ============================================================

COMMIT;