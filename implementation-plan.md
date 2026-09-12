# Constraint-Based University Timetable Scheduler — Implementation Plan

> **How to use this file:** Upload this document directly to GitHub Copilot (or paste it into a Copilot Chat / Copilot Workspace session) at the start of a task instead of re-explaining the project. Each phase below is scoped so you can say "implement Phase 3" and Copilot has everything it needs: the schema, the stack, the folder layout, and the exact deliverable.

---

## 1. Project Summary

**Name:** Constraint-Based University Timetable Scheduler
**Problem:** Automatically generate a conflict-free university timetable (course + faculty + room + time) instead of doing it by hand, using constraint optimization (not ML).
**Hard constraints (must never break):** a faculty member can't teach two classes at once; a room can't hold two classes at once; a room must be big enough and the right type (e.g. LAB); a batch can't have two overlapping classes.
**Soft constraints (nice to have):** minimize gaps in a batch's day, minimize faculty idle time, respect faculty time preferences, reduce wasted room capacity.
**Standout feature:** incremental rescheduling — when one constraint changes (e.g. a faculty member becomes unavailable), only the affected slots are re-optimized, not the whole timetable.

---

## 2. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React / Next.js + TypeScript | Timetable dashboard, drag-and-drop editing |
| Backend | Python + FastAPI | REST API, validation, job orchestration |
| Database | PostgreSQL | Schema already finalized (see `schema.sql`) |
| ORM / migrations | SQLAlchemy + Alembic | Keep migrations versioned from day one |
| Solver | Google OR-Tools (CP-SAT) | Constraint programming, not ML |
| Async jobs | Redis + RQ/Celery | Scheduling runs can take time; don't block API requests |
| Deployment | Docker + docker-compose | One command to bring up db + api + frontend + redis |

---

## 3. Data Model Recap

Use the schema in `schema.sql` (already finalized) as the single source of truth. Summary for quick reference:

| Table | One-line purpose |
|---|---|
| `departments` | Owns faculty, batches, and courses |
| `semesters` | A term with a date range |
| `faculty` | People who teach |
| `batches` | Groups of students sharing one timetable (e.g. CSE-A) |
| `courses` | Subjects, with optional room-type/capacity requirements |
| `rooms` | Physical spaces with type and capacity |
| `course_offerings` | "This course, by this faculty, to this batch, this semester" |
| `faculty_availability` | Weekly windows a faculty member can be scheduled |
| `room_availability` | Weekly windows a room can be used |
| `faculty_preferences` | Soft-constraint input: preferred teaching windows |
| `timetables` | One solver run/version for a semester |
| `timetable_slots` | One placed class: offering + room + day + time, inside a timetable |

Do not re-derive this schema from memory in any Copilot session — always attach `schema.sql` alongside this file.

---

## 4. Implementation Phases

Work through these in order. Each phase has a clear, demoable output — don't start a phase until the previous one's "Definition of Done" is met.

### Phase 0 — Project Scaffolding
**Goal:** Empty-but-running skeleton.
- [ ] Create monorepo structure (see Section 5).
- [ ] `docker-compose.yml` with services: `postgres`, `redis`, `api`, `web`.
- [ ] FastAPI app boots with a `/health` endpoint.
- [ ] Next.js app boots with a placeholder page.
- **Definition of Done:** `docker-compose up` brings up all four services and `/health` returns 200.

### Phase 1 — Database Layer
**Goal:** Schema is live and seedable.
- [ ] Add `schema.sql` as the initial Alembic migration (or translate it into SQLAlchemy models and let Alembic autogenerate — translate manually to avoid drift).
- [ ] Write SQLAlchemy models for all 12 tables, matching column names and constraints exactly.
- [ ] Write a `seed.py` script that inserts a small fake dataset: 2 departments, 5 faculty, 4 batches, 10 courses, 6 rooms, availability windows for each faculty/room, and ~15 course_offerings.
- **Definition of Done:** `alembic upgrade head` + `python seed.py` leaves a fully populated dev database.

### Phase 2 — CRUD API (no solver yet)
**Goal:** Admin can manage raw data through the API.
- [ ] REST endpoints for each entity table: `departments`, `semesters`, `faculty`, `batches`, `courses`, `rooms`, `course_offerings`, `faculty_availability`, `room_availability`, `faculty_preferences`.
  - Standard shape per entity: `GET /api/{entity}`, `GET /api/{entity}/{id}`, `POST /api/{entity}`, `PATCH /api/{entity}/{id}`, `DELETE /api/{entity}/{id}`.
- [ ] Input validation with Pydantic schemas mirroring the DB `CHECK` constraints (e.g. `start_time < end_time`, `day_of_week` 1–7).
- **Definition of Done:** Can create a full semester's worth of data via API calls alone (e.g. via a Postman/HTTPie script), no direct SQL needed.

### Phase 3 — Basic Solver (hard constraints only)
**Goal:** Generate a conflict-free timetable for one semester.
- [ ] New module `solver/` (pure Python, no FastAPI dependency, so it's independently testable).
- [ ] Load all `course_offerings` for a semester + their courses, faculty, batches, plus `rooms`, `faculty_availability`, `room_availability`.
- [ ] Model with OR-Tools CP-SAT:
  - Decision variable per `course_offering` session: which room, which day, which start time (discretize the day into time buckets, e.g. every 30 min).
  - Hard constraint: no faculty double-booked (`faculty_availability` respected + no overlapping sessions for same faculty).
  - Hard constraint: no room double-booked, and room capacity/type matches course requirement.
  - Hard constraint: no batch double-booked.
  - Hard constraint: total sessions per week per course_offering matches `courses.sessions_per_week`, each of length `courses.duration_minutes`.
- [ ] On success, write results into a new `timetables` row (`status='COMPLETED'`) and its `timetable_slots`.
- [ ] Endpoint: `POST /api/semesters/{id}/generate-timetable` → runs solver synchronously for now, returns the new `timetable_id`.
- **Definition of Done:** Given the seed data, calling the endpoint produces a `timetables` row with zero hard-constraint violations, verifiable by a script that scans `timetable_slots` for overlaps.

### Phase 4 — Soft Constraints & Scoring
**Goal:** Timetables aren't just valid, they're good.
- [ ] Add an objective function to the CP-SAT model:
  - Reward slots that match `faculty_preferences.preference_score`.
  - Penalize gaps in a batch's day (sum of idle time between a batch's sessions).
  - Penalize wasted room capacity (`room.capacity - batch.student_count`).
- [ ] Store the resulting objective value in `timetables.score`.
- [ ] Make the scoring weights configurable (e.g. a config dict/env vars), not hardcoded magic numbers.
- **Definition of Done:** Two timetables generated from the same data with different weightings visibly differ in preference satisfaction (demoable, log the deltas).

### Phase 5 — Async Job Handling
**Goal:** Solver runs don't block the API for large datasets.
- [ ] Move solver execution into a Redis-backed job queue (RQ or Celery).
- [ ] `POST /api/semesters/{id}/generate-timetable` enqueues a job and immediately returns a `timetable_id` with `status='GENERATING'`.
- [ ] `GET /api/timetables/{id}` reports current `status` and `score` once complete.
- **Definition of Done:** A 250-course-offering generation run doesn't time out the HTTP request; status polling shows `GENERATING` → `COMPLETED`.

### Phase 6 — Dashboard (read-only first)
**Goal:** Visualize the timetable.
- [ ] Next.js page: pick a semester + timetable version, see a weekly grid per batch (or per faculty/room, toggleable).
- [ ] Show `timetables.score` and a breakdown of soft-constraint penalties.
- **Definition of Done:** A non-technical person can open the dashboard and read the generated timetable without touching the API directly.

### Phase 7 — Manual Editing with Validation
**Goal:** Admin can drag-and-drop a `timetable_slot` to a new room/day/time, and the backend either accepts or explains why not.
- [ ] `PATCH /api/timetable-slots/{id}` endpoint that re-validates all hard constraints for just the moved slot against the rest of that `timetable_id`.
- [ ] On failure, return a specific reason (e.g. `"faculty_unavailable"`, `"room_conflict_with_slot_42"`, `"batch_conflict_with_slot_17"`), not a generic error.
- [ ] Frontend drag-and-drop UI wired to this endpoint, surfacing the specific violated constraint in the UI.
- **Definition of Done:** Attempting an invalid move shows the admin the exact rule that was broken.

### Phase 8 — Incremental Rescheduling
**Goal:** The headline feature. One change → minimal re-optimization.
- [ ] Endpoint: `POST /api/faculty/{id}/unavailability` (or similar) to register a new constraint (e.g. a one-off unavailability window).
- [ ] Solver mode: given an existing `timetable_id`, identify only the `timetable_slots` that now violate a constraint, fix all other slots as constants in the CP-SAT model, and re-solve only for the affected ones (+ maybe their room/day neighbors to find a slot).
- [ ] Create a new `timetables` version (`version_number + 1`) with the diff.
- [ ] Endpoint: `GET /api/timetables/{id}/diff/{other_id}` returns a list of changed slots (before → after) for the dashboard to display.
- **Definition of Done:** Simulate a faculty unavailability on seed data; confirm only the affected `course_offerings` move, and the diff endpoint correctly lists exactly those changes.

### Phase 9 — Benchmarking
**Goal:** Numbers for the resume, backed by your own system.
- [ ] Dataset generator script: produce synthetic datasets at 50 / 100 / 250 / 500 course_offerings.
- [ ] Benchmark script: record solve time, hard-constraint violation count (should be 0), soft-constraint score, room utilization %.
- [ ] Save results to a simple CSV/markdown table in `/benchmarks`.
- **Definition of Done:** A benchmarks report exists with real numbers from your own runs — no invented statistics.

### Phase 10 — Deployment
**Goal:** Publicly runnable demo.
- [ ] Finalize `docker-compose.yml` (or split into prod-specific compose file).
- [ ] Environment-based config (`.env` for DB URL, Redis URL, secret keys).
- [ ] Deploy to a small cloud VM or platform (e.g. Render, Railway, Fly.io) — pick one and document the steps taken.
- **Definition of Done:** A public URL where the dashboard and API are reachable.

---

## 5. Suggested Repository Structure

```
university-scheduler/
├── docker-compose.yml
├── schema.sql                      # source of truth for DB structure
├── implementation-plan.md          # this file
├── api/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/                 # SQLAlchemy models, one file per table group
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── routers/                # one router per entity + one for timetables
│   │   ├── solver/
│   │   │   ├── model_builder.py    # builds CP-SAT variables & constraints
│   │   │   ├── hard_constraints.py
│   │   │   ├── soft_constraints.py
│   │   │   ├── incremental.py      # partial re-solve logic
│   │   │   └── runner.py           # entrypoint used by the job queue
│   │   ├── jobs/                   # Redis/RQ or Celery task definitions
│   │   └── db/
│   │       ├── session.py
│   │       └── seed.py
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── web/
│   ├── app/                        # Next.js app router
│   ├── components/
│   │   ├── TimetableGrid.tsx
│   │   ├── SlotEditor.tsx
│   │   └── DiffView.tsx
│   └── package.json
└── benchmarks/
    ├── generate_dataset.py
    ├── run_benchmark.py
    └── results.md
```

---

## 6. API Surface (target state, after Phase 8)

| Method | Path | Purpose |
|---|---|---|
| CRUD | `/api/{departments,semesters,faculty,batches,courses,rooms,course-offerings,faculty-availability,room-availability,faculty-preferences}` | Manage raw data |
| POST | `/api/semesters/{id}/generate-timetable` | Enqueue a full solve |
| GET | `/api/timetables/{id}` | Status + score |
| GET | `/api/timetables/{id}/slots` | All slots in this version |
| PATCH | `/api/timetable-slots/{id}` | Manual move, validated |
| POST | `/api/faculty/{id}/unavailability` | Trigger incremental reschedule |
| GET | `/api/timetables/{id}/diff/{other_id}` | Compare two versions |

---

## 7. Core Algorithm Notes (for whoever implements Phase 3–4 & 8)

- **Time representation:** discretize each day into fixed-size buckets (e.g. 30-minute slots from 8:00–18:00). A session of `duration_minutes` occupies a contiguous run of buckets starting at a decision variable.
- **Decision variables:** for each `course_offering` session instance (there are `sessions_per_week` of them), a variable for `room_id`, `day_of_week`, and `start_bucket`.
- **Hard constraints as CP-SAT `AddNoOverlap` / interval variables:**
  - One no-overlap constraint per faculty (across all their sessions).
  - One no-overlap constraint per room.
  - One no-overlap constraint per batch.
- **Objective:** weighted sum — maximize preference match, minimize batch gap time, minimize room-capacity waste. Keep weights in one config object so they're tunable without touching model logic.
- **Incremental solve:** fix all `IntVar`s for unaffected sessions to their current values (`model.Add(var == current_value)`), leave the rest free, re-solve. This is dramatically faster than a full re-solve and is the basis of Phase 8.

---

## 8. What NOT to Build (scope guardrails)

To keep this a finishable, explainable project:
- No equipment inventory tracking — folded into `courses.required_room_type` / `min_capacity`.
- No course prerequisite/degree-planning logic — out of scope for a timetabling tool.
- No multi-batch-per-offering support — one batch per `course_offering` is enough to demonstrate the algorithm.
- No machine learning — this is a constraint-optimization project by design; don't let scope creep turn it into an ML project.

---

## 9. Milestone Checklist (copy into GitHub Projects / Issues)

- [ ] Phase 0 — Scaffolding
- [ ] Phase 1 — Database layer
- [ ] Phase 2 — CRUD API
- [ ] Phase 3 — Basic solver (hard constraints)
- [ ] Phase 4 — Soft constraints & scoring
- [ ] Phase 5 — Async job handling
- [ ] Phase 6 — Dashboard (read-only)
- [ ] Phase 7 — Manual editing with validation
- [ ] Phase 8 — Incremental rescheduling
- [ ] Phase 9 — Benchmarking
- [ ] Phase 10 — Deployment
