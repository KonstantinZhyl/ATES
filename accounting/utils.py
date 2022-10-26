from avro.schema import parse
from avro.io import validate


def validate_schema(event_type, version, event):
    schema = parse(open(f'../avro_schemas/{event_type}/{version}.avro').read())
    return validate(schema, event, raise_on_error=True)
