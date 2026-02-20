import json
import pika
import logging
import time

from src.config import RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def publish_event(event: dict):
    # try to publish with a few retries in case RabbitMQ is temporarily unavailable
    max_attempts = 5
    delay = 1
    for attempt in range(1, max_attempts + 1):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    socket_timeout=5,
                )
            )

            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=json.dumps(event, default=str),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            logger.info("Event published to queue")
            connection.close()
            return
        except Exception as e:
            logger.warning(f"Publish attempt {attempt} failed: {e}")
            time.sleep(delay)
            delay *= 2
    # if we reach here, all attempts failed
    raise RuntimeError("Unable to publish event after multiple attempts")
