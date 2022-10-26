import json
from avro.schema import parse
from avro.io import validate
from models import UserRole
from uuid import UUID


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        if isinstance(obj, UserRole):
            # if the obj is uuid, we simply return the value of uuid
            return obj.name
        return json.JSONEncoder.default(self, obj)


def validate_schema(event_type, version, event):
    schema = parse(open(f'../avro_schemas/{event_type}/{version}.avro').read())
    return validate(schema, event, raise_on_error=True)
