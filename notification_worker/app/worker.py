import json
import os
import time

import pika


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "chat.events")
QUEUE = os.getenv("RABBITMQ_QUEUE", "notification_worker")
ROUTING_KEYS = ["message.created", "chat.created", "file.uploaded", "user.online", "user.offline"]


def connect_with_retry() -> pika.BlockingConnection:
    while True:
        try:
            return pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        except Exception as exc:
            print(f"[notification-worker] waiting for RabbitMQ: {exc}")
            time.sleep(3)


def main() -> None:
    connection = connect_with_retry()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)

    for routing_key in ROUTING_KEYS:
        channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=routing_key)

    def handle_message(channel, method, properties, body) -> None:
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {"raw": body.decode("utf-8", errors="replace")}
        print(f"[notification-worker] {method.routing_key}: {payload}")
        channel.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=QUEUE, on_message_callback=handle_message)
    print("[notification-worker] started")
    channel.start_consuming()


if __name__ == "__main__":
    main()

