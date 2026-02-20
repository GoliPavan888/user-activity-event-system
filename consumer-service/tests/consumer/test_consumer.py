import os
import sys
import time
import json

# ensure /app is on path when tests are run inside container
sys.path.insert(0, "/app")

from fastapi.testclient import TestClient
# import consumer app for health check
from src import consumer

client = TestClient(consumer.app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"

import pika
import mysql.connector

QUEUE = os.getenv("QUEUE_NAME", "user_activity_events")
RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBIT_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root_password")
DB_NAME = os.getenv("DB_NAME", "user_activity_db")


def publish_to_queue(message: dict):
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.basic_publish(exchange="", routing_key=QUEUE, body=json.dumps(message))
    conn.close()


def count_rows():
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM user_activities")
    cnt = cur.fetchone()[0]
    cur.close()
    conn.close()
    return cnt


def test_consumer_integration():
    # ensure queue is empty
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_purge(queue=QUEUE)
    conn.close()

    initial = count_rows()

    event = {
        "user_id": 42,
        "event_type": "page_view",
        "timestamp": "2026-02-20T12:00:00Z",
        "metadata": {"page": "/home"},
    }

    publish_to_queue(event)

    # wait for consumer to insert
    timeout = 10
    while timeout > 0:
        if count_rows() == initial + 1:
            break
        time.sleep(1)
        timeout -= 1

    assert count_rows() == initial + 1
    # verify the inserted row matches the event
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM user_activities ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    assert row["user_id"] == event["user_id"]
    assert row["event_type"] == event["event_type"]


def test_consumer_malformed_message():
    # send something that cannot be parsed to event
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE, durable=True)

    # publish invalid JSON
    ch.basic_publish(exchange="", routing_key=QUEUE, body="not-json")
    conn.close()

    # give consumer a moment
    time.sleep(2)

    # verify no crash and next valid message still processed
    initial = count_rows()
    event = {
        "user_id": 99,
        "event_type": "login",
        "timestamp": "2026-02-20T13:00:00Z",
        "metadata": {},
    }
    publish_to_queue(event)

    timeout = 10
    while timeout > 0:
        if count_rows() >= initial + 1:
            break
        time.sleep(1)
        timeout -= 1

    assert count_rows() >= initial + 1


def test_consumer_retry_and_dlq():
    # publish an event that will fail DB formatting (bad timestamp)
    bad = {
        "user_id": 55,
        "event_type": "signup",
        "timestamp": "not-a-timestamp",
        "metadata": {},
    }
    # purge DLQ first
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE + "_dlq", durable=True)
    ch.queue_purge(queue=QUEUE + "_dlq")
    conn.close()

    publish_to_queue(bad)

    # allow retries/processing by polling DLQ until a message appears
    dlq_count = 0
    timeout = 30
    while timeout > 0 and dlq_count < 1:
        conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
        )
        ch = conn.channel()
        q = ch.queue_declare(queue=QUEUE + "_dlq", durable=True, passive=True)
        dlq_count = q.method.message_count
        conn.close()
        if dlq_count < 1:
            time.sleep(1)
            timeout -= 1

    assert dlq_count >= 1
