from fastapi import FastAPI

app = FastAPI(title="University Timetable Scheduler")


@app.get("/health")
def health_check():
    return {"status": "ok"}
