-- ============================================================
-- CONSTRAINT-BASED UNIVERSITY TIMETABLE SCHEDULER
-- PostgreSQL Schema — simplified, resume-ready version
-- ============================================================
--
-- DESIGN GOAL
-- This is intentionally smaller than a full production system.
-- It keeps just enough tables to explain, in one sentence each,
-- what problem the scheduler is solving — good for a resume /
-- interview walkthrough, not a real ERP.
--
-- WHY NAMES WERE CHANGED FROM AN EARLIER DRAFT
--   * "professors"       -> "faculty"            (standard university term)
--   * "student_groups"   -> "batches"             (standard university term,
--                                                   e.g. "CSE-A" is a batch)
--   * "course_sections"  -> "course_offerings"    (a course_section told you
--                                                   nothing on its own; a
--                                                   course_offering clearly
--                                                   means "this course, taught
--                                                   by this faculty, to this
--                                                   batch, in this semester")
--   * "schedule_versions"-> "timetables"          (a timetable is what an
--                                                   admin/student actually
--                                                   thinks in terms of)
--   * "schedule_entries" -> "timetable_slots"     (one row = one slot inside
--                                                   a timetable)
--
-- WHAT WAS REMOVED ON PURPOSE (to stay simple)
--   * equipment / room_equipment / course_required_equipment
--         -> collapsed into two plain columns on "courses":
--            required_room_type, min_capacity. A separate
--            equipment catalog is real-world detail that isn't
--            needed to demonstrate the scheduling algorithm.
--   * course_prerequisites
--         -> this is a curriculum/degree-planning concern, not
--            a timetabling concern, so it doesn't belong in a
--            scheduler's core schema.
--   * course_offerings <-> batches junction table
--         -> simplified to one batch per offering (batch_id is
--            a normal column on course_offerings). Real
--            universities occasionally combine two batches into
--            one lecture, but modeling that many-to-many
--            relationship adds a join everywhere for a case that
--            is the exception, not the rule.
--
-- NAMING RULES (kept uniform everywhere)
--   * Table names: plural, snake_case              -> faculty, batches
--   * Primary key: always "id"
--   * Foreign key: always "<singular_referenced_table>_id"
--   * Constraints: pk_ / fk_ / uq_ / ck_ + <table>_<meaning>
-- ============================================================


-- ============================================================
-- 1. DEPARTMENTS
--    Every faculty member, batch and course belongs to one
--    department — this is how real universities (incl. NITK)
--    organize everything, so it's kept even though the
--    scheduler doesn't strictly require it.
-- ============================================================

CREATE TABLE departments (
    id    BIGSERIAL PRIMARY KEY,
    code  VARCHAR(20) NOT NULL,
    name  VARCHAR(150) NOT NULL,

    CONSTRAINT uq_departments_code
        UNIQUE (code)
);


-- ============================================================
-- 2. SEMESTERS
--    e.g. "Odd Semester 2026", with its date range.
-- ============================================================

CREATE TABLE semesters (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,

    CONSTRAINT uq_semesters_name
        UNIQUE (name),

    CONSTRAINT ck_semesters_valid_dates
        CHECK (start_date < end_date)
);


-- ============================================================
-- 3. FACULTY
--    The people who teach courses.
-- ============================================================

CREATE TABLE faculty (
    id             BIGSERIAL PRIMARY KEY,
    department_id  BIGINT NOT NULL,
    name           VARCHAR(100) NOT NULL,
    email          VARCHAR(255),

    CONSTRAINT fk_faculty_department
        FOREIGN KEY (department_id)
        REFERENCES departments (id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_faculty_email
        UNIQUE (email)
);


-- ============================================================
-- 4. BATCHES
--    A group of students who share the same timetable
--    (e.g. "CSE-A", "ECE-B"). Called "student_groups" or
--    "sections" elsewhere — "batch" is the plain, standard
--    university word for this.
-- ============================================================

CREATE TABLE batches (
    id             BIGSERIAL PRIMARY KEY,
    department_id  BIGINT NOT NULL,
    name           VARCHAR(100) NOT NULL,
    student_count  INTEGER NOT NULL,

    CONSTRAINT fk_batches_department
        FOREIGN KEY (department_id)
        REFERENCES departments (id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_batches_name
        UNIQUE (name),

    CONSTRAINT ck_batches_positive_student_count
        CHECK (student_count > 0)
);


-- ============================================================
-- 5. COURSES
--    A subject that can be taught (e.g. "Database Systems").
--    Room requirements live directly on the course as two
--    plain, optional columns instead of a separate table.
-- ============================================================

CREATE TABLE courses (
    id                   BIGSERIAL PRIMARY KEY,
    department_id        BIGINT NOT NULL,
    code                 VARCHAR(30) NOT NULL,
    name                 VARCHAR(150) NOT NULL,
    duration_minutes     INTEGER NOT NULL,
    sessions_per_week    INTEGER NOT NULL,
    required_room_type   VARCHAR(50),
    min_capacity         INTEGER,

    CONSTRAINT fk_courses_department
        FOREIGN KEY (department_id)
        REFERENCES departments (id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_courses_code
        UNIQUE (code),

    CONSTRAINT ck_courses_positive_duration
        CHECK (duration_minutes > 0),

    CONSTRAINT ck_courses_positive_sessions_per_week
        CHECK (sessions_per_week > 0),

    CONSTRAINT ck_courses_valid_required_room_type
        CHECK (required_room_type IS NULL OR required_room_type IN ('CLASSROOM', 'LAB', 'AUDITORIUM')),

    CONSTRAINT ck_courses_positive_min_capacity
        CHECK (min_capacity IS NULL OR min_capacity > 0)
);


-- ============================================================
-- 6. ROOMS
--    Physical spaces classes can be held in.
-- ============================================================

CREATE TABLE rooms (
    id         BIGSERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    capacity   INTEGER NOT NULL,
    room_type  VARCHAR(50) NOT NULL,

    CONSTRAINT uq_rooms_name
        UNIQUE (name),

    CONSTRAINT ck_rooms_positive_capacity
        CHECK (capacity > 0),

    CONSTRAINT ck_rooms_valid_room_type
        CHECK (room_type IN ('CLASSROOM', 'LAB', 'AUDITORIUM'))
);


-- ============================================================
-- 7. COURSE OFFERINGS
--    THE table that used to be the confusing "course_sections".
--    One row = "this course is taught by this faculty member,
--    to this batch, in this semester." Nothing else needs to
--    be inferred from the name.
-- ============================================================

CREATE TABLE course_offerings (
    id            BIGSERIAL PRIMARY KEY,
    course_id     BIGINT NOT NULL,
    faculty_id    BIGINT NOT NULL,
    batch_id      BIGINT NOT NULL,
    semester_id   BIGINT NOT NULL,

    CONSTRAINT fk_course_offerings_course
        FOREIGN KEY (course_id)
        REFERENCES courses (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_course_offerings_faculty
        FOREIGN KEY (faculty_id)
        REFERENCES faculty (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_course_offerings_batch
        FOREIGN KEY (batch_id)
        REFERENCES batches (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_course_offerings_semester
        FOREIGN KEY (semester_id)
        REFERENCES semesters (id)
        ON DELETE RESTRICT,

    -- the same course can't be offered twice to the same batch
    -- in the same semester
    CONSTRAINT uq_course_offerings_course_batch_semester
        UNIQUE (course_id, batch_id, semester_id)
);


-- ============================================================
-- 8. FACULTY AVAILABILITY
--    Weekly windows in which a faculty member CAN be scheduled,
--    for a given semester.
-- ============================================================

CREATE TABLE faculty_availability (
    id           BIGSERIAL PRIMARY KEY,
    faculty_id   BIGINT NOT NULL,
    semester_id  BIGINT NOT NULL,
    day_of_week  SMALLINT NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,

    CONSTRAINT fk_faculty_availability_faculty
        FOREIGN KEY (faculty_id)
        REFERENCES faculty (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_faculty_availability_semester
        FOREIGN KEY (semester_id)
        REFERENCES semesters (id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_faculty_availability_valid_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT ck_faculty_availability_valid_time_range
        CHECK (start_time < end_time)
);


-- ============================================================
-- 9. ROOM AVAILABILITY
--    Weekly windows in which a room CAN be used, for a given
--    semester (e.g. blocked for maintenance otherwise).
-- ============================================================

CREATE TABLE room_availability (
    id           BIGSERIAL PRIMARY KEY,
    room_id      BIGINT NOT NULL,
    semester_id  BIGINT NOT NULL,
    day_of_week  SMALLINT NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,

    CONSTRAINT fk_room_availability_room
        FOREIGN KEY (room_id)
        REFERENCES rooms (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_room_availability_semester
        FOREIGN KEY (semester_id)
        REFERENCES semesters (id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_room_availability_valid_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT ck_room_availability_valid_time_range
        CHECK (start_time < end_time)
);


-- ============================================================
-- 10. FACULTY PREFERENCES
--     Soft-constraint input: how much a faculty member likes
--     teaching in a given weekly window. The solver tries to
--     respect these but is allowed to violate them if needed.
-- ============================================================

CREATE TABLE faculty_preferences (
    id                BIGSERIAL PRIMARY KEY,
    faculty_id        BIGINT NOT NULL,
    semester_id       BIGINT NOT NULL,
    day_of_week       SMALLINT NOT NULL,
    start_time        TIME NOT NULL,
    end_time          TIME NOT NULL,
    preference_score  INTEGER NOT NULL,

    CONSTRAINT fk_faculty_preferences_faculty
        FOREIGN KEY (faculty_id)
        REFERENCES faculty (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_faculty_preferences_semester
        FOREIGN KEY (semester_id)
        REFERENCES semesters (id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_faculty_preferences_valid_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT ck_faculty_preferences_valid_time_range
        CHECK (start_time < end_time)
);


-- ============================================================
-- 11. TIMETABLES
--     One attempt/run of the solver for a semester. Keeping
--     multiple timetables per semester (versioned) is what
--     makes "incremental rescheduling" possible: you can
--     compare version 2 against version 1 to show exactly
--     what changed.
-- ============================================================

CREATE TABLE timetables (
    id               BIGSERIAL PRIMARY KEY,
    semester_id      BIGINT NOT NULL,
    version_number   INTEGER NOT NULL,
    score            NUMERIC(12, 4),
    status           VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    generated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_timetables_semester
        FOREIGN KEY (semester_id)
        REFERENCES semesters (id)
        ON DELETE CASCADE,

    CONSTRAINT ck_timetables_positive_version_number
        CHECK (version_number > 0),

    CONSTRAINT ck_timetables_valid_status
        CHECK (status IN ('DRAFT', 'GENERATING', 'ACTIVE', 'ARCHIVED', 'FAILED')),

    CONSTRAINT uq_timetables_semester_version
        UNIQUE (semester_id, version_number)
);


-- ============================================================
-- 12. TIMETABLE GENERATION JOBS
--     Persistent state for asynchronous timetable-generation requests.
-- ============================================================

CREATE TABLE timetable_generation_jobs (
    id             BIGSERIAL,
    semester_id    BIGINT NOT NULL,
    status         VARCHAR(20) NOT NULL,
    timetable_id   BIGINT,
    error_message  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at   TIMESTAMPTZ,

    CONSTRAINT pk_timetable_generation_jobs
        PRIMARY KEY (id),

    CONSTRAINT fk_timetable_generation_jobs_semester
        FOREIGN KEY (semester_id)
        REFERENCES semesters (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_timetable_generation_jobs_timetable
        FOREIGN KEY (timetable_id)
        REFERENCES timetables (id)
        ON DELETE SET NULL,

    CONSTRAINT ck_timetable_generation_jobs_valid_status
        CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED'))
);

CREATE UNIQUE INDEX uq_timetable_generation_jobs_active_semester
    ON timetable_generation_jobs (semester_id)
    WHERE status IN ('PENDING', 'RUNNING');


-- ============================================================
-- 13. TIMETABLE SLOTS
--     One row = one course_offering placed into one room, at
--     one day/time, inside one timetable.
-- ============================================================

CREATE TABLE timetable_slots (
    id                   BIGSERIAL PRIMARY KEY,
    timetable_id         BIGINT NOT NULL,
    course_offering_id   BIGINT NOT NULL,
    room_id              BIGINT NOT NULL,
    day_of_week          SMALLINT NOT NULL,
    start_time           TIME NOT NULL,
    end_time             TIME NOT NULL,

    CONSTRAINT fk_timetable_slots_timetable
        FOREIGN KEY (timetable_id)
        REFERENCES timetables (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_timetable_slots_course_offering
        FOREIGN KEY (course_offering_id)
        REFERENCES course_offerings (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_timetable_slots_room
        FOREIGN KEY (room_id)
        REFERENCES rooms (id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_timetable_slots_valid_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT ck_timetable_slots_valid_time_range
        CHECK (start_time < end_time)
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_faculty_department
    ON faculty (department_id);

CREATE INDEX idx_batches_department
    ON batches (department_id);

CREATE INDEX idx_courses_department
    ON courses (department_id);

CREATE INDEX idx_course_offerings_course
    ON course_offerings (course_id);

CREATE INDEX idx_course_offerings_faculty
    ON course_offerings (faculty_id);

CREATE INDEX idx_course_offerings_batch
    ON course_offerings (batch_id);

CREATE INDEX idx_course_offerings_semester
    ON course_offerings (semester_id);

CREATE INDEX idx_faculty_availability_faculty
    ON faculty_availability (faculty_id);

CREATE INDEX idx_faculty_availability_semester
    ON faculty_availability (semester_id);

CREATE INDEX idx_room_availability_room
    ON room_availability (room_id);

CREATE INDEX idx_room_availability_semester
    ON room_availability (semester_id);

CREATE INDEX idx_faculty_preferences_faculty
    ON faculty_preferences (faculty_id);

CREATE INDEX idx_faculty_preferences_semester
    ON faculty_preferences (semester_id);

CREATE INDEX idx_timetables_semester
    ON timetables (semester_id);

CREATE INDEX idx_timetable_slots_timetable
    ON timetable_slots (timetable_id);

CREATE INDEX idx_timetable_slots_course_offering
    ON timetable_slots (course_offering_id);

CREATE INDEX idx_timetable_slots_room
    ON timetable_slots (room_id);

CREATE INDEX idx_timetable_slots_day_time
    ON timetable_slots (day_of_week, start_time, end_time);