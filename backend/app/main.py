from fastapi import FastAPI
from app.routers.batches import router as batches_router
from app.routers.course_offerings import router as course_offerings_router
from app.routers.courses import router as courses_router
from app.routers.departments import router as departments_router
from app.routers.faculty import router as faculty_router
from app.routers.faculty_availability import router as faculty_availability_router
from app.routers.faculty_preferences import router as faculty_preferences_router
from app.routers.room_availability import router as room_availability_router
from app.routers.rooms import router as rooms_router
from app.routers.semesters import router as semesters_router

app = FastAPI(title="University Timetable Scheduler")


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(departments_router)
app.include_router(semesters_router)
app.include_router(faculty_router)
app.include_router(batches_router)
app.include_router(courses_router)
app.include_router(rooms_router)
app.include_router(course_offerings_router)
app.include_router(faculty_availability_router)
app.include_router(room_availability_router)
app.include_router(faculty_preferences_router)
