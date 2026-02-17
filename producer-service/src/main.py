from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

from src.producer import publish_event
from src.models import Event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Producer Service")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/events/track")
def track_event(event: Event):
    try:
        publish_event(event.dict())

        logger.info(f"Event queued: {event.dict()}")

        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message": "Event queued successfully"
            },
        )

    except Exception as e:
        logger.error(f"Failed to queue event: {e}")

        return JSONResponse(
            status_code=500,
            content={"error": "Failed to queue event"},
        )
