from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

from fastapi.exceptions import RequestValidationError
from fastapi import Request

from src.producer import publish_event
from src.schemas import UserActivityEvent
from src.config import RABBITMQ_HOST, RABBITMQ_PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # startup actions could go here
    yield
    logger.info("Producer FastAPI shutdown event")

app = FastAPI(title="Producer Service", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    # convert FastAPI's 422 into 400 for missing/invalid data
    logger.warning(f"Validation error for {request.url}: {exc}")
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request payload", "details": exc.errors()},
    )


@app.get("/health")
def health_check():
    # verify RabbitMQ connectivity
    try:
        import pika
        conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, socket_timeout=2)
        )
        conn.close()
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "reason": str(e)})
    return {"status": "healthy"}


@app.post("/api/v1/events/track")
def track_event(event: UserActivityEvent):
    try:
        publish_event(event.model_dump())
        logger.info(f"Event queued: {event.model_dump()}")

        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message": "Event queued successfully",
            },
        )

    except Exception as e:
        logger.error(f"Failed to queue event: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to queue event"},
        )


# graceful shutdown handler
import signal

def shutdown_handler(*_):
    logger.info("Producer shutting down...")

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

