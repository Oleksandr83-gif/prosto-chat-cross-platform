import json
from typing import Any

import pika

from app.config import settings


class AMQPPublisher:
    def __init__(self, url: str | None = None, exchange: str | None = None) -> None:
        self.url = url or settings.rabbitmq_url
        self.exchange = exchange or settings.rabbitmq_exchange

    def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(self.url))
            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange, exchange_type="topic", durable=True)
            channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
            )
            connection.close()
        except Exception as exc:
            print(f"[amqp] publish skipped: {routing_key}: {exc}")

