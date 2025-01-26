import json

def attempt_json_deserialize(name, value, expect_type=None):
    try:
        value = json.loads(value)
    except (TypeError, json.decoder.JSONDecodeError): pass

    if expect_type is not None and not isinstance(value, expect_type):
        raise ValueError(f"Got {type(value)} but expected {expect_type} on param {name}.")

    return value