from app.amqp.rabbitmq import AMQPPublisher
from app.database import SessionLocal
from app.websocket.connection_manager import ConnectionManager
from app.workers.thread_manager import ThreadManager


amqp_publisher = AMQPPublisher()
connection_manager = ConnectionManager()
thread_manager = ThreadManager(SessionLocal, amqp_publisher)

