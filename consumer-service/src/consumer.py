import json
import pika
import threading

from fastapi import FastAPI

from .config import RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME

app = FastAPI(title="Consumer Service")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


def process_message(ch, method, properties, body):
    try:
        event = json.loads(body)
        print("Received event:", event)

        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print("Processing failed:", e)

        # Acknowledge anyway to avoid infinite retry
        ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=process_message,
    )

    print("Consumer started. Waiting for messages...")
    channel.start_consuming()


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=start_consumer, daemon=True)
    thread.start()
