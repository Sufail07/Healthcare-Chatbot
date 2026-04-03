"""Extracts structured symptoms from natural language using LLM via OpenRouter."""

import json
import re
import logging
import httpx
from openai import AsyncOpenAI

from app.config import get_settings
from app.services.ml_service import get_known_symptoms
from app.services.llm_service import _call_with_retry

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=httpx.Timeout(120.0, connect=15.0),
            default_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Healthcare Chatbot",
            },
        )
    return _client


def _strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> reasoning blocks from model output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


async def parse_symptoms(user_message: str) -> list[str]:
    """Extract symptom keywords from natural language using LLM.

    Returns list of symptom strings matching known model symptoms.
    """
    known = get_known_symptoms()
    known_str = ", ".join(known)

    system_prompt = (
        "You are a medical symptom extraction system. Extract symptoms from the user's "
        "message and map them to the closest matching symptoms from the known list.\n\n"
        "RULES:\n"
        "- Only return symptoms from the known list below\n"
        "- Return a JSON array of symptom strings\n"
        "- If no symptoms found, return an empty array []\n"
        "- Map common language to medical terms (e.g., 'throwing up' -> 'vomiting')\n\n"
        f"KNOWN SYMPTOMS:\n{known_str}"
    )

    try:
        settings = get_settings()
        client = _get_client()
        response = await _call_with_retry(
            client,
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        content = _strip_think_blocks(content)
        # Extract JSON array from response
        if "[" in content:
            json_str = content[content.index("["):content.rindex("]") + 1]
            symptoms = json.loads(json_str)
            # Validate against known symptoms
            return [s for s in symptoms if s in known]
        return []
    except Exception as e:
        logger.error(f"Symptom parsing error: {e}")
        return _fallback_parse(user_message, known)


def _fallback_parse(message: str, known_symptoms: list[str]) -> list[str]:
    """Simple keyword matching fallback when LLM is unavailable."""
    message_lower = message.lower().replace(" ", "_")
    found = []
    for symptom in known_symptoms:
        # Check both underscore and space versions
        if symptom in message_lower or symptom.replace("_", " ") in message.lower():
            found.append(symptom)
    return found
