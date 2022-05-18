import jsonschema
import json

def validate_metadata(metadata):
    """
    Validates a metadata dict object against a predefined JSON Schema
    """
    f = open('validation/validationSchema.json')
    validation_schema = json.load(f)

    v = jsonschema.Draft7Validator(validation_schema)
    errors = sorted(v.iter_errors(metadata), key=lambda e: e.path)

    if not errors:
        return True

    return errors
