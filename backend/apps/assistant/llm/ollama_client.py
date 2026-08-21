import json
import os

import requests


OLLAMA_URL = os.environ.get(
    "OLLAMA_BASE_URL"
)

MODEL_NAME = os.environ.get(
    "OLLAMA_MODEL"
)


def generate_response(
    prompt,
    temperature=0,
    format_json=False,
):

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    if format_json:

        payload["format"] = "json"

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "response",
        "",
    )


def generate_json(
    prompt,
):

    response = generate_response(
        prompt=prompt,
        temperature=0,
        format_json=True,
    )

    try:

        return json.loads(
            response
        )

    except json.JSONDecodeError:

        return {
            "tools": []
        }