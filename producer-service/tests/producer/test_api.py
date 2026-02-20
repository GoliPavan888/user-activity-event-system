import sys
import os
import uuid
import json

# Add /app to python path
sys.path.insert(0, "/app")

# use a dedicated queue to avoid racing with the consumer container
test_queue = f"test_queue_{uuid.uuid4().hex}"
os.environ["QUEUE_NAME"] = test_queue

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"


def test_track_event():
    payload = {
        "user_id": 1,
        "event_type": "login",
        "timestamp": "2026-02-17T15:10:00Z",
        "metadata": {"ip": "127.0.0.1"},
    }

    response = client.post("/api/v1/events/track", json=payload)
    assert response.status_code == 202

    # verify message landed in RabbitMQ
    import pika
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "rabbitmq"), port=int(os.getenv("RABBITMQ_PORT", 5672)))
    )
    ch = conn.channel()
    ch.queue_declare(queue=test_queue, durable=True)
    method_frame, header, body = ch.basic_get(queue=test_queue, auto_ack=True)
    conn.close()
    assert method_frame is not None
    received = json.loads(body)
    # convert both timestamps to a common ISO format for comparison
    from datetime import datetime
    def norm(ts):
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).isoformat()
    assert received["user_id"] == payload["user_id"]
    assert received["event_type"] == payload["event_type"]
    assert norm(received["timestamp"]) == norm(payload["timestamp"])
    assert received["metadata"] == payload["metadata"]


def test_invalid_payload():
    # missing user_id and wrong types
    bad_payload = {"event_type": 123, "timestamp": "not-a-date"}
    response = client.post("/api/v1/events/track", json=bad_payload)

    assert response.status_code == 400
    assert "Invalid request payload" in response.json().get("error", "")
