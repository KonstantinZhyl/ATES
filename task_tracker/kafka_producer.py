import json
from kafka import KafkaProducer
from utils import UUIDEncoder


KAFKA_SERVER = "localhost:9092"
kafka_producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    api_version=(0, 11, 15)
)


def kafka_send_message(message: dict, topic: str):
    json_payload = json.dumps(message, cls=UUIDEncoder).encode()
    kafka_producer.send(topic, json_payload)
    kafka_producer.flush()
