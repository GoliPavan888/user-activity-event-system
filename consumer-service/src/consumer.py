import json
import pika
import threading
import signal
import time
import logging

from fastapi import FastAPI

from .config import RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME
from .database import insert_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Consumer Service")

connection = None
channel = None


@app.get("/health")
def health_check():
    return {"status": "healthy"}


def process_message(ch, method, properties, body):
    event = json.loads(body)

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

    logger.error(f"Failed after retries. Dropping message: {event}")
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


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=start_consumer, daemon=True)
    thread.start()


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
