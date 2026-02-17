import json
import pika
import logging

from src.config import RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def publish_event(event: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT
        )
    )

    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2,
        ),
    )

    logger.info("Event published to queue")

    connection.close()
