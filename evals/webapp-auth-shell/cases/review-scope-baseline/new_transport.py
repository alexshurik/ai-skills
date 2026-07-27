"""This file is copied into the fixture after the base commit."""

import json


def create_request(raw_body: str, store) -> dict:
    payload = json.loads(raw_body)
    store.setex(f"request:{payload['id']}", 60, json.dumps(payload))
    return payload
