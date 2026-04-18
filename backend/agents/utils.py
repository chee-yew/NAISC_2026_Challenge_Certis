"""Shared helpers for all agents."""
import json
import logging
import re

logger = logging.getLogger(__name__)


def parse_llm_json(text: str) -> dict:
    """
    Parse a JSON blob from LLM output.

    """
    original = text

    # Clean fence patterns
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)
    text = text.strip()

    # Try parsing as json
    try:
        raw: dict = json.loads(text)
        return {_to_snake(k): v for k, v in raw.items()}
    except json.JSONDecodeError:
        pass

    # Else try to extract {...}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidate = match.group()
        try:
            raw = json.loads(candidate)
            return {_to_snake(k): v for k, v in raw.items()}
        except json.JSONDecodeError:
            pass

    # Log for debugging
    logger.error("parse_llm_json failed. Raw LLM output was:\n%s", original)
    raise ValueError(f"Could not parse JSON from LLM response: {original[:200]!r}")


def _to_snake(key: str) -> str:
    """Convert camelCase, PascalCase, or space/hyphen-separated keys to snake_case."""
    # Replace spaces and hyphens with underscores
    key = re.sub(r"[\s\-]+", "_", key)
    # Insert underscore before uppercase letters followed by a lowercase letter or digit
    key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return key.lower()
