-- ============================================================
-- CONSTRAINT-BASED UNIVERSITY SCHEDULER
-- PostgreSQL Database Schema
-- ============================================================

-- ============================================================
-- 1. SEMESTERS
-- ============================================================

CREATE TABLE semesters (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,

    CONSTRAINT valid_semester_dates
        CHECK (start_date < end_date)
);


-- ============================================================
-- 2. PROFESSORS
-- ============================================================

CREATE TABLE professors (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(255) UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- 3. STUDENT GROUPS
-- ============================================================

CREATE TABLE student_groups (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    size        INTEGER NOT NULL,

    CONSTRAINT valid_student_group_size
        CHECK (size > 0)
);


-- ============================================================
-- 4. COURSES
-- ============================================================

CREATE TABLE courses (
    id               BIGSERIAL PRIMARY KEY,
    code             VARCHAR(30) NOT NULL UNIQUE,
    name             VARCHAR(150) NOT NULL,
    description      TEXT,
    duration_minutes INTEGER NOT NULL,

    CONSTRAINT valid_course_duration
        CHECK (duration_minutes > 0)
);


-- ============================================================
-- 5. COURSE SECTIONS
-- ============================================================

CREATE TABLE course_sections (
    id               BIGSERIAL PRIMARY KEY,

    course_id        BIGINT NOT NULL,
    semester_id      BIGINT NOT NULL,
    professor_id     BIGINT NOT NULL,

    section_name     VARCHAR(50) NOT NULL,

    -- Allows a section to have a different duration
    -- from the default course duration if necessary.
    duration_minutes INTEGER,

    CONSTRAINT fk_section_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_section_semester
        FOREIGN KEY (semester_id)
        REFERENCES semesters(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_section_professor
        FOREIGN KEY (professor_id)
        REFERENCES professors(id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_section_duration
        CHECK (
            duration_minutes IS NULL
            OR duration_minutes > 0
        ),

    CONSTRAINT unique_course_section
        UNIQUE (course_id, semester_id, section_name)
);


-- ============================================================
-- 6. SECTION ↔ STUDENT GROUPS
-- ============================================================

CREATE TABLE section_student_groups (
    section_id       BIGINT NOT NULL,
    student_group_id BIGINT NOT NULL,

    PRIMARY KEY (section_id, student_group_id),

    CONSTRAINT fk_ssg_section
        FOREIGN KEY (section_id)
        REFERENCES course_sections(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ssg_student_group
        FOREIGN KEY (student_group_id)
        REFERENCES student_groups(id)
        ON DELETE CASCADE
);


-- ============================================================
-- 7. ROOMS
-- ============================================================

CREATE TABLE rooms (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    capacity    INTEGER NOT NULL,
    room_type   VARCHAR(50) NOT NULL,

    CONSTRAINT valid_room_capacity
        CHECK (capacity > 0),

    CONSTRAINT valid_room_type
        CHECK (
            room_type IN (
                'CLASSROOM',
                'LAB',
                'AUDITORIUM'
            )
        )
);


-- ============================================================
-- 8. EQUIPMENT
-- ============================================================

CREATE TABLE equipment (
    id      BIGSERIAL PRIMARY KEY,
    name    VARCHAR(100) NOT NULL UNIQUE
);


-- ============================================================
-- 9. ROOM ↔ EQUIPMENT
-- ============================================================

CREATE TABLE room_equipment (
    room_id       BIGINT NOT NULL,
    equipment_id  BIGINT NOT NULL,
    quantity      INTEGER NOT NULL DEFAULT 1,

    PRIMARY KEY (room_id, equipment_id),

    CONSTRAINT fk_room_equipment_room
        FOREIGN KEY (room_id)
        REFERENCES rooms(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_room_equipment_equipment
        FOREIGN KEY (equipment_id)
        REFERENCES equipment(id)
        ON DELETE CASCADE,

    CONSTRAINT valid_equipment_quantity
        CHECK (quantity > 0)
);


-- ============================================================
-- 10. PROFESSOR AVAILABILITY
-- ============================================================

CREATE TABLE professor_availability (
    id           BIGSERIAL PRIMARY KEY,
    professor_id BIGINT NOT NULL,

    day_of_week  SMALLINT NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,

    CONSTRAINT fk_professor_availability_professor
        FOREIGN KEY (professor_id)
        REFERENCES professors(id)
        ON DELETE CASCADE,

    CONSTRAINT valid_professor_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT valid_professor_time
        CHECK (start_time < end_time)
);


-- ============================================================
-- 11. ROOM AVAILABILITY
-- ============================================================

CREATE TABLE room_availability (
    id          BIGSERIAL PRIMARY KEY,
    room_id     BIGINT NOT NULL,

    day_of_week SMALLINT NOT NULL,
    start_time  TIME NOT NULL,
    end_time    TIME NOT NULL,

    CONSTRAINT fk_room_availability_room
        FOREIGN KEY (room_id)
        REFERENCES rooms(id)
        ON DELETE CASCADE,

    CONSTRAINT valid_room_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT valid_room_time
        CHECK (start_time < end_time)
);


-- ============================================================
-- 12. PROFESSOR PREFERENCES
-- ============================================================

CREATE TABLE professor_preferences (
    id             BIGSERIAL PRIMARY KEY,
    professor_id   BIGINT NOT NULL,

    day_of_week    SMALLINT NOT NULL,
    start_time     TIME NOT NULL,
    end_time       TIME NOT NULL,

    preference_score INTEGER NOT NULL,

    CONSTRAINT fk_professor_preference_professor
        FOREIGN KEY (professor_id)
        REFERENCES professors(id)
        ON DELETE CASCADE,

    CONSTRAINT valid_preference_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT valid_preference_time
        CHECK (start_time < end_time)
);


-- ============================================================
-- 13. COURSE PREREQUISITES
-- ============================================================

CREATE TABLE course_prerequisites (
    course_id             BIGINT NOT NULL,
    prerequisite_course_id BIGINT NOT NULL,

    PRIMARY KEY (course_id, prerequisite_course_id),

    CONSTRAINT fk_prerequisite_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_prerequisite_required_course
        FOREIGN KEY (prerequisite_course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    CONSTRAINT course_cannot_be_own_prerequisite
        CHECK (course_id <> prerequisite_course_id)
);


-- ============================================================
-- 14. COURSE REQUIREMENTS
-- ============================================================

CREATE TABLE course_requirements (
    id             BIGSERIAL PRIMARY KEY,
    course_id      BIGINT NOT NULL,

    room_type      VARCHAR(50),
    min_capacity   INTEGER,

    CONSTRAINT fk_course_requirement_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    CONSTRAINT valid_requirement_room_type
        CHECK (
            room_type IS NULL
            OR room_type IN (
                'CLASSROOM',
                'LAB',
                'AUDITORIUM'
            )
        ),

    CONSTRAINT valid_requirement_capacity
        CHECK (
            min_capacity IS NULL
            OR min_capacity > 0
        )
);


-- ============================================================
-- 15. COURSE ↔ REQUIRED EQUIPMENT
-- ============================================================

CREATE TABLE course_required_equipment (
    course_id     BIGINT NOT NULL,
    equipment_id  BIGINT NOT NULL,
    quantity      INTEGER NOT NULL DEFAULT 1,

    PRIMARY KEY (course_id, equipment_id),

    CONSTRAINT fk_course_required_equipment_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_course_required_equipment_equipment
        FOREIGN KEY (equipment_id)
        REFERENCES equipment(id)
        ON DELETE CASCADE,

    CONSTRAINT valid_required_equipment_quantity
        CHECK (quantity > 0)
);


-- ============================================================
-- 16. SCHEDULE VERSIONS
-- ============================================================

CREATE TABLE schedule_versions (
    id              BIGSERIAL PRIMARY KEY,

    semester_id     BIGINT NOT NULL,
    version_number  INTEGER NOT NULL,

    objective_score NUMERIC(12, 4),

    status          VARCHAR(30) NOT NULL DEFAULT 'DRAFT',

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_schedule_version_semester
        FOREIGN KEY (semester_id)
        REFERENCES semesters(id)
        ON DELETE CASCADE,

    CONSTRAINT valid_version_number
        CHECK (version_number > 0),

    CONSTRAINT valid_schedule_status
        CHECK (
            status IN (
                'DRAFT',
                'GENERATING',
                'COMPLETED',
                'ACTIVE',
                'ARCHIVED',
                'FAILED'
            )
        ),

    CONSTRAINT unique_semester_version
        UNIQUE (semester_id, version_number)
);


-- ============================================================
-- 17. SCHEDULE ENTRIES
-- ============================================================

CREATE TABLE schedule_entries (
    id                  BIGSERIAL PRIMARY KEY,

    schedule_version_id BIGINT NOT NULL,
    section_id          BIGINT NOT NULL,
    room_id             BIGINT NOT NULL,

    day_of_week         SMALLINT NOT NULL,
    start_time          TIME NOT NULL,
    end_time            TIME NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_schedule_entry_version
        FOREIGN KEY (schedule_version_id)
        REFERENCES schedule_versions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_schedule_entry_section
        FOREIGN KEY (section_id)
        REFERENCES course_sections(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_schedule_entry_room
        FOREIGN KEY (room_id)
        REFERENCES rooms(id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_schedule_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT valid_schedule_time
        CHECK (start_time < end_time)
);


-- ============================================================
-- INDEXES
-- ============================================================

-- Course sections
CREATE INDEX idx_course_sections_course
    ON course_sections(course_id);

CREATE INDEX idx_course_sections_semester
    ON course_sections(semester_id);

CREATE INDEX idx_course_sections_professor
    ON course_sections(professor_id);


-- Student group relationships
CREATE INDEX idx_section_student_groups_student_group
    ON section_student_groups(student_group_id);


-- Professor availability
CREATE INDEX idx_professor_availability_professor
    ON professor_availability(professor_id);


-- Room availability
CREATE INDEX idx_room_availability_room
    ON room_availability(room_id);


-- Professor preferences
CREATE INDEX idx_professor_preferences_professor
    ON professor_preferences(professor_id);


-- Course prerequisites
CREATE INDEX idx_course_prerequisites_prerequisite
    ON course_prerequisites(prerequisite_course_id);


-- Course requirements
CREATE INDEX idx_course_requirements_course
    ON course_requirements(course_id);


-- Course required equipment
CREATE INDEX idx_course_required_equipment_equipment
    ON course_required_equipment(equipment_id);


-- Schedule versions
CREATE INDEX idx_schedule_versions_semester
    ON schedule_versions(semester_id);


-- Schedule entries
CREATE INDEX idx_schedule_entries_version
    ON schedule_entries(schedule_version_id);

CREATE INDEX idx_schedule_entries_section
    ON schedule_entries(section_id);

CREATE INDEX idx_schedule_entries_room
    ON schedule_entries(room_id);

CREATE INDEX idx_schedule_entries_day_time
    ON schedule_entries(day_of_week, start_time, end_time);