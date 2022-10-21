import json
from uuid import UUID
from kafka import KafkaProducer
from models import UserRole

KAFKA_SERVER = "localhost:9092"
kafka_producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    api_version=(0, 11, 15)
)

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        if isinstance(obj, UserRole):
            # if the obj is uuid, we simply return the value of uuid
            return obj.name
        return json.JSONEncoder.default(self, obj)


def kafka_send_message(message: dict, topic: str):
    json_payload = json.dumps(message, cls=UUIDEncoder).encode()
    kafka_producer.send(topic, json_payload)
    kafka_producer.flush()
