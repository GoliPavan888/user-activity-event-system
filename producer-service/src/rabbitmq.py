import json
import pika

from .config import RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME


def publish_event(event: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
    )

    channel = connection.channel()

    # Ensure queue exists
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(event, default=str),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ),
    )

    connection.close()
