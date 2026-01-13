from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from apps.api.services.audit_log import append_audit_log
from apps.api.services.intent_validator import INTENT_JSON_SCHEMA


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _extract_json_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    outputs = getattr(response, "output", None) or []
    for output in outputs:
        content = None
        if isinstance(output, dict):
            content = output.get("content", [])
        else:
            content = getattr(output, "content", [])
        for item in content or []:
            if isinstance(item, dict):
                text = item.get("text")
            else:
                text = getattr(item, "text", None)
            if text:
                return text
    raise ValueError("No JSON content returned from LLM response.")


def parse_intent(raw_text: str, language: str | None, intent_id: str) -> dict[str, Any]:
    prompt = (
        "You are an intent parser for a SalesOps system.\n"
        "Return ONLY JSON that matches the given schema. No extra keys.\n"
        f"raw_text: {raw_text}\n"
        f"language: {language or ''}\n"
        f"intent_id: {intent_id}\n"
    )

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        input=prompt,
        store=False,
        text={
            "format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "SalesOpsIntent",
                    "strict": True,
                    "schema": INTENT_JSON_SCHEMA,
                },
            }
        },
    )

    text = _extract_json_text(response)
    parsed = json.loads(text)
    append_audit_log(
        "llm_intent_parser",
        {"raw_text": raw_text, "language": language, "intent_id": intent_id},
        parsed,
    )
    return parsed
