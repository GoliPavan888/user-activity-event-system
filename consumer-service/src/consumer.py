import json
import pika
import threading
import signal
import time
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from .database import insert_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # start consumer thread
    thread = threading.Thread(target=start_consumer, daemon=True)
    thread.start()
    yield
    # on shutdown, call handler
    shutdown_handler()

app = FastAPI(title="Consumer Service", lifespan=lifespan)

connection = None
channel = None


@app.get("/health")
def health_check():
    # verify RabbitMQ and MySQL connectivity
    errors = []
    try:
        import pika
        conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, socket_timeout=2)
        )
        conn.close()
    except Exception as e:
        errors.append(f"rabbitmq:{e}")
    try:
        import mysql.connector
        db = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=2,
        )
        db.close()
    except Exception as e:
        errors.append(f"mysql:{e}")
    if errors:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "errors": errors})
    return {"status": "healthy"}


def process_message(ch, method, properties, body):
    try:
        event = json.loads(body)
    except json.JSONDecodeError as je:
        logger.error(f"Malformed message, dropping: {je}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            insert_event(event)

            logger.info(f"Stored event: {event}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        except Exception as e:
            logger.error(
                f"DB insert failed (attempt {attempt + 1}): {e}"
            )
            time.sleep(retry_delay)

    logger.error(f"Failed after retries. Sending to DLQ: {event}")
    # publish to dead-letter queue instead of silently dropping
    try:
        dlq = QUEUE_NAME + "_dlq"
        ch.basic_publish(
            exchange="",
            routing_key=dlq,
            body=json.dumps(event),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        logger.info(f"Message sent to DLQ {dlq}")
    except Exception as de:
        logger.error(f"Failed to publish to DLQ: {de}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    global connection, channel

    while True:
        try:
            logger.info("Connecting to RabbitMQ...")

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                )
            )

            channel = connection.channel()

            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            # dead-letter queue for messages that fail after retries
            channel.queue_declare(queue=QUEUE_NAME + "_dlq", durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=process_message,
            )

            logger.info("Consumer started. Waiting for messages...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            logger.warning(
                "RabbitMQ not ready. Retrying in 5 seconds..."
            )
            time.sleep(5)




def shutdown_handler(*args):
    global connection, channel

    logger.info("Shutting down consumer...")

    try:
        if channel and channel.is_open:
            channel.stop_consuming()

        if connection and connection.is_open:
            connection.close()

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

