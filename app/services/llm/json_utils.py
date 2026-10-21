import json
from typing import Any


def clean_and_parse_json(raw: str) -> dict[str, Any]:
    """Parse JSON returned by an LLM, allowing a surrounding Markdown code fence."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object from the model.")
    return parsed
