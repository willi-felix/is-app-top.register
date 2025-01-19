import os
import json
import jsonschema
from jsonschema import validate

schema = {
    "type": "object",
    "properties": {
        "subdomain": {"type": "string"},
        "domain": {"type": "string"},
        "email": {"type": "string"},
        "github_username": {"type": "string"},
        "description": {"type": "string"},
        "records": {
            "type": "object",
            "properties": {
                "A": {"type": "array", "items": {"type": "string"}},
                "AAAA": {"type": "array", "items": {"type": "string"}},
                "CNAME": {"type": "array", "items": {"type": "string"}},
                "NS": {"type": "array", "items": {"type": "string"}},
                "MX": {"type": "array", "items": {"type": "string"}},
                "TXT": {"type": "array", "items": {"type": "string"}}
            },
            "additionalProperties": False
        },
        "proxied": {"type": "boolean"}
    },
    "required": ["subdomain", "domain", "email", "github_username", "records", "proxied"],
    "additionalProperties": False
}

def validate_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    try:
        validate(instance=data, schema=schema)
        print(f"{file_path} is valid.")
    except jsonschema.exceptions.ValidationError as err:
        print(f"{file_path} is invalid: {err.message}")
        exit(1)

if __name__ == "__main__":
    for filename in os.listdir('domains'):
        if filename.endswith('.json'):
            validate_json(os.path.join('domains', filename))
