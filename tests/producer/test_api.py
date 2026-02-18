import sys
import os

# Add /app to python path
sys.path.insert(0, "/app")

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_track_event():
    payload = {
    "user_id": "1",
    "event_type": "login",
    "timestamp": "2026-02-17 15:10:00",
    "metadata": {"ip": "127.0.0.1"}
}


    response = client.post("/api/v1/events/track", json=payload)
    assert response.status_code == 202
