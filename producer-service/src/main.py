from fastapi import FastAPI, status
from .schemas import UserActivityEvent

app = FastAPI(title="Producer Service")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/events/track", status_code=status.HTTP_202_ACCEPTED)
def track_event(event: UserActivityEvent):
    # FastAPI automatically serializes datetime
    return {
        "message": "Event accepted",
        "event": event
    }
